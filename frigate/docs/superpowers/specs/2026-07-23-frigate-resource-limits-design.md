# Frigate Resource Limits Design

## Goal

Keep Frigate reliable for two 2560x1920 continuous-recording cameras with person detection while preventing it from starving Home Assistant, Minecraft, Jellyfin, and the host's other services.

## Measured baseline

- Host: Intel N150, 4 physical CPU cores, 15 GiB RAM, 4 GiB swap.
- Host pressure during measurement: about 1.4 GiB RAM available and swap fully occupied.
- Frigate workload: two 2560x1920 H.264 main streams recorded without re-encoding at roughly 5 Mbps each.
- Detection workload: both streams scaled to 960x720 at 5 FPS, tracking `person`, using the CPU detector.
- Video decode: VAAPI on `/dev/dri/renderD128`.
- Frigate sampled CPU: 37% average and 67% maximum, where 100% is one CPU core.
- Frigate memory: about 2.07 GiB average and 2.27 GiB observed peak.
- Frigate process count: 455 current and 494 observed peak.
- Shared memory: about 100 MiB used, with Frigate reporting a 162 MiB minimum.
- The embeddings process used about 960 MiB because semantic search and face recognition were enabled.

## Approved feature scope

- Preserve continuous recording at the cameras' native 2560x1920 resolution.
- Preserve seven-day recording retention and the separate 2 TiB recordings filesystem.
- Preserve person detection at 960x720 and 5 FPS.
- Preserve VAAPI decoding, audio recording, live view, MQTT, and existing camera access.
- Disable semantic search.
- Disable face recognition.
- Do not change camera resolution, bitrate, frame rate, recording retention, detector type, or unrelated stacks.

## Resource policy

Apply these Docker Compose limits to the Frigate service:

- `cpus: "2.0"`: allows up to half of the four-core host. This is well above the measured sub-one-core load while preserving two cores for other stacks during a Frigate spike.
- `mem_limit: "2g"`: a hard ceiling chosen for the expected post-embeddings workload of roughly 1.1-1.3 GiB, leaving substantial startup and transient headroom.
- `mem_reservation: "1g"`: a soft pressure target below the expected steady-state footprint.
- `memswap_limit: "2g"`: equal to the memory limit, preventing Frigate from adding to the host's already exhausted swap.
- `pids_limit: 768`: about 55% above the observed peak of 494, enough for Frigate's process and thread model without leaving it unbounded.
- Keep `shm_size: "512mb"` unchanged: it is more than three times Frigate's reported minimum and currently has ample headroom.

## Failure behavior and rollback

- Docker throttles CPU above two cores rather than terminating Frigate.
- If Frigate reaches 2 GiB, the kernel may terminate a Frigate process or container instead of consuming memory needed by unrelated services. This condition must be treated as a failed sizing check, not as acceptable steady behavior.
- Verification must check Docker's memory event counters for `oom` and `oom_kill`, not only container health.
- Take timestamped backups of `config/config.yml` and `docker-compose.yml` before editing.
- Rollback restores both backups and recreates only the Frigate service.

## Validation

Before restart:

- Parse the YAML and assert both enrichment features are explicitly disabled.
- Run `docker compose config`.
- Run Frigate's built-in `python3 -m frigate --validate-config`.

After restart:

- Wait for the Frigate health check to report healthy.
- Confirm the effective API reports semantic search and face recognition disabled.
- Confirm `docker inspect` reports 2 CPUs, 2 GiB memory, 2 GiB memory-plus-swap, a 1 GiB reservation, 768 PIDs, and 512 MiB shared memory.
- Confirm the cgroup reports no OOM or OOM-kill events.
- Confirm both cameras produce fresh non-empty 2560x1920 MP4 segments.
- Sample CPU, memory, swap, and PID use after startup. Memory must remain below the 2 GiB ceiling, PIDs below 768, and recordings must continue without errors.
- Confirm Home Assistant, Minecraft, Jellyfin, Nginx Proxy Manager, Traefik, Cloudflare Tunnel, and Mosquitto remain running or healthy as applicable.

## Documentation

Append the applied limits, disabled features, measured post-change usage, verification results, and rollback paths to `Homelab/Memory/Frigate.md`. Do not record camera credentials or other secrets.
