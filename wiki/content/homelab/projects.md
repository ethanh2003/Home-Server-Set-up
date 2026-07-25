# Homelab Project Status

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


Last verified: 2026-07-04

## Status Model

- Runtime: `running`, `partial`, `stopped`, `unknown`, or `non-runtime`.
- Project status: `operational`, `in progress`, `needs IaC cleanup`, `needs docs`, `blocked`, or `archived`.
- Remaining tasks are concrete next actions, not placeholders.

## Projects

| Project | Kind | Runtime | Project status | Path |
| --- | --- | --- | --- | --- |
| [actual-budget](/homelab/stacks/actual-budget) | stack | running | needs docs | `/home/ethan/docker/actual-budget` |
| [arr-suite](/homelab/stacks/arr-suite) | stack | partial | in progress | `/home/ethan/docker/arr-suite` |
| [cloudflared](/homelab/stacks/cloudflared) | stack | running | needs docs | `/home/ethan/docker/cloudflared` |
| [dawarich](/homelab/stacks/dawarich) | stack | running | operational | `/home/ethan/docker/dawarich` |
| [dockhand](/homelab/stacks/dockhand) | stack | stopped | in progress | `/home/ethan/docker/dockhand` |
| [ebooks](/homelab/stacks/ebooks) | stack | running | in progress | `/home/ethan/docker/ebooks` |
| [frigate](/homelab/stacks/frigate) | stack | running | needs docs | `/home/ethan/docker/frigate` |
| [github-runner](/homelab/stacks/github-runner) | stack | running | needs docs | `/home/ethan/docker/github-runner` |
| [glances](/homelab/stacks/glances) | stack | running | needs docs | `/home/ethan/docker/glances` |
| [home-assistant](/homelab/stacks/home-assistant) | stack | running | operational | `/home/ethan/docker/home-assistant` |
| [immich](/homelab/stacks/immich) | stack | running | needs docs | `/home/ethan/docker/immich` |
| [jellyfin](/homelab/stacks/jellyfin) | stack | running | needs docs | `/home/ethan/docker/jellyfin` |
| [kopia](/homelab/stacks/kopia) | stack | running | needs docs | `/home/ethan/docker/kopia` |
| [linkstack](/homelab/stacks/linkstack) | stack | running | needs docs | `/home/ethan/docker/linkstack` |
| [Minecraft](/homelab/stacks/Minecraft) | stack | running | needs docs | `/home/ethan/docker/Minecraft` |
| [monitoring-stack](/homelab/stacks/monitoring-stack) | stack | running | needs docs | `/home/ethan/docker/monitoring-stack` |
| [nginx-proxy-manager](/homelab/stacks/nginx-proxy-manager) | stack | running | needs docs | `/home/ethan/docker/nginx-proxy-manager` |
| [obsidian-livesync](/homelab/stacks/obsidian-livesync) | stack | running | needs docs | `/home/ethan/docker/obsidian-livesync` |
| [obsidian-web](/homelab/stacks/obsidian-web) | stack | stopped | in progress | `/home/ethan/docker/obsidian-web` |
| [paperless-ngx](/homelab/stacks/paperless-ngx) | stack | running | operational | `/home/ethan/docker/paperless-ngx` |
| [pingvin-share](/homelab/stacks/pingvin-share) | stack | running | operational | `/home/ethan/docker/pingvin-share` |
| [portainer](/homelab/stacks/portainer) | stack | running | needs docs | `/home/ethan/docker/portainer` |
| [sftp](/homelab/stacks/sftp) | stack | running | needs docs | `/home/ethan/docker/sftp` |
| [smtp-relay](/homelab/stacks/smtp-relay) | stack | running | operational | `/home/ethan/docker/smtp-relay` |
| [spotify-stats](/homelab/stacks/spotify-stats) | stack | running | in progress | `/home/ethan/docker/spotify-stats` |
| [stash](/homelab/stacks/stash) | stack | running | needs docs | `/home/ethan/docker/stash` |
| [timemachine](/homelab/stacks/timemachine) | stack | running | operational | `/home/ethan/docker/timemachine` |
| [traefik](/homelab/stacks/traefik) | stack | running | in progress | `/home/ethan/docker/traefik` |
| [vault-inbox](/homelab/stacks/vault-inbox) | stack | running | operational | `/home/ethan/docker/vault-inbox` |
| [wiki](/homelab/stacks/wiki) | stack | running | operational | `/home/ethan/docker/wiki` |
| arr-multi-user | adjacent repo | non-runtime | in progress | `/home/ethan/arr-multi-user` |
| chicago-dashboard | adjacent repo | non-runtime | in progress | `/home/ethan/chicago-dashboard` |
| dymo-label | adjacent app | unknown | blocked | `/home/ethan/dymo-label` |
| obsidian-api-mcp | adjacent repo | non-runtime | operational | `/home/ethan/obsidian-api-mcp` |

