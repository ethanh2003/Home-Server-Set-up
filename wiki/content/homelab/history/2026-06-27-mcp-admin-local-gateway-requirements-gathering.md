# 2026-06-27T03-17-14-lkyC-mcp_admin_local_gateway_requirements_gathering

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f0714-d85d-7991-829d-aa7d148f5c7a
updated_at: 2026-06-27T03:30:13+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/27/rollout-2026-06-27T03-17-14-019f0714-d85d-7991-829d-aa7d148f5c7a.jsonl
cwd: /home/ethan

# Requirements gathering for a comprehensive local MCP admin gateway

Rollout context: The user wanted to design a comprehensive Model Context Protocol (MCP) server for secure administrative access to their Docker environment and host PC, explicitly asking for clarifying questions first and no assumptions before architecture/implementation. The agent inspected the host and existing homelab/MCP footprints, then ran a long requirements-discovery interview.

## Task 1: Clarify scope and requirements for the MCP admin gateway

Outcome: partial

Preference signals:
- The user explicitly asked: "Before proposing an architecture or implementation, ask me as many clarifying questions as necessary... Do not make assumptions—gather enough information first" -> future agents should default to requirements-first, question-driven design for similar security-sensitive builds.
- When offered access scope, the user chose "Local only (Recommended)" -> the user prefers a localhost-only trust boundary for this admin-capable MCP server.
- When asked about admin surface, the user chose "Curated + gated shell" -> normal operation should use typed tools, with a separate high-friction shell escape hatch.
- When asked about clients, the user chose "Codex only" -> optimize for Codex compatibility first instead of broad client support.
- When asked about transport, the user chose "Local service (Recommended)" -> prefer a long-running localhost service over Codex-launched stdio.
- When asked about auth, the user chose "Local token + file ACL (Recommended)" -> even local services should require explicit token auth plus filesystem permissions.
- When asked about approvals, the user chose "Session unlock" and then "Until manually locked" for unlock duration -> unlocking should be explicit and persist until manually revoked, with status/audit visibility.
- When asked about audit storage, the user chose "SQLite + Docker logs (Recommended)" -> keep local structured audit data independent of the monitoring stack.
- When asked about capability breadth, the user chose "Full homelab ops" and later "Everything reachable" -> the design should treat this as a broad homelab control plane, not just a Docker wrapper.
- When asked about deployment, the user chose "Host systemd service (Recommended)" -> do not default to a containerized runtime for the MCP daemon.
- When asked about project location, the user chose "/home/ethan/mcp-admin" -> keep the project separate from the Docker stack repo.
- When asked about mutating behavior, the user chose "Plan then execute token" -> mutating tools should stage a plan/confirmation token before execution.
- When asked how to reuse existing servers, the user chose "Gateway with adapters (Recommended)" -> prefer one audited gateway with pluggable adapters rather than many disconnected MCP servers.
- When asked about secrets, the user chose "Local env files only" -> the initial design should assume local env-file-based config rather than SOPS/vault.
- When asked about privilege model, the user chose "Run as root" and then "Root with strict systemd hardening (Recommended)" -> root is acceptable only with strong compensating controls.
- When asked about filesystem scope, the user chose "Full filesystem by default" -> host-wide file access is desired, not a Docker-tree-only sandbox.
- When asked about backups, the user chose "No automatic backups" -> future plans should not assume automatic pre-write backups are acceptable.
- When asked about shell policy, the user chose "Interactive allowlist bypass with audit (Recommended)" -> after unlock, arbitrary shell is allowed but must be fully audited.
- When asked about service integrations, the user chose "Everything reachable" -> adapter scaffolding should anticipate all homelab services, not a narrow subset.
- When asked about adapter depth, the user chose "Full app APIs" but then agreed to "Phased v1 foundation (Recommended)" -> broad end-state, but delivery must be phased.
- When asked which adapters to do first, the user chose "Media stack" -> first full adapters after the core should prioritize ARR/media services.
- When asked about destructive Docker actions, the user chose "Two-step token + unlock (Recommended)" -> destructive Docker operations need stronger gating than ordinary host tools.
- When asked about high-risk host actions, the user chose "Unlock only" -> host-risk tools should not need the extra plan token, but still need unlock.
- When asked about audit retention, the user chose "90 days + aggressive redaction (Recommended)" -> logs should be retained locally but redacted conservatively.
- When asked about validation level, the user chose "Manual smoke tests only" -> the user did not want a large formal test matrix for this planning pass.
- When asked about third-party reuse, the user chose "Use any useful server" -> the plan may reuse existing MCP servers or integrations broadly, with judgment.
- When asked about dependency updates, the user deferred: "pick the rest based on best judgment" -> the agent had to infer conservative defaults for unasked operational details.

