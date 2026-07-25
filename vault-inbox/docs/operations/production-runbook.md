# vault-inbox Production Runbook

This runbook is for operating `vault-inbox` in Ethan's homelab. It assumes the app lives at `/home/ethan/docker/vault-inbox`, the live Obsidian vault is mounted at `/data/Obsidian/Main`, and the Docker service is attached to `proxy_net`.

## Production Invariants

- Keep `VAULT_INBOX_CODEX_ENABLED=false` and `VAULT_INBOX_WORKER_ENABLED=false` in Docker.
- Run authenticated Codex processing only from the host user service `vault-inbox-host-worker.service`.
- Keep command-center access behind LAN/VPN or Cloudflare Access. Do not expose it directly to the public Internet.
- Keep `/data/Obsidian/Main` Git-clean before and after worker activity.
- Do not commit `data/`, `logs/`, Codex logs, SQLite files, `.env`, private vault content, or generated caches.

## Deploy And Verify Docker

Deploy from the repo root:

```bash
cd /home/ethan/docker/vault-inbox
docker compose build
docker compose up -d
```

Validate the generated Compose config:

```bash
docker compose config >/tmp/vault-inbox-compose-config.txt
```

Expected: exit code `0`.

Check container state:

```bash
docker inspect -f '{{.State.Status}} {{.State.Health.Status}}' vault-inbox
```

Expected:

```text
running healthy
```

Check redacted health from inside the container:

```bash
docker exec vault-inbox curl -fsS http://127.0.0.1:8080/api/health
```

Expected shape:

```json
{"app":{"ok":true,"name":"vault-inbox"},"vault":{"ok":true},"codex":{"enabled":false},"ollama":{"model":"nomic-embed-text"},"smtp":{"enabled":true}}
```

If the container is unhealthy, inspect recent logs:

```bash
docker logs --tail 120 vault-inbox
```

Do not enable container Codex processing to fix health. The container intentionally lacks host Codex auth.

## Host Codex Worker

Install or refresh the user service:

```bash
mkdir -p ~/.config/systemd/user
cp /home/ethan/docker/vault-inbox/deploy/vault-inbox-host-worker.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now vault-inbox-host-worker.service
```

Check status:

```bash
systemctl --user status vault-inbox-host-worker.service --no-pager
```

Expected: `Active: active (running)` and an `ExecStart` using:

```text
/home/ethan/docker/vault-inbox/backend/.venv/bin/python -m vault_inbox.host_worker
```

Restart after code changes:

```bash
systemctl --user restart vault-inbox-host-worker.service
```

Follow worker logs:

```bash
journalctl --user -u vault-inbox-host-worker.service -n 120 --no-pager -f
```

Run a one-shot idle check:

```bash
/home/ethan/docker/vault-inbox/backend/.venv/bin/python -m vault_inbox.host_worker \
  --once \
  --database-path /home/ethan/docker/vault-inbox/data/vault-inbox.sqlite3 \
  --vault-root /data/Obsidian/Main \
  --app-repo-root /home/ethan/docker/vault-inbox \
  --codex-binary /usr/local/bin/codex
```

Expected when no work is queued:

```text
INFO:__main__:process_once result: None
```

The worker marks a claimed job as `running`. If the worker is interrupted, jobs older than `VAULT_INBOX_WORKER_STALE_RUNNING_SECONDS` are requeued on the next worker pass. The default is `1800` seconds.

## Queue Operations

Check action-needed jobs and queue eligible reruns:

```bash
docker exec vault-inbox curl -fsS -X POST http://127.0.0.1:8080/api/commands/queue-reruns
```

Expected when current work is complete:

```json
{"ok":true,"queued":0,"jobs":[]}
```

Operational meanings:

- `queued`: waiting for the host worker.
- `running`: claimed by a worker.
- `completed`: Codex processing completed; `commit_sha` may be empty if there was no committable diff.
- `needs_rerun`: capture-only fallback exists and Codex should be retried.
- `needs_review`: processing was skipped or rejected and needs operator review.
- `superseded`: historical attempt; a newer job for the same capture/job type exists.

If a capture falls back to capture-only, inspect `Vault Admin/Inbox/YYYY-MM-DD.md` in the vault and the job error before rerunning. Do not delete historical job rows from SQLite as routine cleanup.

## Vault Git Safety

Check vault cleanliness before and after worker activity:

```bash
git -C /data/Obsidian/Main status --short --untracked-files=all
```

Expected for a clean vault: no output.

Check recent vault commits:

```bash
git -C /data/Obsidian/Main log --oneline -8
```

`vault-inbox` commits should use messages such as:

```text
vault-inbox codex job <job-prefix>
vault-inbox capture-only fallback <job-prefix>
```

The policy engine blocks hidden/plugin paths, trash, secret-like files, and old Therapy transcript/summary/archive paths. Normal ignored folders such as `.obsidian/` may exist in the vault; they should not block Codex runs unless Codex changes them.

If the vault is dirty:

1. Inspect paths with `git -C /data/Obsidian/Main status --short --untracked-files=all`.
2. Review only non-sensitive paths relevant to `vault-inbox`.
3. Commit allowed operational notes if they are valid and intentional.
4. Leave therapy, secrets, plugin config, and ambiguous personal content for manual review.

Do not run `git reset --hard` or delete vault content as a routine recovery step.

## Cloudflare Access

`https://inbox.ethan-herring.com` must be protected before off-LAN use. Cloudflare's current docs describe Access self-hosted apps as policy-checked web apps, and Tunnel published applications as public-hostname-to-service mappings.

