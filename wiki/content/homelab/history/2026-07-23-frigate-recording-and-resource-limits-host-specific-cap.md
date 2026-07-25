# 2026-07-23T19-51-21-3Pyk-frigate_recording_and_resource_limits_host_specific_cap

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f9088-54a4-78a1-865e-f7fda3df2aa4
updated_at: 2026-07-23T21:34:47+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/23/rollout-2026-07-23T19-51-21-019f9088-54a4-78a1-865e-f7fda3df2aa4.jsonl
cwd: /home/ethan

# Frigate resource sizing was tuned on the live homelab host and capped with Docker limits after the user asked to leave headroom for other stacks.

Rollout context: The user first reported that Frigate continuous recording was not enabled, then asked to cap continuous recording at 1–2 TB, then asked whether the 960x720 stream was a bug because it should be 5 MP, and finally asked for proper resource limits based on the specific setup while leaving enough for other important stacks. The work happened in `/home/ethan` with the live Frigate stack under `/home/ethan/docker/frigate`. The Frigate camera config contained plaintext RTSP credentials, so it was treated as secret-bearing and not committed.

## Task 1: Fix Frigate recording, cap storage, verify 5 MP recordings, and apply host-specific resource limits

Outcome: success

Preference signals:
- The user asked for limits "based on my specific setup" and "allowing frigate what it needs while leaving enough for my other important stacks" -> future Frigate sizing should be measurement-driven against the live host, not a generic preset.
- When the user said "Also you can cut the search and face detection off" -> future memory budgeting for this stack should default to disabling Frigate semantic search and face recognition when the goal is to preserve host headroom.
- When the user questioned "Why is it only 960x720? It should be 5mp" -> future agents should verify actual recorded resolution separately from detection-frame settings before changing camera configuration.
- The user’s follow-up "Apply it" after approving the design -> once the design is accepted, proceed directly to implementation rather than re-litigating the options.

Key steps:
- Verified that Frigate was healthy but recording was disabled in the effective config; logs showed `Recordings must be enabled in the config to be turned on via MQTT.`
- Added `record.enabled: true` with `continuous.days: 7`, then created a dedicated 2 TiB ext4 loop filesystem mounted at `/mnt/data_14tb/media/frigate/recordings` and persisted it in `/etc/fstab` so recordings could not consume the rest of the 14 TB disk.
- Confirmed via `ffprobe` that saved recordings were actually `2560x1920` H.264 at roughly 5 Mbps, while the `960x720 @ 5 FPS` setting only applied to the detection feed.
- Measured the live host before sizing: Intel N150, 4 cores, 15 GiB RAM, 4 GiB swap, with the host already memory-pressured and swap-full.
- Measured Frigate’s live load before changes: roughly 2.07 GiB RAM average, 2.27 GiB peak, ~37% CPU average, and 455 PIDs, with semantic search and face recognition consuming about 960 MiB.
- After the user approved disabling search/face, applied Docker limits to Frigate: `cpus: "2.0"`, `mem_limit: "2g"`, `mem_reservation: "1g"`, `memswap_limit: "2g"`, `pids_limit: 768`, `shm_size: "512mb"`.
- Recreated only Frigate, verified health, verified the runtime cgroup values, verified the effective API config, and confirmed fresh recordings still landed at 2560x1920.
- Updated `/data/Obsidian/Main/Homelab/Memory/Frigate.md` with the durable before/after measurements, the 2 TiB recordings filesystem, and the rollback backups.

Failures and how to do differently:
- The first log scan for post-change errors falsely matched the word `room` inside camera names because it contained the substring `oom`; future scans should use exact error patterns or anchored regexes.
- The live Frigate config output contained plaintext camera credentials; do not commit `config/config.yml`, do not paste it into durable notes, and consider rotating the camera password.
- The secret-bearing Frigate config file is ignored by git in this repo, so repository commits should only include the secret-free Compose file and documentation/plan artifacts.

Reusable knowledge:
- Frigate records the main stream unchanged; the `960x720` setting in this setup was the detector feed, not the stored recording resolution.
- The live recording filesystem can be hard-capped cleanly with a dedicated loop-mounted ext4 image mounted at Frigate’s recordings directory.
- On this host, the effective post-change Frigate footprint settled at about 1.19 GiB RAM, ~34.5% of one CPU average, and 340 PIDs, leaving materially more host memory available afterward.
- Runtime verification that mattered: `docker inspect` for cgroup values, `docker exec frigate python3 -m frigate --validate-config`, `/api/config`, `memory.events`, `docker stats --no-stream`, and `ffprobe` on the newest `.mp4` files.

References:
- [1] Frigate config validation output: `Your config file is valid.`
- [2] Runtime limits verified after recreation: `NanoCpus=2000000000 Memory=2147483648 MemoryReservation=1073741824 MemorySwap=2147483648 PidsLimit=768 ShmSize=536870912`
- [3] Effective API verification: semantic search and face recognition disabled, recording enabled, continuous retention 7 days.
- [4] Fresh recording probe: both cameras produced `2560x1920` H.264 MP4 segments after the change.
- [5] Commit for the scoped change: `8adbb2c ops: bound Frigate resource usage`
- [6] Durable note updated at `/data/Obsidian/Main/Homelab/Memory/Frigate.md` with the measured before/after resource usage and rollback backups.
