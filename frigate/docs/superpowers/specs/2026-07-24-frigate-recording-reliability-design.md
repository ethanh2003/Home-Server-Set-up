# Frigate Recording Reliability Design

## Goal

Make continuous recording the highest-priority Frigate workload for the two living-room cameras, preserve each camera's native 2560x1920 H.264 stream at approximately 25 FPS, and automatically recover when a camera capture pipeline stops even though the Frigate container still reports healthy.

This is a single-host self-healing design. It minimizes and detects recording gaps, but it cannot guarantee recording through host, storage, network, camera, or power failure. Eliminating those single points of failure requires an independent second recorder.

## Live failure and baseline

- The Intel N150 iGPU is available at `/dev/dri/renderD128`.
- Frigate successfully uses VAAPI hardware decoding and VAAPI scaling.
- Both cameras supply H.264 High video at 2560x1920 and approximately 25 FPS with AAC audio.
- Saved recordings use direct video stream copy, so recorded video retains the camera's native resolution, frame rate, and bitrate.
- Dog View is producing current recordings.
- Couch View stopped producing recordings after Frigate reached its 2 GiB memory cgroup limit and the kernel killed that camera's `frigate.capture` process.
- The container remained healthy and go2rtc continued serving Couch View live video, so container health and live-view success did not reveal the recording outage.
- Each camera is currently opened directly by both Frigate FFmpeg and go2rtc. Sharing one go2rtc ingest will reduce camera connections and centralize reconnect handling.
- Object detection, semantic search, face recognition, license-plate recognition, and bird classification are not part of the reliability-critical workload.

## Approved priorities

In descending order:

1. Keep both camera recording pipelines producing fresh, valid segments.
2. Preserve native video quality and seven-day continuous retention.
3. Recover automatically and visibly from a stale recording pipeline.
4. Offload decode and scaling to the Intel iGPU without making recording depend on GPU encoding.
5. Preserve live view, audio, MQTT, and current Frigate access.
6. Leave object detection and optional enrichment workloads disabled.

## Architecture

### Camera ingest

go2rtc will maintain the single direct RTSP connection to each physical camera. Frigate's FFmpeg input for each camera will read the matching local stream from:

```text
rtsp://127.0.0.1:8554/<camera-name>
```

The local inputs will use Frigate's `preset-rtsp-restream` input preset and supply the `record`, `detect`, and `audio` roles. Live view and recording will therefore share go2rtc's upstream camera connection instead of opening duplicate direct connections.

The original credential-bearing camera URLs remain only in the ignored Frigate configuration. Credentials will not be copied into committed files, documentation, monitoring scripts, logs, or Obsidian.

### Recording path

The recording path will copy the H.264 video stream without transcoding. VAAPI encoding will not be used for recordings because it would reduce quality and add GPU initialization and encoding to the critical path.

AAC audio passthrough will first be tested against both local restreams in a disposable recording. It will be used only if the resulting files have valid, monotonic timestamps and pass `ffprobe`. If either camera fails that test, Frigate will retain its existing AAC audio encode preset for reliability. Video remains direct-copy in either case.

Continuous recording remains enabled for seven days on `/mnt/data_14tb/media/frigate`. No camera resolution, bitrate, frame-rate, or retention reduction is allowed.

### GPU usage

The Frigate configuration will explicitly select `preset-vaapi` for hardware decode. VAAPI will decode and scale frames used by motion processing and live-view fallbacks. The render device and existing render/video groups remain available to the container.

Object detection remains disabled, so no detector process will be moved to OpenVINO in this change. The rollout will test the narrow `PERFMON` capability for Intel GPU metrics. The capability will remain only if it makes Frigate's GPU statistics work; otherwise it will be removed. Frigate will not be made privileged merely to expose GPU utilization statistics.

### Resource policy

The Frigate service will retain its two-CPU ceiling, 512 MiB shared-memory allocation, 768 PID ceiling, and no-container-swap policy.