Reference docs:

- Cloudflare Access self-hosted apps: <https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/>
- Cloudflare Tunnel published applications: <https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/>
- Cloudflare Tunnel setup: <https://developers.cloudflare.com/tunnel/setup/>

Manual dashboard path:

1. In Cloudflare Zero Trust, create or open a self-hosted Access application named `vault-inbox`.
2. Add public hostname `inbox.ethan-herring.com`.
3. Add an allow policy for `echerring.ech@gmail.com`.
4. In Networking > Tunnels, add a published application route for `inbox.ethan-herring.com`.
5. Set service URL to `http://vault-inbox:8080` from the `cloudflared` container on `proxy_net`.
6. Enable Access protection on the route.
7. Visit `https://inbox.ethan-herring.com` from an off-LAN browser and confirm Cloudflare Access prompts before the app loads.

Scripted path:

```bash
export CLOUDFLARE_API_TOKEN=...
export CLOUDFLARE_ACCOUNT_ID=...
export CLOUDFLARE_ZONE_ID=...
export CLOUDFLARE_TUNNEL_ID=...
export CLOUDFLARE_ZERO_TRUST_TEAM_NAME=...
python3 /home/ethan/docker/vault-inbox/scripts/cloudflare-vault-inbox-access.py
```

The default mode is dry-run. Review all payloads, then apply:

```bash
python3 /home/ethan/docker/vault-inbox/scripts/cloudflare-vault-inbox-access.py --apply
```

If the token cannot update Tunnel configuration, run:

```bash
python3 /home/ethan/docker/vault-inbox/scripts/cloudflare-vault-inbox-access.py --apply --skip-tunnel-config
```

Then finish the Tunnel public hostname route manually in the dashboard.

## Common Incidents

### Container unhealthy

```bash
docker inspect -f '{{.State.Status}} {{.State.Health.Status}}' vault-inbox
docker logs --tail 120 vault-inbox
docker compose config >/tmp/vault-inbox-compose-config.txt
```

If config is valid and logs point to a transient startup issue, recreate the service:

```bash
cd /home/ethan/docker/vault-inbox
docker compose up -d
```

### Host worker down

```bash
systemctl --user status vault-inbox-host-worker.service --no-pager
journalctl --user -u vault-inbox-host-worker.service -n 120 --no-pager
systemctl --user restart vault-inbox-host-worker.service
```

After restart, confirm the queue:

```bash
docker exec vault-inbox curl -fsS -X POST http://127.0.0.1:8080/api/commands/queue-reruns
```

### Codex auth or binary failure

Check the configured binary:

```bash
/usr/local/bin/codex --version
```

Inspect the latest Codex logs without copying sensitive content into tickets or public notes:

```bash
find /home/ethan/docker/vault-inbox/logs/codex -maxdepth 1 -type f -printf '%TY-%Tm-%Td %TH:%TM %p\n' | sort | tail -10
```

If auth is broken, fix host Codex auth on the host. Do not mount `/home/ethan/.codex/auth.json` into the Docker container.

### Dirty vault blocks processing

```bash
git -C /data/Obsidian/Main status --short --untracked-files=all
```

Review changed paths. Commit only allowed, intentional, non-sensitive operational notes. Leave protected paths and ambiguous personal content untouched until reviewed.

### Stuck running job

Check service status and logs first:

```bash
systemctl --user status vault-inbox-host-worker.service --no-pager
journalctl --user -u vault-inbox-host-worker.service -n 120 --no-pager
```

If the worker was interrupted, wait for `VAULT_INBOX_WORKER_STALE_RUNNING_SECONDS` and let the worker requeue the stale job on its next pass. Then run:

```bash
/home/ethan/docker/vault-inbox/backend/.venv/bin/python -m vault_inbox.host_worker \
  --once \
  --database-path /home/ethan/docker/vault-inbox/data/vault-inbox.sqlite3 \
  --vault-root /data/Obsidian/Main \
  --app-repo-root /home/ethan/docker/vault-inbox \
  --codex-binary /usr/local/bin/codex
```

### Cloudflare route not protected

If `https://inbox.ethan-herring.com` loads without Cloudflare Access from off-LAN:

1. Disable or remove the public hostname route until Access is configured.
2. Confirm the Access application domain is `inbox.ethan-herring.com`.
3. Confirm the policy allows only the intended email.
4. Confirm the Tunnel route has Access protection enabled.
5. Retest from an off-LAN browser session.

## Release Verification

Run this full local verification before considering a production change complete:

```bash
cd /home/ethan/docker/vault-inbox
backend/.venv/bin/python -m pytest -q
(cd frontend && npm run build && npm run test:e2e)
docker compose config >/tmp/vault-inbox-compose-config.txt
docker inspect -f '{{.State.Status}} {{.State.Health.Status}}' vault-inbox
docker exec vault-inbox curl -fsS http://127.0.0.1:8080/api/health
docker exec vault-inbox curl -fsS -X POST http://127.0.0.1:8080/api/commands/queue-reruns
systemctl --user status vault-inbox-host-worker.service --no-pager
git -C /data/Obsidian/Main status --short --untracked-files=all
```

Expected:

- Backend tests pass.
- Frontend build passes.
- Playwright E2E passes.
- Docker Compose config exits `0`.
- Container state is `running healthy`.
- Health response is redacted and reports `codex.enabled=false`.
- Queue rerun response is `queued: 0` when no work is pending.
- Host worker is active.
- Vault Git status has no output.
