# 2026-06-14T00-31-04-Inr4-home_assistant_homelab_setup_requirements

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019ec38a-0a6b-7b73-8cf9-6d256264717a
updated_at: 2026-06-14T00:31:39+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/14/rollout-2026-06-14T00-31-04-019ec38a-0a6b-7b73-8cf9-6d256264717a.jsonl
cwd: /home/ethan

# Home Assistant homelab setup requirements were specified in detail, but no implementation actions are shown in this rollout.

Rollout context: The user wants the agent to take charge of a personal Home Assistant homelab setup as code, using a practical and maintainable Docker Compose-based workflow on Linux, with strong safety constraints around backups, secrets, and non-destructive changes. The rollout content is primarily a long task specification rather than evidence of repo changes or validation.

## Task 1: Home Assistant repo discovery, setup, and documentation plan

Outcome: uncertain

Preference signals:
- The user explicitly asked for a "practical, working, maintainable setup, not a theoretical plan" -> future runs should bias toward concrete file changes, validation, and deployable structure rather than discussion-only output.
- The user said "Prefer Docker Compose unless the existing repo clearly uses another deployment method" -> default to Compose-based Home Assistant deployment when choosing architecture.
- The user said "Keep secrets out of Git" and "Use .example files for placeholders" -> future work should create example secret/env files and avoid touching real secrets.
- The user asked to "Make only reviewable changes" and "Do as much as possible in one run" -> future agents should batch safe edits, but keep them reviewable and avoid opaque large-scale rewrites.
- The user asked to "Do not overwrite existing Home Assistant config without making a timestamped backup first" and "Do not run docker compose down -v" / other destructive commands -> future agents should treat backups and non-destructive operations as hard defaults.
- The user requested explicit output sections (summary, files changed, commands run, deployment status, manual steps, risks, next tasks) -> future responses should preserve this reporting format unless the user says otherwise.

Key steps:
- The user defined a phased workflow: discovery of repo, existing HA containers/config/mounted paths/services, then plan, implementation, scripts, docs, optional services, and validation.
- The user requested safe scripts for backup, validation, deploy, restart, logs, and rollback, with deploy required to back up and validate before restart.
- The user requested conventions for readable YAML, clear aliases, package-based organization when useful, documented helper entities, placeholders/TODOs for unknown IDs, and no invented entity IDs.

Failures and how to do differently:
- No repo discovery or implementation evidence is present in the rollout, so this should be treated as a requirements capture rather than a completed setup.
- Future agents should not assume the Home Assistant install exists or is absent; the user explicitly wants discovery first.
- Future agents should not expose Home Assistant publicly, change firewall/router settings, or enable optional integrations by default without evidence they are already used.

Reusable knowledge:
- The target layout the user wants is explicit and should be used as the default structure when creating or normalizing the repo: `home-assistant/`, `docker/compose.home-assistant.yml`, `scripts/ha-*.sh`, and `docs/*.md` including runbook, entity map, automation standards, dashboard plan, and backup/restore docs.
- Optional integrations the user mentioned should remain optional and documented unless there is repo evidence that they are already in use: MQTT/Mosquitto, Zigbee2MQTT, Z-Wave JS UI, ESPHome, MariaDB, InfluxDB, Prometheus exporter, Grafana integration, Frigate.
- If Home Assistant already exists, the user wants a timestamped backup before edits, preservation of entity IDs and automations unless a clear bug is explained, and organization/documentation improvements rather than a rewrite.

References:
- [1] Safety constraints: "Do not delete Docker volumes", "Do not run `docker compose down -v`", "Do not run `docker system prune`, `docker volume prune`, or destructive cleanup commands".
- [2] Required scripts: `ha-backup.sh`, `ha-validate.sh`, `ha-deploy.sh`, `ha-restart.sh`, `ha-logs.sh`, `ha-rollback.sh`.
- [3] Required docs: `docs/home-assistant-runbook.md`, `docs/entity-map.md`, `docs/automation-standards.md`, `docs/dashboard-plan.md`, `docs/backup-and-restore.md`.
- [4] Final reporting requested: summary, files changed, commands run, deployment status, manual steps, risks/assumptions, next recommended tasks.
