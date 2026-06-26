# STACKS_README.md

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

# Docker Compose Stacks

`/home/ethan/docker` is the homelab infrastructure-as-code root. Each active
service or service group should live in one stack directory with a Compose file,
tracked documentation, and SOPS-managed secrets when needed.

## Source of Truth

- Compose and docs: Git.
- Secret values: SOPS-encrypted `.env.sops` or `*.sops.env`.
- Runtime state: ignored bind mounts, databases, config directories, logs, and
  app data.
- Wiki UI: generated from Git by `./scripts/wiki-sync.sh`.

Plain `.env` files are runtime artifacts and must not be committed.

## Active Stack Inventory

| Stack | Purpose | IaC notes |
| --- | --- | --- |
| `Minecraft/` | Minecraft server | SOPS env present. |
| `actual-budget/` | Actual Budget and sync helper | SOPS env present. |
| `arr-suite/` | Gluetun, qBittorrent, Prowlarr, Radarr, Sonarr | Preserve VPN routing through `gluetun`. |
| `cloudflared/` | Cloudflare Tunnel public ingress | SOPS env present; NPM may still be live during transition. |
| `github-runner/` | Self-hosted GitHub Actions runner | Privileged Docker socket access. |
| `glances/` | System monitoring | No secrets expected. |
| `home-assistant/` | Home Assistant, Mosquitto, Ring MQTT, Matter | Has dedicated docs and backup scripts. |
| `immich/` | Immich photos | SOPS env present; keep DB on fast local storage. |
| `jellyfin/` | Jellyfin and Jellyseerr | SOPS env present. |
| `kopia/` | Backups | SOPS env present. |
| `linkstack/` | LinkStack profile site | Uses `compose.yml`; still needs full IaC normalization. |
| `monitoring-stack/` | Prometheus, Grafana, Loki, Promtail, exporters | SOPS env present. |
| `nginx-proxy-manager/` | Legacy reverse proxy | Retain as rollback until Traefik cutover is complete. |
| `obsidian-livesync/` | CouchDB for Obsidian LiveSync | SOPS env present. |
| `paperless-ngx/` | Paperless-ngx document management | Uses shared SMTP relay. |
| `pingvin-share/` | File sharing | UI-managed app settings; needs SOPS review. |
| `sftp/` | FTP/SFTP access | SOPS env present. |
| `smtp-relay/` | Docker-local outbound SMTP relay | Google Workspace relay must allow host IP. |
| `spotify-stats/` | Your Spotify stats | SOPS env present. |
| `stash/` | Stash media library | Needs SOPS/docs review. |
| `traefik/` | Target-state IaC reverse proxy | Runs in parallel until cutover. |
| `wiki/` | Wiki.js documentation UI | Git-to-wiki sync and optional MCP integration. |

## Common Commands

```bash
./scripts/secrets-decrypt.sh
./scripts/iac-validate.sh
./scripts/wiki-sync.sh --check
./scripts/wiki-sync.sh --backfill
```

For a single stack:

```bash
./scripts/secrets-decrypt.sh --stack wiki
./scripts/wiki-sync.sh --stack wiki
cd wiki
docker compose config
docker compose up -d
```

## Wiki Documentation

The Wiki.js stack renders the Git-tracked docs under:

- `wiki.ethan-herring.com`
- `wiki.pup-percy.com`
- `wiki.ethanh.online`

Generated wiki source lives in `wiki/content/`. Manual edits in Wiki.js are not
authoritative; persistent changes should be made in Git and republished.
