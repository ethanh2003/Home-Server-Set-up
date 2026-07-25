# 2026-07-04T20-53-48-oPiF-manage_stacks_restart_only_previously_running_services

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f2ee8-ae52-7192-a9b9-6d6686399311
updated_at: 2026-07-04T20:59:08+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/04/rollout-2026-07-04T20-53-48-019f2ee8-ae52-7192-a9b9-6d6686399311.jsonl
cwd: /home/ethan

# Updated `docker/manage-stacks.sh` so `restart` only brings back services that were already running.

Rollout context: The user asked to change `/home/ethan/docker/manage-stacks.sh` so `restart` does not restart every service in each compose stack. The work happened in `/home/ethan/docker`, and the file was already dirty before the edit, so the implementation had to preserve existing uncommitted changes.

## Task 1: Design the restart-only-running-services change

Outcome: success

Preference signals:
- The user asked to update `manage-stacks.sh` to “only restart containers that were already running” -> future similar changes should preserve existing run state rather than using a blanket stack restart.
- The user had an already-modified working tree and the assistant explicitly noted it should “preserve the current working-tree version of the file” -> future edits to this file should read the current diff first and avoid overwriting unrelated changes.

Key steps:
- Inspected `docker/manage-stacks.sh` and the existing `git diff` before editing.
- Confirmed the existing `restart` branch was `docker compose down && docker compose up -d --remove-orphans`, which would start every service in the stack.
- Chose a Bash-array approach using `docker compose ps --services --filter status=running` to snapshot running services before `down`.

Failures and how to do differently:
- A root-level `docker compose ps` from `/home/ethan/docker` failed with `no configuration file provided: not found`; that directory is a stack parent, not a compose project. Future checks should run inside an actual stack directory or only use CLI help for capability checks.
- A first fake-Docker verification harness was wrong because it shifted arguments before matching them; the corrected harness was needed to validate the script behavior.

Reusable knowledge:
- `docker compose ps --services --filter status=running` is supported by the installed Compose CLI and is the right primitive for capturing currently running services.
- `/home/ethan/docker/manage-stacks.sh` discovers stacks by scanning immediate subdirectories for `docker-compose.yml`.
- The `restart` branch now snapshots running services, runs `docker compose down`, then calls `docker compose up -d --remove-orphans "${RUNNING_SERVICES[@]}"` only when the snapshot is non-empty.

References:
- [1] `git -C /home/ethan/docker diff -- manage-stacks.sh` showed the file was already modified before the change, including prior argument-handling cleanup.
- [2] Relevant script lines after the patch: `mapfile -t RUNNING_SERVICES < <(docker compose ps --services --filter status=running)` followed by conditional `down` and `up` in the `restart)` branch.
- [3] `bash -n /home/ethan/docker/manage-stacks.sh` exited cleanly.
- [4] Isolated fake-Docker harness output: empty stack printed `No running services found before restart; skipping start.`; stack with `web` and `worker` running invoked `docker compose up -d --remove-orphans web worker`.

## Task 2: Implement and verify the script change

Outcome: success

Preference signals:
- The user requested an implementation, not a discussion-only answer -> future similar requests should proceed to code changes once the plan is agreed.
- The user’s wording focused on “only restart containers that were already running” -> the behavior should stay narrowly scoped to the `restart` action, not `start`/`stop`/`pull`.

Key steps:
- Patched only the `restart` branch in `docker/manage-stacks.sh`.
- Kept `ensure_network` behavior unchanged for `restart`.
- Verified syntax with `bash -n`.
- Verified Compose CLI support with `docker compose ps --help`.
- Verified the runtime call pattern using a temporary fake `docker` executable instead of touching live stacks.

Failures and how to do differently:
- The first harness run incorrectly returned no running services for the “running” stack because the fake `docker` script consumed its own arguments too early. The corrected harness fixed the issue by matching on the original positional args.
- The actual `/home/ethan/docker` directory should not be used as a compose project root for ad hoc `docker compose` commands; use the relevant stack directory or a harness.

Reusable knowledge:
- The final script behavior is:
  - snapshot running services before `down`
  - `down` the stack
  - skip `up` if nothing was running
  - otherwise restart only the previously running services
- Verification that mattered was behavioral, not just syntax: the fake-Docker harness confirmed the exact `up` arguments passed per stack.

References:
- [1] Final diff hunk in `manage-stacks.sh`:
  - `mapfile -t RUNNING_SERVICES < <(docker compose ps --services --filter status=running)`
  - `if docker compose down; then ... docker compose up -d --remove-orphans "${RUNNING_SERVICES[@]}" ... fi`
- [2] `docker compose ps --help` showed `--services` and `--filter status=running` are valid options.
- [3] Final harness output:
  - empty stack: `No running services found before restart; skipping start.`
  - running stack: `docker compose up -d --remove-orphans web worker`
- [4] The work remained in `/home/ethan/docker/manage-stacks.sh` and did not touch live containers during verification.
