# Homelab Project Status

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


Last verified: 2026-07-04

## Status Model

- Runtime: `not checked` in deterministic output; opt-in snapshots may report `running`, `partial`, `stopped`, `unknown`, or `non-runtime`.
- Project status: `operational`, `in progress`, `needs IaC cleanup`, `needs docs`, `blocked`, or `archived`.
- Remaining tasks are concrete next actions, not placeholders.

## Projects

| Project | Kind | Runtime | Project status | Path |
| --- | --- | --- | --- | --- |
| [actual-budget](/homelab/stacks/actual-budget) | stack | not checked | needs docs | `/home/ethan/docker/actual-budget` |
| [arr-suite](/homelab/stacks/arr-suite) | stack | not checked | needs docs | `/home/ethan/docker/arr-suite` |
| [cloudflared](/homelab/stacks/cloudflared) | stack | not checked | needs docs | `/home/ethan/docker/cloudflared` |
| [dawarich](/homelab/stacks/dawarich) | stack | not checked | operational | `/home/ethan/docker/dawarich` |
| [dockhand](/homelab/stacks/dockhand) | stack | not checked | needs docs | `/home/ethan/docker/dockhand` |
| [ebooks](/homelab/stacks/ebooks) | stack | not checked | in progress | `/home/ethan/docker/ebooks` |
| [frigate](/homelab/stacks/frigate) | stack | not checked | needs docs | `/home/ethan/docker/frigate` |
| [github-runner](/homelab/stacks/github-runner) | stack | not checked | needs docs | `/home/ethan/docker/github-runner` |
| [glances](/homelab/stacks/glances) | stack | not checked | needs docs | `/home/ethan/docker/glances` |
| [home-assistant](/homelab/stacks/home-assistant) | stack | not checked | operational | `/home/ethan/docker/home-assistant` |
| [immich](/homelab/stacks/immich) | stack | not checked | needs docs | `/home/ethan/docker/immich` |
| [jellyfin](/homelab/stacks/jellyfin) | stack | not checked | needs docs | `/home/ethan/docker/jellyfin` |
| [kopia](/homelab/stacks/kopia) | stack | not checked | needs docs | `/home/ethan/docker/kopia` |
| [linkstack](/homelab/stacks/linkstack) | stack | not checked | needs docs | `/home/ethan/docker/linkstack` |
| [Minecraft](/homelab/stacks/Minecraft) | stack | not checked | needs docs | `/home/ethan/docker/Minecraft` |
| [monitoring-stack](/homelab/stacks/monitoring-stack) | stack | not checked | needs docs | `/home/ethan/docker/monitoring-stack` |
| [nginx-proxy-manager](/homelab/stacks/nginx-proxy-manager) | stack | not checked | needs docs | `/home/ethan/docker/nginx-proxy-manager` |
| [obsidian-livesync](/homelab/stacks/obsidian-livesync) | stack | not checked | needs docs | `/home/ethan/docker/obsidian-livesync` |
| [obsidian-web](/homelab/stacks/obsidian-web) | stack | not checked | operational | `/home/ethan/docker/obsidian-web` |
| [paperless-ngx](/homelab/stacks/paperless-ngx) | stack | not checked | operational | `/home/ethan/docker/paperless-ngx` |
| [pingvin-share](/homelab/stacks/pingvin-share) | stack | not checked | operational | `/home/ethan/docker/pingvin-share` |
| [portainer](/homelab/stacks/portainer) | stack | not checked | needs docs | `/home/ethan/docker/portainer` |
| [sftp](/homelab/stacks/sftp) | stack | not checked | needs docs | `/home/ethan/docker/sftp` |
| [smtp-relay](/homelab/stacks/smtp-relay) | stack | not checked | operational | `/home/ethan/docker/smtp-relay` |
| [spotify-stats](/homelab/stacks/spotify-stats) | stack | not checked | in progress | `/home/ethan/docker/spotify-stats` |
| [stash](/homelab/stacks/stash) | stack | not checked | needs docs | `/home/ethan/docker/stash` |
| [timemachine](/homelab/stacks/timemachine) | stack | not checked | operational | `/home/ethan/docker/timemachine` |
| [traefik](/homelab/stacks/traefik) | stack | not checked | in progress | `/home/ethan/docker/traefik` |
| [vault-inbox](/homelab/stacks/vault-inbox) | stack | not checked | operational | `/home/ethan/docker/vault-inbox` |
| [wiki](/homelab/stacks/wiki) | stack | not checked | operational | `/home/ethan/docker/wiki` |

## Remaining Task Index

### actual-budget

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### arr-suite

- Runtime: not checked
- Project status: needs docs
- Keep dry-run-first acquisition workflows and approval artifacts for bulk Radarr changes.
- Continue live queue verification before any Jellyfin collection or cleanup work.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### cloudflared

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### dawarich

- Runtime: not checked
- Project status: operational
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### dockhand

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### ebooks

- Runtime: not checked
- Project status: in progress
- Finish first-run application configuration in Calibre-Web Automated and LazyLibrarian.
- Verify StoryGraph watcher behavior after adding a real export CSV.
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### frigate

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### github-runner

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### glances

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### home-assistant

- Runtime: not checked
- Project status: operational
- Keep backup, validation, deploy, restart, logs, and rollback helper docs aligned with the live scripts.
- Maintain separate handling for the primary Home Assistant instance and `HomeAssistant2`.

### immich

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### jellyfin

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### kopia

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### linkstack

- Runtime: not checked
- Project status: needs docs
- Normalize the stack into the broader IaC model and document public hardening settings.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### Minecraft

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### monitoring-stack

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### nginx-proxy-manager

- Runtime: not checked
- Project status: needs docs
- Keep as rollback during Traefik migration.
- Reconcile generated proxy configs with the live SQLite database before disabling stale rows.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### obsidian-livesync

- Runtime: not checked
- Project status: needs docs
- Resolve the stale duplicate NPM row for `obsidian.ethan-herring.com` if it still exists.
- Keep LiveSync replication separate from the always-on Obsidian API/MCP service.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### obsidian-web

- Runtime: not checked
- Project status: operational
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### paperless-ngx

- Runtime: not checked
- Project status: operational
- Keep routine image updates, backups, and documentation current.

### pingvin-share

- Runtime: not checked
- Project status: operational
- Review whether Pingvin settings should stay UI-managed or gain tracked documentation for each production setting.

### portainer

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### sftp

- Runtime: not checked
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### smtp-relay

- Runtime: not checked
- Project status: operational
- Keep routine image updates, backups, and documentation current.

### spotify-stats

- Runtime: not checked
- Project status: in progress
- Finish hardening large Your Spotify imports beyond the current cache and `/tmp/imports` fixes.
- Decide whether the upstream checkout changes should become a local patch, fork, or discardable hotfix.

### stash

- Runtime: not checked
- Project status: needs docs
- Add a stack README covering media roots, backups, scan behavior, and qBittorrent seeding constraints.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### timemachine

- Runtime: not checked
- Project status: operational
- If remote Macs cannot route to `192.168.1.230`, advertise and approve a Tailscale route for `192.168.1.230/32`.
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### traefik

- Runtime: not checked
- Project status: in progress
- Complete Cloudflare cutover from NPM to Traefik after route parity is verified.
- Keep NPM available as rollback until public ingress has been proven off-LAN.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### vault-inbox

- Runtime: not checked
- Project status: operational
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### wiki

- Runtime: not checked
- Project status: operational
- Keep routine image updates, backups, and documentation current.
