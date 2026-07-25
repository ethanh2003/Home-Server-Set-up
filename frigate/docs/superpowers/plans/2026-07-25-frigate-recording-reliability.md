# Frigate Recording Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Preserve native-quality continuous recording for both living-room cameras and automatically recover when a recording pipeline becomes stale even if Frigate still reports healthy.

**Architecture:** go2rtc owns one upstream RTSP connection per camera and Frigate consumes the local restream for recording, motion decode, audio, and live view. Video remains direct-copy while VAAPI handles decode/scale only. A separately tested host systemd watchdog evaluates per-camera recording freshness and performs one cooldown-protected Frigate restart when the application fails to recover a dead capture pipeline.

**Tech Stack:** Frigate 0.17, go2rtc, FFmpeg/ffprobe, VAAPI, Docker Compose, Python 3 standard library, unittest, systemd

## Global Constraints

- Recording continuity is the highest priority; object detection and optional enrichment workloads remain disabled.
- Preserve both cameras' native 2560x1920 H.264 main streams at their native average frame rate and bitrate.
- Preserve seven-day continuous retention on `/mnt/data_14tb/media/frigate`.
- Never re-encode recording video.
- Use VAAPI for decode/scale, not recording encode.
- Keep credential-bearing camera URLs only in ignored mode-0600 configuration and backup files.
- Retain two CPUs, 512 MiB shared memory, 768 PIDs, and no container swap.
- Set the Frigate memory limit to 3 GiB, reservation to 1536 MiB, and memory-plus-swap limit to 3 GiB.
- Do not make Frigate privileged.
- Recreate or restart only Frigate; preserve unrelated worktree and service state.
- Back up live configuration before editing and verify both cameras after every runtime mutation.
- The watchdog checks every 30 seconds, considers segments stale after 90 seconds, confirms staleness on a second run, and enforces a ten-minute restart cooldown.
- Preserve the watchdog runtime directory across completed oneshot runs so confirmation and cooldown state survives between timer intervals.
- Update Obsidian only with secret-free verified operational facts.

---

### Task 1: Build the recording-freshness watchdog

**Files:**
- Create: `frigate/scripts/recording_watchdog.py`
- Create: `frigate/tests/test_recording_watchdog.py`

**Interfaces:**
- Consumes: camera names from repeated `--camera` arguments, host recording root from `--recordings-root`, Compose file from `--compose-file`, and persistent state from `--state-file`
- Produces: `newest_segment(root: Path, camera: str, now: datetime) -> Path | None`, `segment_is_valid(path: Path, now: datetime, max_age: int) -> bool`, `evaluate_camera(...) -> str`, and a CLI exit status of 0 for healthy/recovered or 1 for stale/unrecoverable

- [x] **Step 1: Create tests for current-hour and previous-hour segment discovery**

Write `frigate/tests/test_recording_watchdog.py` using `unittest`, `tempfile`, and `unittest.mock`. Include:

```python
def recording_path(root: Path, when: datetime, camera: str, name: str) -> Path:
    path = root / when.strftime("%Y-%m-%d") / when.strftime("%H") / camera / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"segment")
    os.utime(path, (when.timestamp(), when.timestamp()))
    return path

class SegmentTests(unittest.TestCase):
    def test_newest_segment_checks_current_and_previous_hour(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            now = datetime(2026, 7, 25, 0, 0, 20, tzinfo=timezone.utc)
            expected = recording_path(
                root, now - timedelta(seconds=30), "camera_a", "59.50.mp4"
            )
            self.assertEqual(
                watchdog.newest_segment(root, "camera_a", now),
                expected,
            )

    def test_zero_byte_segment_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.mp4"
            path.touch()
            now = datetime.now(timezone.utc)
            self.assertFalse(watchdog.segment_is_valid(path, now, 90))
```

- [x] **Step 2: Run the focused tests and verify they fail**

Run:

```bash
cd /home/ethan/docker
python3 -m unittest -v frigate/tests/test_recording_watchdog.py
```

Expected: import or attribute failures because the watchdog module does not exist.

- [x] **Step 3: Implement segment discovery and validation**

In `frigate/scripts/recording_watchdog.py`, implement:

