# Docker Compose Stacks

This directory contains the Docker Compose configurations for the home server infrastructure, migrated from Portainer.

## Structure

Each service or logical group of services has its own directory:

- **actual-budget/**: Actual Budget finance tool.
- **arr-suite/**: The *Arr stack (Sonarr, Radarr, Lidarr, Prowlarr, Whisparr) + Gluetun VPN + qBittorrent + AutoBrr + Flaresolverr.
- **cloudflared/**: Cloudflare Tunnel.
- **glances/**: System monitoring tool.
- **home-assistant/**: Home Assistant, Mosquitto, and Ring-MQTT.
- **homepage/**: The dashboard service.
- **immich/**: Immich Photos server.
- **immich-ml/**: Immich Machine Learning worker.
- **jellyfin/**: Jellyfin media server and Jellyseerr.
- **kopia/**: Kopia backup server.
- **matter-server/**: Matter (IoT) server.
- **minecraft/**: Minecraft Paper server.
- **monitoring/**: Uptime Kuma, Ntfy, and Diun.
- **nginx-proxy-manager/**: Reverse proxy.
- **nextcloud/**: Nextcloud AIO.
- **stash-komga/**: Stash (adult media) and Komga (comics).
- **tube-archivist/**: YouTube archiving stack.

## Usage

To start a stack, navigate to its directory and run:

```bash
docker compose up -d
```

To stop a stack:

```bash
docker compose down
```

## Environment Variables

Each stack may require a `.env` file. 
**Note:** `.env` files contain sensitive secrets and are **ignored by git**. 
Make sure to back them up separately or use a secrets manager.

## Migration Notes

These files were migrated from Portainer's internal storage (`@docker/portainer_data/compose/*`). 
The `stack.env` files from Portainer have been converted to standard `.env` files.
