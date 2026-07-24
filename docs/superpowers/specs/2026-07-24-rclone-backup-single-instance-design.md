# Rclone Backup Single-Instance Design

## Problem

`rclone_backup.sh` runs from cron at 03:00 and 15:00 without mutual
exclusion. A backup can take longer than twelve hours, so later schedules start
additional copies against the same `GDrive:Backups/Current` destinations.

On 2026-07-24, seven scheduled runs were active simultaneously, including jobs
dating to 2026-07-21. They generated hundreds of thousands of Google Drive
`404` errors, expanded `rclone_backup.log` to 185 GB, exhausted swap, and
contributed to host-wide memory pressure that interrupted Home Assistant's
Frigate previews.

## Design

### Single-instance execution

The script will acquire a non-blocking advisory lock before starting a backup.
The default lock path will be `/run/user/<uid>/rclone_backup.lock`, with an
environment override for isolated testing. If another invocation already holds
the lock, the new invocation will record a concise skip message and exit
successfully without running `rclone`.

Keeping the lock inside the script protects cron and manual invocations without
requiring scheduler-specific behavior.

### Bounded logging

Interactive `rclone --progress` output will be removed from scheduled backups.
Each `rclone` operation will retain its final 2,000 output lines plus its exit
status in the main log. This prevents repeated remote errors from growing the
log without limit while preserving enough context to investigate a failed
stage.

After acquiring the lock, the script will retain only the final 10 MiB when the
persistent log is larger than 10 MiB. The log path and limits will support
environment overrides for isolated testing.

### Existing incident cleanup

All stale `rclone_backup.sh` process trees will be terminated because none of
them owns the new lock and several are concurrently mutating the same remote
destinations. The final 10 MB of the 185 GB incident log will be preserved in a
timestamped incident file. The active log will then be truncated in place so
open file descriptors cannot keep the deleted space allocated.

The next scheduled run will start cleanly. No replacement full backup will be
started during remediation.

## Error handling

- Lock contention is an expected skip and exits successfully.
- A failed `rclone` stage records its bounded output and nonzero status.
- The script stops before later backup or pruning stages and exits nonzero when
  a backup stage fails.
- Cleanup targets only process trees whose command line is the deployed
  `rclone_backup.sh` or its known `rclone sync` children.
- The Google Drive configuration and credentials are not printed, copied, or
  stored in tests or documentation.

## Testing

A shell integration test will:

1. Copy the real script into an isolated temporary directory.
2. Put a controlled fake `rclone` ahead of the real binary in `PATH`, and use
   isolated lock and log paths through the supported environment overrides.
3. Hold the isolated script lock and invoke the copied script.
4. Assert that the invocation exits quickly and the fake `rclone` is never
   called.
5. Release the lock and assert that the three sync operations and one archive
   listing run through the fake, with no purge when the listing is empty.

The test must fail against the current unlocked script before production code
is changed, then pass after the implementation.

Live verification will confirm:

- no stale backup or `rclone sync` processes remain;
- the large log space is reclaimed;
- a held lock prevents a second invocation;
- shell syntax and the integration test pass;
- the existing cron schedule remains unchanged;
- host memory and swap pressure improve without restarting unrelated services.