```python
def hour_directories(root: Path, now: datetime) -> list[Path]:
    return [
        root / stamp.strftime("%Y-%m-%d") / stamp.strftime("%H")
        for stamp in (now, now - timedelta(hours=1))
    ]

def newest_segment(root: Path, camera: str, now: datetime) -> Path | None:
    matches = [
        path
        for hour in hour_directories(root, now)
        for path in (hour / camera).glob("*.mp4")
        if path.is_file()
    ]
    return max(matches, key=lambda path: path.stat().st_mtime, default=None)

def segment_is_valid(path: Path | None, now: datetime, max_age: int) -> bool:
    if path is None or path.stat().st_size == 0:
        return False
    age = now.timestamp() - path.stat().st_mtime
    return 0 <= age <= max_age
```

Use timezone-aware UTC timestamps throughout.

- [x] **Step 4: Add policy tests for confirmation and cooldown**

Add tests that use a temporary JSON state file and assert:

```python
self.assertEqual(first_result.action, "confirm")
self.assertEqual(second_result.action, "restart")
self.assertEqual(cooldown_result.action, "cooldown")
```

Cover these cases:

- healthy recording clears prior stale state;
- first stale observation records `first_stale_at` without restart;
- stale observation at least 30 seconds later requests restart;
- a restart within the previous 600 seconds suppresses another restart;
- one stale camera is reported without hiding the other camera's healthy state.

- [x] **Step 5: Run the policy tests and verify they fail**

Run:

```bash
cd /home/ethan/docker
python3 -m unittest -v frigate/tests/test_recording_watchdog.py
```

Expected: failures for the not-yet-implemented state and policy functions.

- [x] **Step 6: Implement state, locking, restart, health wait, and probing**

Implement a `CameraResult` dataclass with `camera`, `action`, and `segment` fields. Store:

```json
{
  "first_stale_at": {"camera_name": 0},
  "last_restart_at": 0
}
```

The CLI must:

- acquire an exclusive non-blocking `fcntl.flock` on `--lock-file`;
- evaluate every configured camera before deciding whether to restart;
- return 0 and clear that camera's stale state when a valid fresh segment exists;
- return 1 on first confirmation, cooldown, failed restart, failed health wait, or failed post-restart recording verification;
- execute exactly `docker compose -f <compose-file> restart frigate` for a confirmed stale camera outside cooldown;
- poll `docker inspect frigate --format={{.State.Health.Status}}` for at most 120 seconds;
- wait at most 120 additional seconds for fresh segments from both cameras;
- run `/usr/bin/ffprobe -v error -show_entries stream=codec_name,width,height -of json <segment>` on each recovered segment;
- log camera, segment age, action, and recovery outcome to stdout/stderr without printing RTSP URLs or configuration contents;
- support `--dry-run`, which reports the intended restart without running Docker.

- [x] **Step 7: Run all watchdog tests**

Run:

```bash
cd /home/ethan/docker
python3 -m unittest -v frigate/tests/test_recording_watchdog.py
python3 -m py_compile frigate/scripts/recording_watchdog.py
```

Expected: all tests pass and compilation exits 0.

- [x] **Step 8: Commit the watchdog**

Run:

```bash
git -C /home/ethan/docker add \
  frigate/scripts/recording_watchdog.py \
  frigate/tests/test_recording_watchdog.py
git -C /home/ethan/docker diff --cached --check
git -C /home/ethan/docker commit -m "feat: monitor Frigate recording freshness"
```

Expected: the commit contains only the watchdog and its tests.

---

### Task 2: Add hardened systemd scheduling

**Files:**
- Create: `frigate/systemd/frigate-recording-watchdog.service`
- Create: `frigate/systemd/frigate-recording-watchdog.timer`
- Test: `frigate/tests/test_recording_watchdog.py`

**Interfaces:**
- Consumes: `/usr/bin/python3`, `frigate/scripts/recording_watchdog.py`, Docker, the Compose file, and the recordings filesystem
- Produces: `frigate-recording-watchdog.service` and a 30-second persistent timer

- [x] **Step 1: Write a failing unit-content test**

Add a test that reads the unit templates and asserts:

```python
        self.assertIn("Type=oneshot", service)
        self.assertIn("NoNewPrivileges=true", service)
        self.assertIn("RuntimeDirectoryPreserve=yes", service)
        self.assertIn("OnUnitActiveSec=30s", timer)
self.assertIn("Persistent=true", timer)
self.assertNotIn("rtsp://", service + timer)
```