Key steps:
- The agent first inspected the host: Ubuntu 24.04, Docker Engine 29.5.0, single default Docker context, local Docker socket, and many running Compose-managed stacks under `/home/ethan/docker`.
- It discovered existing MCP-related footprints (`~/.codex/mcp`, VS Code `mcp.json`, Gemini extensions, and an ARR wrapper script).
- It confirmed there is already a `run-mcp-arr.sh` wrapper in `/home/ethan/docker/arr-suite/scripts/` that launches `npx -y mcp-arr-server` with env-driven Sonarr/Radarr/Prowlarr URLs and API keys.
- The agent used one-question-at-a-time prompting and kept refining scope, auth, privilege, transport, storage, and integration preferences before drafting a plan.
- The agent also searched the web for current MCP ecosystem references and found official Docker MCP catalog/toolkit materials, Portainer MCP, and MCP auth/transport docs, but did not proceed into implementation.

Failures and how to do differently:
- The rollout stopped at requirements gathering; no architecture was finalized with user approval, and no implementation or design-doc writing occurred.
- The assistant made a proposed plan, but the rollout ended before the user could approve or revise it, so future agents should treat the plan as provisional rather than settled.
- A skill-file path check (`/home/ethan/.codex/skills/.system/superpowers/using-superpowers/SKILL.md`) failed because the path did not exist; the working skill content came from the plugin cache path instead.
- The broad scope chosen by the user (“full homelab ops”, “everything reachable”, “full app APIs”) conflicts with the phased-delivery answer that was eventually framed; future agents should keep decomposing into phases even if the end goal remains broad.

Reusable knowledge:
- This host is Ubuntu 24.04 with Docker Engine 29.5.0; the Docker socket is `/var/run/docker.sock`, and the user account is already in the `docker` group.
- There are many live homelab stacks under `/home/ethan/docker`, including NPM, Traefik, monitoring, Home Assistant, Immich, Paperless, Stash, Pingvin, Jellyfin, the GitHub runner, and more; the deployment plan should likely integrate with that existing layout.
- Existing MCP-adjacent assets already present on the machine include `~/.codex/mcp/jellyfin-mcp-venv`, a VS Code MCP config file at `~/.config/Code/User/mcp.json`, Gemini MCP-related extensions, and `arr-suite/scripts/run-mcp-arr.sh`.
- The `run-mcp-arr.sh` script shows a reuse pattern worth preserving: load `.env` if present, export transport/host/port/path variables, default service URLs to localhost ports, require API keys, and exec `npx -y mcp-arr-server`.
- The user’s preferred v1 shape is: localhost-only, Codex-only, local token auth, session unlock/manual relock, root service with strict hardening, SQLite audit plus Docker logs, plan-then-execute for mutations, and a gateway architecture with pluggable adapters.
- The user accepted broad third-party reuse, but the plan should still assume explicit pinning and auditable integration rather than blind trust.
- The broad end-state should be delivered in phases, with the media stack as the first fully implemented adapter batch after the core gateway.

References:
- [1] Host snapshot: `Ubuntu 24.04.4 LTS`, kernel `7.0.5-zabbly+`, Docker Engine `29.5.0`, Docker socket `srw-rw---- root docker /var/run/docker.sock`, user in `docker` group.
- [2] Existing compose stacks discovered under `/home/ethan/docker`, including `/home/ethan/docker/arr-suite/docker-compose.yml`, `/home/ethan/docker/traefik/docker-compose.yml`, `/home/ethan/docker/monitoring-stack/docker-compose.yml`, `/home/ethan/docker/nginx-proxy-manager/docker-compose.yml`, `/home/ethan/docker/home-assistant/docker-compose.yml`, `/home/ethan/docker/immich/docker-compose.yml`, `/home/ethan/docker/paperless-ngx/docker-compose.yml`, `/home/ethan/docker/stash/docker-compose.yml`, and others.
- [3] Existing MCP-related artifacts: `/home/ethan/.codex/mcp/jellyfin-mcp-venv`, `/home/ethan/.config/Code/User/mcp.json`, `/home/ethan/.gemini/extensions/grafana/mcp-grafana`, `/home/ethan/.gemini/extensions/mcp-toolbox`, `/home/ethan/docker/arr-suite/scripts/run-mcp-arr.sh`.
- [4] `run-mcp-arr.sh` contents showed the reuse pattern: `export MCP_TRANSPORT="${MCP_TRANSPORT:-http}"`, `HOST="${MCP_ARR_HOST:-127.0.0.1}"`, `PORT="${MCP_ARR_PORT:-3000}"`, `MCP_PATH="${MCP_ARR_PATH:-/mcp}"`, defaults for `SONARR_URL`, `RADARR_URL`, `PROWLARR_URL`, and required `SONARR_API_KEY`, `RADARR_API_KEY`, `PROWLARR_API_KEY` before `exec npx -y mcp-arr-server`.
- [5] The assistant’s provisional plan captured the user-selected architecture: `/home/ethan/mcp-admin`, Python/FastMCP, host systemd service, token auth, SQLite audit, manual unlock, plan tokens for destructive Docker ops, unlock-only high-risk host actions, and phased adapters beginning with the media stack.
