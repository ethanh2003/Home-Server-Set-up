# 2026-07-09T14-56-22-DDcv-obsidian_web_resource_limits

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f4761-3bf7-7081-a4bd-b67d714c286b
updated_at: 2026-07-09T15:17:43+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/09/rollout-2026-07-09T14-56-22-019f4761-3bf7-7081-a4bd-b67d714c286b.jsonl
cwd: /home/ethan

# Added resource limits to the existing Obsidian web stack

Rollout context: The existing LAN/VPN-only browser Obsidian stack at `/home/ethan/docker/obsidian-web` was already running against `/data/Obsidian/Main` behind Nginx Proxy Manager on `obsidian-web.ethanh.online`, with the separate always-on `/home/ethan/obsidian-api-mcp` daemon still serving REST/MCP on `0.0.0.0:27124`. The user then asked to add resource limits to the web stack.

## Task 1: Add container resource limits to `obsidian-web`

Outcome: success

Preference signals:
- The user asked, simply, "can you add resource limits to it" -> future updates to this stack should default to adding explicit Docker limits rather than leaving the GUI container uncapped.
- The request came after a live service was already running -> future edits should be conservative, modify only the targeted stack, and verify the running container after recreation.

Key steps:
- Read the current compose file and measured live usage with `docker stats`; the GUI session was using roughly 715–841 MiB RAM and about 132–137 PIDs during verification.
- Chose conservative limits that would still leave the Electron GUI usable: `cpus: "2.0"`, `mem_limit: "3g"`, `memswap_limit: "4g"`, and `pids_limit: 512`.
- Updated `/home/ethan/docker/obsidian-web/docker-compose.yml` and documented the limits in `/home/ethan/docker/obsidian-web/README.md`.
- Recreated the container and verified Docker actually applied the limits via `docker inspect` and `docker stats`.

Failures and how to do differently:
- `docker compose config` expands the new resource fields into numeric byte values, so the human-readable source of truth is the compose file, not the expanded output.
- The local `.env` for this stack has a shell-sensitive non-secret value; the previous run already fixed that to `TITLE=Obsidian_Web`, so future edits should preserve that shell-safe form if the env file is re-sourced in shell commands.

Reusable knowledge:
- The container is `obsidian-web`, image `lscr.io/linuxserver/obsidian:latest`, and it remains healthy after the limit change.
- The service is still reachable through NPM at `https://obsidian-web.ethanh.online/` with basic auth; unauthenticated access still returns `401`.
- Verified host config after recreation: `NanoCpus=2000000000`, `Memory=3221225472`, `MemorySwap=4294967296`, `PidsLimit=512`, `ShmSize=1073741824`.
- Live resource usage at verification time was about `841.2MiB / 3GiB` and `pids=132`, so the chosen cap had headroom.

References:
- [1] Updated files: `/home/ethan/docker/obsidian-web/docker-compose.yml`, `/home/ethan/docker/obsidian-web/README.md`
- [2] Applied compose snippet: `cpus: "2.0"`, `mem_limit: "3g"`, `memswap_limit: "4g"`, `pids_limit: 512`, `shm_size: "1gb"`
- [3] Verification: `docker inspect obsidian-web --format 'NanoCpus={{.HostConfig.NanoCpus}} Memory={{.HostConfig.Memory}} MemorySwap={{.HostConfig.MemorySwap}} PidsLimit={{.HostConfig.PidsLimit}} ShmSize={{.HostConfig.ShmSize}}'` -> `NanoCpus=2000000000 Memory=3221225472 MemorySwap=4294967296 PidsLimit=512 ShmSize=1073741824`
- [4] Verification: `docker stats obsidian-web --no-stream` -> about `mem=841.2MiB / 3GiB`, `pids=132`
- [5] Verification: `https_auth:200` and `https_no_auth:401` after recreating the container
