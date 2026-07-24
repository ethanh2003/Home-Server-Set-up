# Rclone Backup Single-Instance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent overlapping rclone backups, bound their diagnostic output, and safely remove the stale jobs and 185 GB incident log.

**Architecture:** Keep the existing cron schedule and enforce exclusivity inside `rclone_backup.sh` with a non-blocking `flock`. Wrap each rclone operation in a bounded-output runner that retains only the final diagnostic lines and propagates the real rclone exit status.

**Tech Stack:** Bash, util-linux `flock`, GNU `awk`, rclone 1.73.0, cron.

## Global Constraints

- Keep the existing 03:00/15:00 schedule,
  `0 3,15 * * * /home/ethan/docker/rclone_backup.sh`, unchanged.
- Default lock path: `/run/user/<uid>/rclone_backup.lock`.
- Persistent log target: final 10 MiB.
- Per-rclone diagnostic target: final 2,000 lines.
- Never contact Google Drive from automated tests.
- Do not print or copy rclone credentials.
- Do not start a replacement full backup during remediation.

---

### Task 1: Protect the backup with a non-blocking lock

**Files:**
- Create: `tests/test-rclone-backup.sh`
- Modify: `rclone_backup.sh`

**Interfaces:**
- Consumes: `RCLONE_BACKUP_LOCK_FILE` and `RCLONE_BACKUP_LOG_FILE` optional environment variables.
- Produces: exit status `0` with no rclone calls when the lock is already held.

- [ ] **Step 1: Write the failing lock-contention test**

Create a shell integration test that copies the deployed script to a temporary
directory, places this controlled fake ahead of rclone in `PATH`, and invokes
the copied script while holding its isolated lock:

```bash
#!/bin/bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TEST_ROOT=$(mktemp -d)
trap 'rm -rf "$TEST_ROOT"' EXIT
mkdir -p "$TEST_ROOT/bin"

cp "$REPO_ROOT/rclone_backup.sh" "$TEST_ROOT/rclone_backup.sh"
sed -i "s#LOG_FILE=\"/home/ethan/docker/rclone_backup.log\"#LOG_FILE=\"${RCLONE_BACKUP_LOG_FILE:-/home/ethan/docker/rclone_backup.log}\"#" "$TEST_ROOT/rclone_backup.sh"

cat > "$TEST_ROOT/bin/rclone" <<'FAKE'
#!/bin/bash
printf '%s\n' "$*" >> "$RCLONE_CALL_LOG"
FAKE
chmod +x "$TEST_ROOT/bin/rclone"

export PATH="$TEST_ROOT/bin:$PATH"
export RCLONE_CALL_LOG="$TEST_ROOT/rclone.calls"
export RCLONE_BACKUP_LOCK_FILE="$TEST_ROOT/rclone.lock"
export RCLONE_BACKUP_LOG_FILE="$TEST_ROOT/rclone.log"

exec 8>"$RCLONE_BACKUP_LOCK_FILE"
flock -n 8
"$TEST_ROOT/rclone_backup.sh"

test ! -e "$RCLONE_CALL_LOG"
grep -q "already running" "$RCLONE_BACKUP_LOG_FILE"
```

- [ ] **Step 2: Run the test and verify RED**

Run: `bash tests/test-rclone-backup.sh`

Expected: FAIL because the fake rclone call file exists; the current script
does not honor a lock.

- [ ] **Step 3: Add the minimal lock**

At the top of `rclone_backup.sh`, make the log and lock paths overridable,
create their parent directories, open the lock on file descriptor 9, and use
`flock -n 9`. On contention, append a timestamped `already running` message and
exit `0`.

- [ ] **Step 4: Run the test and verify GREEN**

Run: `bash tests/test-rclone-backup.sh`

Expected: PASS with no fake rclone calls.

### Task 2: Bound rclone output and propagate failures

**Files:**
- Modify: `tests/test-rclone-backup.sh`
- Modify: `rclone_backup.sh`

**Interfaces:**
- Consumes: `RCLONE_BACKUP_MAX_LOG_BYTES` and
  `RCLONE_BACKUP_MAX_STAGE_LINES` optional positive integer overrides.