The memory hard limit will increase from 2 GiB to 3 GiB, with a 1536 MiB reservation and a 3 GiB memory-plus-swap limit. This preserves host protection while adding room above the approximately 1.1-1.3 GiB post-enrichment steady state for reconnect and capture-process spikes. Fresh post-change measurements must confirm that ordinary use remains comfortably below the new ceiling.

## Recording freshness watchdog

A host-level systemd timer will check recording freshness every 30 seconds. The check is independent of Frigate's Docker health status and evaluates each configured camera separately.

For each camera, the watchdog will:

1. Find its newest non-empty recording segment on the recordings filesystem.
2. Treat the camera as healthy when that segment is no more than 90 seconds old.
3. On the first stale result, wait for one confirmation interval to avoid reacting to a filesystem timing race.
4. If the same camera remains stale, take a diagnostic snapshot to journald, restart only the Frigate service, and wait for container health.
5. Confirm that both cameras resume creating new segments and that the new segments pass `ffprobe`.
6. Publish a clear success or failure result to journald.

The watchdog will use a lock to prevent overlapping runs and a ten-minute restart cooldown to prevent a disconnected camera from repeatedly interrupting the healthy camera. A stale camera during cooldown remains a visible failure in the watchdog service status and journal rather than causing a restart loop.

The watchdog script and unit templates will live under `frigate/` in the repository. Installed systemd files and runtime state will contain no credentials.

## Failure handling

- A dead camera capture process with a healthy container is detected through stale recording timestamps and triggers one bounded recovery attempt.
- A camera outage does not cause rapid whole-container restart loops.
- A failed restart, unhealthy Frigate API, invalid segment, full filesystem, read-only filesystem, or missing recording directory produces a failed watchdog result in journald.
- The existing `restart: unless-stopped` policy continues to recover whole-container exits.
- Configuration backups are created before edits. Rollback restores the Frigate YAML and Compose backups, recreates only Frigate, and disables/removes the recording watchdog units.
- The current Couch View outage must be recovered during rollout before the change can be accepted.

## Rollout

1. Back up the credential-bearing Frigate configuration and Compose file with timestamps and restrictive permissions.
2. Capture pre-change recording freshness, resource, cgroup OOM, stream, and filesystem evidence.
3. Test local go2rtc video/audio stream copy for both cameras without altering the running recorder.
4. Validate the proposed Frigate YAML with Frigate's built-in validator and validate Compose before restart.
5. Recreate only Frigate once.
6. Confirm both cameras create new native-quality segments.
7. Install and start the watchdog service and timer.
8. Exercise the watchdog with a non-destructive test mode and a simulated stale fixture; do not intentionally interrupt a live camera merely to test failure handling.
9. Observe recording freshness, memory, CPU, PIDs, OOM counters, logs, and related host services after startup.

## Acceptance criteria

- Both cameras produce non-empty recording segments no more than 90 seconds old.
- New recordings probe as 2560x1920 H.264 at the camera's native average frame rate.
- Video is stream-copied rather than re-encoded.
- Audio is present and valid; passthrough is used only if it passes the timestamp test.
- Frigate's effective configuration reports VAAPI hardware acceleration and object detection disabled.
- Frigate reads both cameras from local go2rtc restream URLs.
- The camera-side main stream remains unchanged.
- Docker reports a 3 GiB memory limit, 1536 MiB reservation, 3 GiB memory-plus-swap limit, two CPUs, 768 PIDs, and 512 MiB shared memory.
- No new cgroup OOM or OOM-kill events occur during the observation window.
- The watchdog passes against live recordings and passes its simulated-stale behavior test.
- Home Assistant, MQTT, reverse-proxy access, and live view remain available.
- The 2 TiB recording filesystem is writable and has sufficient space for seven-day retention.

## Documentation and security

Record the final architecture, resource values, watchdog locations, rollback procedure, and measured verification results in `Homelab/Memory/Frigate.md` in the mounted Obsidian vault. Do not record camera URLs, credentials, tokens, private environment values, or raw logs.

Commit only secret-free repository files. The ignored live Frigate configuration and its backups remain uncommitted.
