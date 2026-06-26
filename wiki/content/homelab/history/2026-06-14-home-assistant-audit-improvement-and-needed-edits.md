# 2026-06-14T00-31-54-Shbq-home_assistant_audit_improvement_and_needed_edits

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019ec38a-cf23-7bb3-a6fd-4c107425d288
updated_at: 2026-06-14T01:14:22+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/14/rollout-2026-06-14T00-31-54-019ec38a-cf23-7bb3-a6fd-4c107425d288.jsonl
cwd: /home/ethan

# Home Assistant audit/improvement work on an existing Docker Compose stack

Rollout context: The user asked multiple times to analyze the live Home Assistant setup, produce an audit/improvement plan, implement the needed edits, and then create an audit report. The work stayed rooted at `/home/ethan/docker/home-assistant` with the broader repo at `/home/ethan/docker`. The stack already existed and ran Home Assistant plus Mosquitto, Ring MQTT, and python-matter-server.

## Task 1: Initial audit, plan, and implementation of the Home Assistant stack

Outcome: success

Preference signals:
- The user explicitly wanted a practical, working setup and later said to “perform needed edits” and “create a audit report of my setup to improve it” -> in similar homelab work, do concrete operational changes, not just advice.
- The user emphasized not exposing Home Assistant publicly, not changing firewall/router settings, not deleting volumes, and preserving secrets -> future similar runs should default to cautious local-only changes and secret-safe handling.
- The user repeatedly asked for validation and concrete status -> after edits, validate with Compose + HA config check + live HTTP/container checks before claiming success.

Key steps:
- Discovered the live Home Assistant stack already existed and was containerized with Docker Compose.
- Took timestamped backups before editing, including a later config-only backup mode when live log files made full backup archives noisy.
- Removed the legacy LuCI YAML device tracker because it was failing at startup and redundant with GL.iNet-backed tracking.
- Added recorder retention and exclusions to reduce recorder DB growth driven by Glances/network sensors.
- Added a maintenance package for logger controls, plus scripts for backup, validation, deploy, restart, logs, status, and rollback dry-run.
- Removed the Docker socket mount after checking that Home Assistant config did not depend on it, and narrowed `trusted_proxies` to the observed reverse proxy/tunnel IPs plus localhost.
- Disabled `network_scanner` via Home Assistant storage because it was causing startup delay and duplicating router/device tracking.

Failures and how to do differently:
- The first backup attempts failed because live files changed during archiving and because some files were root-owned; the working fix was to use `sudo` and to exclude live logs/volatile files from the default backup path.
- A broad `rg` over the config tree pulled in huge custom component blobs and generated too much output; future similar inventory work should target `.storage` JSON and specific config files rather than recursive grep over bundled frontend assets.
- The `network_scanner` integration could not be safely edited in place while Home Assistant was running; the correct fix was to stop Home Assistant, update the config entry in `.storage`, then restart.

Reusable knowledge:
- In this stack, the live config is bind-mounted from `/home/ethan/docker/home-assistant/config/homeassistant`.
- Home Assistant config validation with `docker exec HomeAssistant python -m homeassistant --script check_config --config /config` works and is a useful gate before restarts.
- `docker compose -f /home/ethan/docker/home-assistant/docker-compose.yml config` is a reliable way to confirm the rendered compose after edits.
- `network_scanner` was a single config entry/entity pair in `.storage`; disabling the config entry removed the startup delay.
- The Docker socket mount was not needed for this setup and could be removed safely once inspected.
- `trusted_proxies` had been a broad `172.25.0.0/16`; narrowing it to the observed proxy/tunnel IPs was a concrete hardening step.

References:
- [1] `docker compose -f /home/ethan/docker/home-assistant/docker-compose.yml config` rendered the four services and confirmed the compose file was valid.
- [2] `docker exec HomeAssistant python -m homeassistant --script check_config --config /config` passed before and after edits.
- [3] `docker inspect HomeAssistant --format '{{json .Mounts}}'` confirmed `/var/run/docker.sock` was removed after the final edit.
- [4] `network_scanner` config entry in `.storage/core.config_entries` ended up `disabled_by: user`; entity `sensor.network_scanner` became `disabled_by: config_entry`.
- [5] Audit report file written: `/home/ethan/docker/home-assistant/docs/audit-report-2026-06-14.md`.