- Produces: at most the final configured number of lines per rclone stage,
  plus the stage exit status; stops the routine on a failed stage.

- [ ] **Step 1: Extend the test with successful and failed fake modes**

After releasing file descriptor 8, make the fake rclone:

```bash
if [[ "${FAKE_RCLONE_FAIL:-0}" == "1" && "$1" == "sync" ]]; then
  for number in $(seq 1 25); do printf 'error-line-%s\n' "$number"; done
  exit 7
fi
if [[ "$1" == "sync" ]]; then
  for number in $(seq 1 25); do printf 'output-line-%s\n' "$number"; done
fi
exit 0
```

Run the script with `RCLONE_BACKUP_MAX_STAGE_LINES=10`. Assert that an unlocked
successful run makes exactly three `sync` calls and one `lsf` call, retains
`output-line-25`, omits `output-line-1`, and records success. Then run in
failure mode and assert exit status `7`, retained `error-line-25`, omitted
`error-line-1`, and only one new `sync` call.

- [ ] **Step 2: Run the extended test and verify RED**

Run: `bash tests/test-rclone-backup.sh`

Expected: FAIL because the current script logs all fake output and does not
stop with rclone's exit status.

- [ ] **Step 3: Implement bounded logging**

Add a `run_rclone` function that pipes combined rclone output through a
bounded GNU awk ring buffer:

```bash
rclone "$@" 2>&1 | awk -v max="$MAX_STAGE_LOG_LINES" '
  { lines[NR % max] = $0 }
  END {
    if (NR > max) {
      printf "[... %d earlier lines omitted ...]\n", NR - max
    }
    start = NR > max ? NR - max + 1 : 1
    for (line = start; line <= NR; line++) {
      print lines[line % max]
    }
  }
' >> "$LOG_FILE"
rclone_status=${PIPESTATUS[0]}
```

Record the exit status, return it from the wrapper, remove `--progress`, and
stop before later stages when a backup stage fails. Before the routine starts,
trim an oversized persistent log to its final `MAX_LOG_BYTES` using a temporary
file and atomic rename while the lock is held.

- [ ] **Step 4: Run syntax and behavior tests**

Run:

```bash
bash -n rclone_backup.sh tests/test-rclone-backup.sh
bash tests/test-rclone-backup.sh
```

Expected: both commands exit `0`; the test reports all assertions passed.

- [ ] **Step 5: Commit the tested implementation**

```bash
git add rclone_backup.sh tests/test-rclone-backup.sh
git commit -m "fix: prevent overlapping rclone backups"
```

### Task 3: Clean up the live incident and verify recovery

**Files:**
- Modify: `Homelab/Documentation` note in the mounted Obsidian vault.

**Interfaces:**
- Consumes: exact live process IDs re-resolved immediately before termination.
- Produces: no stale backup processes, reclaimed root filesystem space, and a documented recovery path.

- [ ] **Step 1: Preserve the incident tail**

Write the final 10 MiB of `rclone_backup.log` to a timestamped incident file on
the same filesystem. Verify the preserved file size and readable tail before
continuing.

- [ ] **Step 2: Terminate only the stale backup process trees**

Resolve exact commands matching `/bin/bash /home/ethan/docker/rclone_backup.sh`
and their `rclone sync` children. Send `TERM`, wait up to 30 seconds, then send
`KILL` only to exact survivors. Confirm no matching job remains.

- [ ] **Step 3: Truncate the active incident log**

Run `truncate -s 0 /home/ethan/docker/rclone_backup.log` only after the stale
writers are gone. Verify its apparent size is zero and root filesystem space
has been reclaimed.

- [ ] **Step 4: Verify live single-instance behavior**

Hold the deployed lock, invoke the deployed script with an isolated log
override, and verify it exits `0` without starting rclone. Confirm the crontab
line is unchanged and inspect `free -h`, `swapon --show`, Frigate health, and
Home Assistant health.

- [ ] **Step 5: Update durable documentation**

Record the root cause, lock behavior, bounded logging, incident-tail path,
cleanup outcome, cron schedule, and verification evidence in the appropriate
`Homelab/Documentation/` note. Do not include credentials or raw logs.