- [x] **Step 2: Run the focused unit test and verify it fails**

Run:

```bash
cd /home/ethan/docker
python3 -m unittest -v \
  frigate.tests.test_recording_watchdog.SystemdUnitTests
```

Expected: failure because the unit files do not exist.

- [x] **Step 3: Create the oneshot service**

Create `frigate/systemd/frigate-recording-watchdog.service` with:

```ini
[Unit]
Description=Verify Frigate per-camera recording freshness
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=root
Group=root
WorkingDirectory=/home/ethan/docker
ExecStart=/usr/bin/python3 /home/ethan/docker/frigate/scripts/recording_watchdog.py --camera living_room_-_dog_view --camera living_room_-_couch_view --recordings-root /mnt/data_14tb/media/frigate/recordings --compose-file /home/ethan/docker/frigate/docker-compose.yml --state-file /run/frigate-recording-watchdog/state.json --lock-file /run/frigate-recording-watchdog/lock --max-age 90 --confirm-after 30 --cooldown 600
RuntimeDirectory=frigate-recording-watchdog
RuntimeDirectoryMode=0750
RuntimeDirectoryPreserve=yes
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=read-only
ProtectSystem=strict
ReadOnlyPaths=/home/ethan/docker/frigate /mnt/data_14tb/media/frigate
ReadWritePaths=/run/frigate-recording-watchdog /run/docker.sock
Nice=10
IOSchedulingClass=idle
TimeoutStartSec=300
```

- [x] **Step 4: Create the timer**

Create `frigate/systemd/frigate-recording-watchdog.timer` with:

```ini
[Unit]
Description=Run Frigate recording freshness watchdog

[Timer]
OnBootSec=2min
OnUnitActiveSec=30s
AccuracySec=5s
Persistent=true
Unit=frigate-recording-watchdog.service

[Install]
WantedBy=timers.target
```

- [x] **Step 5: Validate templates and tests**

Run:

```bash
cd /home/ethan/docker
python3 -m unittest -v frigate/tests/test_recording_watchdog.py
systemd-analyze verify \
  /home/ethan/docker/frigate/systemd/frigate-recording-watchdog.service \
  /home/ethan/docker/frigate/systemd/frigate-recording-watchdog.timer
```

Expected: tests pass and `systemd-analyze verify` reports no errors.

- [x] **Step 6: Commit the units**

Run:

```bash
git -C /home/ethan/docker add \
  frigate/systemd/frigate-recording-watchdog.service \
  frigate/systemd/frigate-recording-watchdog.timer \
  frigate/tests/test_recording_watchdog.py
git -C /home/ethan/docker diff --cached --check
git -C /home/ethan/docker commit -m "ops: schedule Frigate recording recovery"
```

Expected: the commit contains only the systemd templates and associated test change.

---

### Task 3: Apply the reliability configuration

**Files:**
- Modify: `frigate/config/config.yml` (ignored, contains secrets)
- Modify: `frigate/docker-compose.yml`
- Create: `frigate/tests/test_reliability_config.py`

**Interfaces:**
- Consumes: the existing direct camera URLs under `go2rtc.streams`
- Produces: local Frigate inputs at `rtsp://127.0.0.1:8554/<camera-name>`, explicit VAAPI decode, disabled detection, direct-copy recording video, and the 3 GiB cgroup policy

- [x] **Step 1: Create timestamped restricted backups**

Run:

```bash
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
install -m 600 -T \
  /home/ethan/docker/frigate/config/config.yml \
  "/home/ethan/docker/frigate/config/config.yml.codex-bak-${stamp}-recording-reliability"
install -m 600 -T \
  /home/ethan/docker/frigate/docker-compose.yml \
  "/home/ethan/docker/frigate/docker-compose.yml.codex-bak-${stamp}-recording-reliability"
cmp /home/ethan/docker/frigate/config/config.yml \
  "/home/ethan/docker/frigate/config/config.yml.codex-bak-${stamp}-recording-reliability"
cmp /home/ethan/docker/frigate/docker-compose.yml \
  "/home/ethan/docker/frigate/docker-compose.yml.codex-bak-${stamp}-recording-reliability"
```