## Task 2: Audit report creation

Outcome: success

Preference signals:
- The user explicitly asked to “create a audit report of my setup to improve it” -> future similar requests should produce a concrete, prioritized report with evidence and next steps, not a generic checklist.
- The user wanted the report based on live state and asked to avoid secret-bearing content -> include evidence, sizes, registry counts, and logs, but redact secret values and sensitive payloads.

Key steps:
- Gathered live evidence from container status, HTTP reachability, Home Assistant config validation, registry counts, DB/backup sizes, and startup logs.
- Wrote a dated audit report in docs with executive summary, findings, risks, recommendations, implementation order, verification commands, and “do not do” boundaries.
- Marked findings as resolved or pending as the work progressed.

Failures and how to do differently:
- Some log/registry extraction commands were too broad and produced huge output from custom component assets; future audits should use focused JSON parsing and log filters only.
- A few size probes required `sudo` for root-owned paths; use `sudo -n` in size/status tooling where the live config tree contains protected files.

Reusable knowledge:
- `ha-status.sh` became the best single command for a quick audit snapshot: container health, HTTP `200`, config check, DB size, backup size, and recent warnings/errors.
- The audit found that `network_scanner` delayed startup, the recorder DB was ~1.2G, manual backups were ~5.6G, and there were many custom integrations plus repeated `/api/mcp` auth attempts.
- The report should distinguish between resolved items and items that are still informational (for example, startup warnings from loaded custom integrations that remain installed).

References:
- [1] Audit report file: `/home/ethan/docker/home-assistant/docs/audit-report-2026-06-14.md`.
- [2] `ha-status.sh` output used for the report showed `HomeAssistant` healthy, HTTP `200`, DB `1.2G`, backups `5.6G`, and the startup warnings.
- [3] Registry counts extracted from `.storage`: `core.config_entries` 49, `core.device_registry` 82, `core.entity_registry` 6616, `lovelace_dashboards` 3.

## Task 3: Needed edits after the audit

Outcome: success

Preference signals:
- When the user said “perform needed edits,” they wanted the audit findings turned into concrete changes, not more discussion -> future similar runs should move from audit to implementation once the risk is clear.
- The user accepted targeted, local changes and repeated the safety constraints -> keep edits narrow, reversible, and verified.

Key steps:
- Removed the Docker socket bind mount from Compose.
- Narrowed `trusted_proxies` to specific observed proxy/tunnel container IPs plus localhost.
- Disabled `network_scanner` in Home Assistant storage while Home Assistant was stopped, then restarted only Home Assistant.
- Updated docs to reflect the resolved state and current operational guidance.
- Revalidated the stack after each major edit and confirmed the live endpoint stayed reachable.

Failures and how to do differently:
- Docker-assigned IPs for `npm` and `cloudflared_tunnel` are not stable across recreates; future similar proxy hardening should either use static container IPs on the shared network or re-check and update the trusted list after recreating those containers.
- Startup logs still show generic custom-integration loader warnings and `py.warnings`; those are informational unless they become blocking.

Reusable knowledge:
- A safe sequence for this stack is: backup -> compose/YAML validation -> stop HomeAssistant only if storage edits are needed -> edit `.storage` or config -> restart/recreate only Home Assistant -> confirm `health: healthy` and `http://127.0.0.1:8123/` returns 200.
- `ha-backup.sh --mode config` is the practical default backup mode; full backups are reserved for riskier changes.
- `network_scanner` was a single config entry that could be disabled cleanly by editing `core.config_entries` while Home Assistant was stopped.

References:
- [1] `docker compose up -d home-assistant` was used to recreate only Home Assistant after edits.
- [2] `docker inspect HomeAssistant --format '{{json .Mounts}}'` after the change no longer listed `/var/run/docker.sock`.
- [3] `docker inspect HomeAssistant --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} ...'` showed `healthy` after the start period.
- [4] `network_scanner` config entry became `disabled_by: user`, and `sensor.network_scanner` became `disabled_by: config_entry`.
- [5] Updated docs: `/home/ethan/docker/home-assistant/docs/home-assistant-runbook.md`, `/home/ethan/docker/home-assistant/docs/custom-integrations.md`, `/home/ethan/docker/home-assistant/docs/audit-report-2026-06-14.md`.