## Remaining Task Index

### actual-budget

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### arr-suite

- Runtime: partial
- Project status: in progress
- Keep dry-run-first acquisition workflows and approval artifacts for bulk Radarr changes.
- Continue live queue verification before any Jellyfin collection or cleanup work.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.
- Inspect `docker compose ps` and service logs before marking the runtime operational.

### cloudflared

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### dawarich

- Runtime: running
- Project status: operational
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### dockhand

- Runtime: stopped
- Project status: in progress
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.
- Inspect `docker compose ps` and service logs before marking the runtime operational.

### ebooks

- Runtime: running
- Project status: in progress
- Finish first-run application configuration in Calibre-Web Automated and LazyLibrarian.
- Verify StoryGraph watcher behavior after adding a real export CSV.
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### frigate

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### github-runner

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### glances

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### home-assistant

- Runtime: running
- Project status: operational
- Keep backup, validation, deploy, restart, logs, and rollback helper docs aligned with the live scripts.
- Maintain separate handling for the primary Home Assistant instance and `HomeAssistant2`.

### immich

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### jellyfin

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### kopia

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### linkstack

- Runtime: running
- Project status: needs docs
- Normalize the stack into the broader IaC model and document public hardening settings.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### Minecraft

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### monitoring-stack

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### nginx-proxy-manager

- Runtime: running
- Project status: needs docs
- Keep as rollback during Traefik migration.
- Reconcile generated proxy configs with the live SQLite database before disabling stale rows.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### obsidian-livesync

- Runtime: running
- Project status: needs docs
- Resolve the stale duplicate NPM row for `obsidian.ethan-herring.com` if it still exists.
- Keep LiveSync replication separate from the always-on Obsidian API/MCP service.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### obsidian-web

- Runtime: stopped
- Project status: in progress
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.
- Inspect `docker compose ps` and service logs before marking the runtime operational.

### paperless-ngx

- Runtime: running
- Project status: operational
- Keep routine image updates, backups, and documentation current.

### pingvin-share

- Runtime: running
- Project status: operational
- Review whether Pingvin settings should stay UI-managed or gain tracked documentation for each production setting.

### portainer

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### sftp

- Runtime: running
- Project status: needs docs
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### smtp-relay

- Runtime: running
- Project status: operational
- Keep routine image updates, backups, and documentation current.

### spotify-stats

- Runtime: running
- Project status: in progress
- Finish hardening large Your Spotify imports beyond the current cache and `/tmp/imports` fixes.
- Decide whether the upstream checkout changes should become a local patch, fork, or discardable hotfix.

### stash

- Runtime: running
- Project status: needs docs
- Add a stack README covering media roots, backups, scan behavior, and qBittorrent seeding constraints.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### timemachine

- Runtime: running
- Project status: operational
- If remote Macs cannot route to `192.168.1.230`, advertise and approve a Tailscale route for `192.168.1.230/32`.
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### traefik

- Runtime: running
- Project status: in progress
- Complete Cloudflare cutover from NPM to Traefik after route parity is verified.
- Keep NPM available as rollback until public ingress has been proven off-LAN.
- Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.

### vault-inbox

- Runtime: running
- Project status: operational
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

### wiki

- Runtime: running
- Project status: operational
- Keep routine image updates, backups, and documentation current.

### arr-multi-user

- Runtime: non-runtime
- Project status: in progress
- Create the initial repository commit once the current scaffold and submodule state are reviewed.
- Finish the companion-app plan set and re-run the repository contract tests.

### chicago-dashboard

- Runtime: non-runtime
- Project status: in progress
- Implement the remaining CTA, weather, calendar, ETA, preferences, and cross-plan consistency plans.
- Review the local server/package changes and decide what belongs in Git.

### dymo-label

- Runtime: unknown
- Project status: blocked
- Initialize source control or explicitly document why the app remains outside Git.
- Restore or recreate `frontend/src/stores/appStore`, `frontend/src/components/Login`, and `frontend/src/components/Editor` so the frontend build can compile.

### obsidian-api-mcp

- Runtime: non-runtime
- Project status: operational
- Keep the user systemd service and bearer-token setup documented with the Obsidian vault notes.
- Do not treat this service as the LiveSync replication engine.
