# Frigate Resource Limits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bound Frigate's CPU, memory, swap, and process usage while preserving native 5 MP recording and person detection on the four-core, 15 GiB host.

**Architecture:** Explicitly disable the optional embeddings workloads in Frigate's YAML, then apply Docker Compose cgroup limits sized from live measurements. Recreate only Frigate and verify both the effective application configuration and the kernel-applied cgroup values before accepting the change.

**Tech Stack:** Frigate 0.17.2, Docker Compose, cgroup v2, YAML, ffprobe, Frigate HTTP API

## Global Constraints

- Preserve both cameras' native 2560x1920 H.264 recordings.
- Preserve person detection at 960x720 and 5 FPS.
- Preserve seven-day retention and the dedicated 2 TiB recordings filesystem.
- Preserve VAAPI decoding, audio recording, live view, MQTT, and existing camera access.
- Disable semantic search and face recognition.
- Apply exactly 2 CPUs, 2 GiB memory, 1 GiB reservation, 2 GiB memory-plus-swap, 768 PIDs, and 512 MiB shared memory.
- Recreate only the Frigate service.
- Preserve unrelated worktree changes and never commit secrets or generated Frigate state.

---

### Task 1: Apply and verify the Frigate resource policy

**Files:**
- Modify: `frigate/config/config.yml`
- Modify: `frigate/docker-compose.yml`
- Modify: `/data/Obsidian/Main/Homelab/Memory/Frigate.md`

**Interfaces:**
- Consumes: the existing `frigate` Compose service, Frigate's `/api/config` and `/api/stats` endpoints, and recorded MP4 segments under `/media/frigate/recordings`
- Produces: explicit disabled enrichment settings and Docker runtime limits visible through `docker inspect` and cgroup v2

- [ ] **Step 1: Back up both live configuration files**

Run:

```bash
cp --preserve=mode,timestamps frigate/config/config.yml frigate/config/config.yml.codex-bak-20260723-resource-limits
cp --preserve=mode,timestamps frigate/docker-compose.yml frigate/docker-compose.yml.codex-bak-20260723-resource-limits
```

Expected: both backup files exist and match their source files byte-for-byte.

- [ ] **Step 2: Run the policy test and verify it fails**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import yaml

root = Path("/home/ethan/docker/frigate")
app = yaml.safe_load((root / "config/config.yml").read_text())
compose = yaml.safe_load((root / "docker-compose.yml").read_text())
service = compose["services"]["frigate"]

assert app["semantic_search"]["enabled"] is False
assert app["face_recognition"]["enabled"] is False
assert service["cpus"] == "2.0"
assert service["mem_limit"] == "2g"
assert service["mem_reservation"] == "1g"
assert service["memswap_limit"] == "2g"
assert service["pids_limit"] == 768
assert service["shm_size"] == "512mb"
PY
```

Expected: FAIL because enrichment features are enabled and the resource keys do not exist.

- [ ] **Step 3: Apply the minimal application and Compose changes**

Set these top-level Frigate values:

```yaml
semantic_search:
  enabled: false
  model_size: small
face_recognition:
  enabled: false
  model_size: small
```

Add these values to the `frigate` Compose service next to `shm_size`:

```yaml
    cpus: "2.0"
    mem_limit: "2g"
    mem_reservation: "1g"
    memswap_limit: "2g"
    pids_limit: 768
```

- [ ] **Step 4: Run the policy test and verify it passes**

Run the exact Python assertion from Step 2.

Expected: exit code 0 with no assertion failure.

- [ ] **Step 5: Validate both configurations**

Run:

```bash
docker compose -f /home/ethan/docker/frigate/docker-compose.yml config -q
docker exec frigate python3 -m frigate --validate-config
```

Expected: Compose exits 0 and Frigate prints `Your config file is valid`.

- [ ] **Step 6: Recreate only Frigate and wait for health**

Run:

```bash
docker compose -f /home/ethan/docker/frigate/docker-compose.yml up -d --force-recreate --no-deps frigate
```

Poll `docker inspect frigate --format '{{.State.Health.Status}}'` for up to 90 seconds.

Expected: `healthy`.

- [ ] **Step 7: Verify effective configuration and runtime cgroups**

Assert through `/api/config` that semantic search and face recognition are disabled. Assert through `docker inspect`:

```text
NanoCpus=2000000000
Memory=2147483648
MemoryReservation=1073741824
MemorySwap=2147483648
PidsLimit=768
ShmSize=536870912
```

Read `/sys/fs/cgroup/memory.events` inside Frigate.

Expected: `oom 0`, `oom_kill 0`, and `oom_group_kill 0`.

- [ ] **Step 8: Verify application behavior and headroom**

Probe the latest fresh MP4 for each camera with `/usr/lib/ffmpeg/7.0/bin/ffprobe`.

Expected for both cameras:

```text
width=2560
height=1920
```

Sample Frigate five times with `docker stats --no-stream`. Confirm memory remains below 2 GiB, PIDs remain below 768, and no recording, OOM, or no-space errors appear in logs. Confirm Frigate, Home Assistant, Minecraft, Jellyfin, Nginx Proxy Manager, Traefik, Cloudflare Tunnel, and Mosquitto remain running or healthy.

- [ ] **Step 9: Document and commit only scoped repository files**

Append the applied limits, disabled features, measured usage, runtime proof, and rollback paths to `/data/Obsidian/Main/Homelab/Memory/Frigate.md`.

Run:

```bash
git -C /home/ethan/docker add \
  frigate/config/config.yml \
  frigate/docker-compose.yml \
  frigate/docs/superpowers/plans/2026-07-23-frigate-resource-limits.md
git -C /home/ethan/docker diff --cached --check
git -C /home/ethan/docker commit -m "ops: bound Frigate resource usage"
```

Expected: the commit contains only the two Frigate configuration files and this plan. The Obsidian note is verified separately because it belongs to the mounted Windows vault.