Expected: both `cmp` commands exit 0 and backups are mode 0600.

- [x] **Step 2: Test AAC passthrough from both local restreams**

For each camera, record a disposable 60-second sample from its current go2rtc stream:

```bash
sample_dir="$(mktemp -d)"
/usr/bin/ffmpeg -hide_banner -loglevel warning -y -t 60 \
  -rtsp_transport tcp \
  -i rtsp://127.0.0.1:8554/living_room_-_dog_view \
  -map 0:v:0 -map 0:a:0 -c copy "${sample_dir}/dog.mp4"
/usr/bin/ffmpeg -hide_banner -loglevel warning -y -t 60 \
  -rtsp_transport tcp \
  -i rtsp://127.0.0.1:8554/living_room_-_couch_view \
  -map 0:v:0 -map 0:a:0 -c copy "${sample_dir}/couch.mp4"
/usr/bin/ffprobe -v error -show_entries \
  stream=codec_name,width,height,avg_frame_rate \
  -show_entries format=duration -of json "${sample_dir}/dog.mp4"
/usr/bin/ffprobe -v error -show_entries \
  stream=codec_name,width,height,avg_frame_rate \
  -show_entries format=duration -of json "${sample_dir}/couch.mp4"
```

Expected: both files contain H.264 2560x1920 video, AAC audio, approximately 60 seconds duration, and FFmpeg reports no non-monotonic or backward-timestamp errors. Use `preset-record-generic-audio-copy` only if both pass; otherwise retain `preset-record-generic-audio-aac`.

- [x] **Step 3: Write a failing configuration-policy test**

Create `frigate/tests/test_reliability_config.py` that loads the live YAML files and asserts:

```python
self.assertEqual(config["ffmpeg"]["hwaccel_args"], "preset-vaapi")
self.assertIn(
    config["ffmpeg"]["output_args"]["record"],
    {"preset-record-generic-audio-copy", "preset-record-generic-audio-aac"},
)
for camera in CAMERAS:
    entry = config["cameras"][camera]
    self.assertFalse(entry["detect"]["enabled"])
    input_config = entry["ffmpeg"]["inputs"][0]
    self.assertEqual(input_config["path"], f"rtsp://127.0.0.1:8554/{camera}")
    self.assertEqual(input_config["input_args"], "preset-rtsp-restream")
    self.assertEqual(set(input_config["roles"]), {"record", "detect", "audio"})
self.assertEqual(service["cpus"], "2.0")
self.assertEqual(service["mem_limit"], "3g")
self.assertEqual(service["mem_reservation"], "1536m")
self.assertEqual(service["memswap_limit"], "3g")
self.assertEqual(service["pids_limit"], 768)
self.assertEqual(service["shm_size"], "512mb")
self.assertNotIn("privileged", service)
```

Also assert that the two `go2rtc.streams` values remain present without printing or snapshotting their credential-bearing values.

- [x] **Step 4: Run the policy test and verify it fails**

Run:

```bash
cd /home/ethan/docker
python3 -m unittest -v frigate/tests/test_reliability_config.py
```

Expected: failures for direct camera FFmpeg inputs, implicit VAAPI selection, missing explicit disabled detection, and the old memory values.

- [x] **Step 5: Apply the minimal YAML and Compose changes**

In `config/config.yml`:

- add top-level `ffmpeg.hwaccel_args: preset-vaapi`;
- set `ffmpeg.output_args.record` to the audio preset selected in Step 2;
- keep each credential-bearing `go2rtc.streams` source unchanged;
- replace each camera FFmpeg path with its matching localhost go2rtc URL;
- add `input_args: preset-rtsp-restream` to each local input;
- set `detect.enabled: false` for both cameras;
- preserve recording retention, live streams, MQTT, notifications, and disabled enrichment values.

In `docker-compose.yml`, set:

```yaml
    cpus: "2.0"
    mem_limit: "3g"
    mem_reservation: "1536m"
    memswap_limit: "3g"
    pids_limit: 768
```

- [x] **Step 6: Test the narrow GPU telemetry capability without changing Frigate**

Run:

```bash
docker run --rm \
  --cap-add PERFMON \
  --device /dev/dri/renderD128:/dev/dri/renderD128 \
  --entrypoint /usr/bin/intel_gpu_top \
  ghcr.io/blakeblackshear/frigate:stable -L
```

Expected: if the command lists the Intel GPU and exits 0, add this to the Frigate service:

```yaml
    cap_add:
      - PERFMON
```

If the command still reports PMU permission failure, do not add the capability. Never add `privileged: true`.

- [x] **Step 7: Run static configuration validation**

Run:

```bash
cd /home/ethan/docker
python3 -m unittest -v frigate/tests/test_reliability_config.py
docker compose -f /home/ethan/docker/frigate/docker-compose.yml config -q
docker exec frigate python3 -m frigate --validate-config
```

Expected: tests pass, Compose exits 0, and Frigate prints `Your config file is valid`.

- [x] **Step 8: Commit the secret-free policy files**

Run:

```bash
git -C /home/ethan/docker add \
  frigate/docker-compose.yml \
  frigate/tests/test_reliability_config.py
git -C /home/ethan/docker diff --cached --check
git -C /home/ethan/docker diff --cached --name-only
git -C /home/ethan/docker commit -m "ops: prioritize Frigate recording reliability"
```

Expected: only the Compose file and policy test are committed. `config/config.yml` and its backup remain ignored and uncommitted.

---

### Task 4: Roll out, install recovery, and prove native-quality recording

**Files:**
- Install: `/etc/systemd/system/frigate-recording-watchdog.service`
- Install: `/etc/systemd/system/frigate-recording-watchdog.timer`
- Modify: `/data/Obsidian/Main/Homelab/Memory/Frigate.md`
- Modify: `frigate/docs/superpowers/plans/2026-07-25-frigate-recording-reliability.md`

**Interfaces:**
- Consumes: validated Frigate/Compose configuration, tested watchdog, and systemd templates
- Produces: a healthy Frigate runtime, fresh valid recordings for both cameras, an enabled recovery timer, verification evidence, and secret-free operations documentation

- [x] **Step 1: Capture pre-rollout state**

Record without storing secrets:

```bash
docker inspect frigate --format \
  'health={{.State.Health.Status}} memory={{.HostConfig.Memory}} reservation={{.HostConfig.MemoryReservation}} swap={{.HostConfig.MemorySwap}} cpus={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}}'
docker exec frigate cat /sys/fs/cgroup/memory.events
docker stats --no-stream frigate
find /mnt/data_14tb/media/frigate/recordings -type f -name '*.mp4' \
  -path '*/living_room_-_dog_view/*' -printf '%T@ %p\n' | sort -nr | head -1
find /mnt/data_14tb/media/frigate/recordings -type f -name '*.mp4' \
  -path '*/living_room_-_couch_view/*' -printf '%T@ %p\n' | sort -nr | head -1
df -h /mnt/data_14tb/media/frigate
```

Expected: Dog View is fresh, Couch View's stale baseline is visible, and the recording filesystem is writable with adequate space.

- [x] **Step 2: Recreate only Frigate once**

Run:

```bash
docker compose -f /home/ethan/docker/frigate/docker-compose.yml \
  up -d --force-recreate --no-deps frigate
```

Poll for up to 120 seconds:

```bash
docker inspect frigate --format '{{.State.Health.Status}}'
```

Expected: `healthy`.

- [x] **Step 3: Verify both recording pipelines before installing automation**

Wait up to 120 seconds for a new segment from each camera. Probe the newest segment for each:

```bash
for camera in living_room_-_dog_view living_room_-_couch_view; do
  newest="$(
    find /mnt/data_14tb/media/frigate/recordings \
      -type f -name '*.mp4' -path "*/${camera}/*" \
      -printf '%T@ %p\n' |
      sort -nr |
      head -1 |
      cut -d' ' -f2-
  )"
  test -n "${newest}"
  /usr/bin/ffprobe -v error \
    -show_entries stream=codec_name,width,height,avg_frame_rate \
    -show_entries format=duration,size \
    -of json "${newest}"
done
```

Expected for both: non-empty H.264 video, 2560x1920, native average frame rate, valid audio, and a recent modification time. Couch View must have a segment newer than the rollout start time.

- [x] **Step 4: Verify effective restream, GPU, and cgroup policy**

