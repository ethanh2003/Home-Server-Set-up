# Gemini Context: Homelab Architecture & Docker Stacks

**Role:** Expert System Context for Homelab Administration.
**Hardware Target:** Beelink Mini S13 Pro (Intel N150 4C/4T, 16GB RAM) + USB Storage Array.
**Network Edge:** GL.iNet Flint 2 (OpenWrt) + Cloudflare Tunnels.

## 1. Operational Authority & Control

* **Management Interface:** CLI-first. Portainer is deprecated; do not suggest it.
* **Script Authority:** The `manage-stacks.sh` script is the **Single Source of Truth** for orchestration.
    * `./manage-stacks.sh start`: Verifies `proxy_net`, mounts, and brings up stacks.
    * `./manage-stacks.sh pull`: Orchestrates image updates (watch for breaking changes in `*arr` apps).
* **Direct Control:** `docker compose` commands are valid but must observe network dependencies.

## 2. Storage & Filesystem Strategy (CRITICAL)

**Core Rule: Separation of State and Data.**

### A. Mount Topology
* **OS/Configs (Fast/Hot):** `/dev/nvme0n1` -> Mounted at `/`.
    * **Usage:** Docker Configs, Databases (SQLite/Postgres), OS Logs.
    * **Path:** `/home/ethan/docker/{service_name}_config`
* **Mass Storage (Warm/Hot):** 14TB Enterprise Recertified (Ext4).
    * **Usage:** Media Libraries (Plex/Jellyfin), Nextcloud Data.
    * **Mount Point:** `/mnt/data_14tb` (MUST be mounted via UUID in `/etc/fstab` to prevent enumeration drift).
    * **Warning:** Do not place active Databases here (high latency/USB overhead).
* **Cold Storage (Archive):** 5TB Seagate (Ext4, SMR).
    * **Usage:** Local Backups, Archives.
    * **Mount Point:** `/mnt/backup_5tb`
    * **Constraint:** Write-intensive tasks will stall this drive (SMR limitation). Sequential writes only.

### B. Persistence Standards
* **Bind Mounts Only:** Do not use Docker Volumes. Use host bind mounts for portability.
* **Permissions:** All containers must run as PUID:PGID `1000:1000` (User: `ethan`) to prevent permission locks on `ext4` USB drives.

## 3. Network Architecture

### A. Internal Traffic (`proxy_net`)
* **Subnet Isolation:** All web-accessible services attach to the external bridge `proxy_net`.
* **Reverse Proxy:** Nginx Proxy Manager (NPM) terminates internal SSL and routes local traffic.

### B. External Ingress (Zero Trust)
* **No Port Forwarding:** The GL-MT6000 Router must have **zero** inbound ports open (exception: WireGuard if strictly necessary, otherwise use Tunnels).
* **Cloudflare Tunnel (`cloudflared`):**
    * Handles all WAN ingress.
    * Bypasses CGNAT.
    * Enforces Cloudflare Access policies (MFA/Geo-blocking) before traffic hits the N150.

### C. DNS & Filtering
* **AdGuard Home:** Upstream DNS for the Docker host.
* **Telemetry:** Ensure AdGuard blocks telemetry domains for the N150 to reduce background noise.

## 4. Compute Constraints (Intel N150)

### A. Hardware Acceleration (QuickSync)
* **Capabilities:** The N150 (Alder Lake-N) supports AV1 decode and HEVC encode.
* **Implementation:**
    * **Plex/Jellyfin/Frigate:** MUST map `/dev/dri:/dev/dri`.
    * **Environment:** Ensure `LIBVA_DRIVER_NAME=i965` or `iHD` is set correctly in compose (usually `iHD` for Gen12+).

### B. Resource Management
* **The Bottleneck:** CPU is the primary constraint; RAM (16GB) is secondary but finite.
* **Limits:** `deploy.resources.limits` are mandatory for Java apps (Minecraft/Jenkins) and heavy DBs (Immich's Postgres).
    * *Example Limit:* `cpus: '2.0'`, `memory: 4G` for heavy containers.
* **AI/ML:** Use OpenVINO for Immich machine learning to offload CPU cycles to the iGPU.

## 5. Directory Map & Stack Logic

* **`arr-suite/`**:
    * **Gateway:** `gluetun` (VPN).
    * **Dependency:** `qbittorrent`, `prowlarr`, `flaresolverr` use `network_mode: service:gluetun`.
    * **Healthcheck:** If `gluetun` fails, the killswitch engages; dependent containers become unreachable.
* **`immich/`**:
    * **Heavy IO:** Requires the NVMe for the database/metadata. Only the `upload_location` maps to `/mnt/data_14tb`.
    * **Redis:** Uses `valkey` (compatible fork).
* **`nginx-proxy-manager/`**: Internal routing only.
* **`cloudflared/`**: The "Public Face". Authentication/Ingress.

## 6. Disaster Recovery & Troubleshooting

* **USB Failure:** If `/mnt/data_14tb` drops, Docker will hang.
    * *Action:* `docker compose down`, unmount/remount, verify UUID, `docker compose up -d`.
* **Database Corruption:** Check `/home/ethan/docker` backups on `/mnt/backup_5tb`.
* **Thermal Throttling:** N150 is fan-cooled but compact. Monitor `glances` for temperature spikes >75°C during transcoding.