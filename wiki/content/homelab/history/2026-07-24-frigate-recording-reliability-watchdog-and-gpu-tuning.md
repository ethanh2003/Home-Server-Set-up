# 2026-07-24T22-07-45-0BKs-frigate_recording_reliability_watchdog_and_gpu_tuning

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f962b-92fa-7331-aa71-245de17a46d4
updated_at: 2026-07-25T02:08:07+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/24/rollout-2026-07-24T22-07-45-019f962b-92fa-7331-aa71-245de17a46d4.jsonl
cwd: /home/ethan

# Frigate recording reliability was restored and hardened after a Couch View outage caused by host memory pressure.

Rollout context: Work happened in `/home/ethan/docker` (primary repo) with live Frigate at `/home/ethan/docker/frigate`, Home Assistant at `/home/ethan/docker/home-assistant`, recordings under `/mnt/data_14tb/media/frigate/recordings`, and Obsidian notes under `/data/Obsidian/Main`. The user’s issue began as `No Preview Found for Living Room - Couch View`, but investigation showed the deeper failure was a host-wide OOM event that had stalled Couch View recording while live view still looked healthy. The later work expanded into making Frigate more resilient to this class of failure.

## Task 1: Restore Couch View and build a recording-freshness watchdog

Outcome: success

Preference signals:
- The user did not want a cosmetic dashboard tweak; the incident was treated as a live break/fix and the user accepted the agent’s pivot to root-cause investigation and then to remediation.
- When the system had a live outage, the user accepted immediate service restoration before development work, indicating that when a live recording path is broken the next agent should prioritize restoring service first.

Key steps:
- Confirmed the Frigate container and Home Assistant were both healthy while Couch View preview failures coincided with host OOM pressure and overlapping `rclone` jobs from earlier tasks.
- Restored Couch View by restarting Frigate once after taking backups of the live Frigate config and compose file.
- Verified both cameras resumed producing fresh native 2560×1920 H.264 segments.
- Wrote a new watchdog script at `frigate/scripts/recording_watchdog.py` that:
  - scans the current and previous recording hour,
  - treats zero-byte or stale segments as invalid,
  - confirms stale status on a later run,
  - restarts Frigate only after confirmation,
  - waits for container health and fresh ffprobe-valid segments,
  - enforces a cooldown to avoid repeatedly interrupting the healthy camera.
- Added unit and boundary tests for segment validity, stale/healthy policy, dry-run restart behavior, and ffprobe probing.

Failures and how to do differently:
- The first test pass failed because the script file did not exist yet; the fix was to create the module and keep the tests tightly coupled to observable behavior.
- The first pass at state handling revealed that a oneshot systemd runtime directory would vanish between runs; later tasks fixed that with `RuntimeDirectoryPreserve=yes`.

Reusable knowledge:
- For this host, the relevant recording directories are under `/mnt/data_14tb/media/frigate/recordings`, and the freshest MP4 can be found by checking the current and previous hour directories for each camera.
- The watchdog’s useful thresholds ended up being: stale after 90 seconds, confirm on a second run after 30 seconds, and cooldown for 10 minutes.
- The watchdog should be exercised in dry-run mode against an isolated fixture before enabling live restart behavior.

References:
- `frigate/scripts/recording_watchdog.py`
- `frigate/tests/test_recording_watchdog.py`
- `docker-compose.yml` change later moved Frigate to 3 GiB memory and added `CAP_PERFMON`
- `systemd` units for the watchdog were added later

## Task 2: Add hardened systemd scheduling for the watchdog

Outcome: success

Preference signals:
- The user accepted automatic recovery only after the agent validated it with tests and live service checks; that suggests future similar recovery automation should be tested and scoped, not hand-waved.

Key steps:
- Added `frigate/systemd/frigate-recording-watchdog.service` and `.timer`.
- Scheduled the watchdog every 30 seconds.
- Hardened the service with oneshot semantics and basic sandboxing.
- Verified the timer is enabled and active, and that the service exits successfully while preserving state across runs.

Failures and how to do differently:
- The first live verification revealed a state-lifetime bug: `RuntimeDirectoryPreserve` was missing, so oneshot completion would clear the runtime state used for confirmation/cooldown. The fix was to add `RuntimeDirectoryPreserve=yes` and a regression test for it.
- `systemctl status` on a oneshot service can return a nonzero status even when the service run itself succeeded; use the journal and the service’s exit status, not only the shell exit code, to judge success.

Reusable knowledge:
- `RuntimeDirectoryPreserve=yes` is required here so the watchdog’s confirmation/cooldown state survives completed runs.
- `systemd-analyze verify` was useful for validating the units before installation.
- The installed watchdog timer is persistent and runs every 30 seconds; the service itself is intentionally oneshot.

References:
- `/etc/systemd/system/frigate-recording-watchdog.service`
- `/etc/systemd/system/frigate-recording-watchdog.timer`
- `systemctl list-timers --all frigate-recording-watchdog.timer`
- `journalctl -u frigate-recording-watchdog.service`

## Task 3: Apply Frigate reliability configuration for native recording and GPU telemetry

Outcome: success

Preference signals:
- The user implicitly accepted the agent’s service-first, proof-first approach: the live change was only kept after canaries, config validation, and runtime evidence all passed.

Key steps:
- Backed up the live `config.yml` and `docker-compose.yml` before mutating them.
- Changed Frigate to use local go2rtc restream inputs per camera and direct stream copy for recording.
- Kept detection/enrichment disabled for both cameras.
- Moved Frigate’s cgroup limits from 2 GiB to 3 GiB memory with 1536 MiB reservation and 3 GiB swap cap, keeping host swap unavailable to Frigate.
- Added the narrow `CAP_PERFMON` capability so Intel GPU telemetry could work.
- Verified the live config with Frigate’s validator, `docker compose config -q`, and runtime inspection.
- Ran a 60-second AAC passthrough canary before enabling audio copy for recording.

Failures and how to do differently:
- The first config test assumed a `hwaccel_args` key in the wrong place and failed; the live config needed to be checked and then updated to reflect how Frigate actually expresses the effective settings.
- A small verification probe initially failed because of shell/Python quoting, not because the system was wrong; use multi-line probes or simpler formatting to avoid that error when verifying video artifacts.

Reusable knowledge:
- Effective live Frigate settings after the change:
  - `hwaccel_args = preset-vaapi`
  - `output_args.record = preset-record-generic-audio-copy`
  - each camera input path is `rtsp://127.0.0.1:8554/<camera>` with `preset-rtsp-restream`
  - detection disabled for both cameras
- Live ffmpeg output confirmed VAAPI decode/scale and `-c copy` recording output.
- go2rtc had exactly one producer and one Frigate consumer per camera after the change.
- Intel GPU telemetry became usable, and a post-change sample showed VAAPI activity.

References:
- `/home/ethan/docker/frigate/docker-compose.yml`
- `/home/ethan/docker/frigate/config/config.yml`
- `/home/ethan/docker/frigate/tests/test_reliability_config.py`
- `docker inspect frigate --format ...`
- `findmnt -T /mnt/data_14tb/media/frigate/recordings`

## Task 4: Roll out, observe stability, and document the result

Outcome: success

Preference signals:
- The user accepted the plan to implement immediately after approval, and the agent kept the rollout evidence-heavy instead of shortcutting to a “done” claim.

Key steps:
- Recreated Frigate once with the new config.
- Confirmed both cameras produced fresh native 2560×1920 H.264/AAC segments after the rollout.