Check the effective API without printing credential-bearing source URLs. Confirm:

- both camera FFmpeg hosts are `127.0.0.1:8554`;
- both detections are disabled;
- VAAPI is the effective hardware acceleration preset;
- record video output is copy;
- Docker reports `Memory=3221225472`, `MemoryReservation=1610612736`, `MemorySwap=3221225472`, `NanoCpus=2000000000`, `PidsLimit=768`, and `ShmSize=536870912`;
- `/sys/fs/cgroup/memory.events` has no new `oom` or `oom_kill` increments after recreation;
- if `PERFMON` was added, Frigate logs no longer contain a new PMU initialization failure and `/api/stats` contains Intel GPU utilization.

- [x] **Step 5: Install and validate the systemd units**

Run:

```bash
install -o root -g root -m 0644 \
  /home/ethan/docker/frigate/systemd/frigate-recording-watchdog.service \
  /etc/systemd/system/frigate-recording-watchdog.service
install -o root -g root -m 0644 \
  /home/ethan/docker/frigate/systemd/frigate-recording-watchdog.timer \
  /etc/systemd/system/frigate-recording-watchdog.timer
systemctl daemon-reload
systemctl enable --now frigate-recording-watchdog.timer
systemctl start frigate-recording-watchdog.service
systemctl status --no-pager frigate-recording-watchdog.service
systemctl list-timers --all frigate-recording-watchdog.timer
```

Expected: the live check exits successfully and the timer is enabled with its next run scheduled.
Also confirm `/run/frigate-recording-watchdog/state.json` remains present after
the oneshot service becomes inactive.

- [x] **Step 6: Exercise recovery policy without interrupting live cameras**

Run all unit tests, then invoke the watchdog against a temporary stale fixture with `--dry-run` twice at controlled timestamps.

Expected:

- first stale fixture run records confirmation state and does not request Docker restart;
- second confirmed run reports the exact intended Frigate restart but does not execute it;
- a third run inside cooldown reports cooldown;
- the live watchdog check remains successful;
- no live recording stream is intentionally stopped.

- [x] **Step 7: Observe post-rollout stability**

For at least ten minutes, sample every minute:

- newest segment age for both cameras;
- `docker stats --no-stream frigate`;
- Frigate PID count;
- cgroup `memory.events`;
- relevant Frigate/go2rtc errors;
- Frigate, Home Assistant, Mosquitto, reverse proxy, and live-view availability.

Expected: both cameras remain below the 90-second freshness threshold, memory remains comfortably below 3 GiB, no new OOM occurs, and unrelated services remain available.

- [x] **Step 8: Document verified operations in Obsidian**

Append a dated, secret-free section to `/data/Obsidian/Main/Homelab/Memory/Frigate.md` containing:

- go2rtc-single-ingest/local-restream architecture;
- native 2560x1920 direct-copy recording policy;
- VAAPI decode/scale role;
- disabled object detection and enrichment;
- applied cgroup values;
- watchdog script, units, thresholds, journal commands, and rollback commands;
- measured post-rollout usage and recording freshness;
- whether AAC passthrough and `PERFMON` were retained;
- Couch View recovery result.

Do not include camera URLs, credentials, private configuration values, or raw logs.

- [x] **Step 9: Mark the plan complete and commit documentation**

Mark completed checkboxes in this plan, then run:

```bash
git -C /home/ethan/docker add \
  frigate/docs/superpowers/plans/2026-07-25-frigate-recording-reliability.md
git -C /home/ethan/docker diff --cached --check
git -C /home/ethan/docker commit -m "docs: record Frigate reliability rollout"
```

Expected: the final documentation commit contains only this plan. Verify the Obsidian note separately because it is outside the repository.

## Rollback

If either camera does not produce fresh valid recordings after recreation:

1. Disable the timer:

   ```bash
   systemctl disable --now frigate-recording-watchdog.timer
   ```

2. Restore the exact timestamped `config.yml` and `docker-compose.yml` backups created in Task 3 with mode 0600.
3. Recreate only Frigate with `docker compose ... up -d --force-recreate --no-deps frigate`.
4. Confirm both recordings and live view.
5. Preserve diagnostic evidence in journald, but do not copy secrets or raw logs into Obsidian or Git.
