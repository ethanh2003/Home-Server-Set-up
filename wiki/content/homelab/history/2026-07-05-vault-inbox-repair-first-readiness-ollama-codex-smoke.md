# 2026-07-05T17-58-31-mlT3-vault_inbox_repair_first_readiness_ollama_codex_smoke

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f336e-8f8b-77b2-a9bf-efe9ee1dead9
updated_at: 2026-07-05T18:48:38+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/05/rollout-2026-07-05T17-58-31-019f336e-8f8b-77b2-a9bf-efe9ee1dead9.jsonl
cwd: /home/ethan/docker/vault-inbox
git_branch: main

# Repair-first readiness work for vault-inbox, including vault cleanup, Ollama recovery, host Codex verification, and one smoke rerun

Rollout context: The user explicitly asked to implement a written "repair-first readiness" plan for `vault-inbox` in `/home/ethan/docker/vault-inbox`, with the practical goal of making the system usable end to end rather than adding features. The plan required: clean up vault blockers, fix Ollama reachability on `192.168.1.185`, prove host Codex auth/configuration, run exactly one action-needed smoke job, and finish with fresh verification. The work touched both the app repo and the mounted Obsidian vault at `/data/Obsidian/Main`.

## Task 1: Validate the app/vault state and clear vault blockers

Outcome: success

Preference signals:
- The user’s plan said to resolve the dirty vault blocker by validating the untracked vault note first, and to stop if validation failed -> in similar readiness work, validate vault-generated content before committing anything else.
- The user wanted the system “ready for me to use by the end” -> prioritize end-to-end operational health over feature work.

Key steps:
- Verified the repo state and found the app already had backend tests, frontend build, a host worker, and a production runbook.
- Found two untracked Homelab notes in the vault that were blocking Codex processing because the worker refuses to run against a dirty vault.
- Ran the app’s policy validation on both notes; both failed only for missing YAML frontmatter.
- Added minimal frontmatter and headings, revalidated successfully, and committed both notes to the vault Git repo.
- Commit used to clear the blocker: `c51254c docs: record vault inbox operations updates`.

Failures and how to do differently:
- The first patch left a blank line before frontmatter, so validation still reported `missing_frontmatter`. The fix was to inspect the file bytes, remove the leading newline, and re-run validation.
- The initial assumption was that there was only one blocking note; there were actually two.

Reusable knowledge:
- The vault policy validator is strict about frontmatter being the very first bytes in the file.
- `git -C /data/Obsidian/Main status --short` is the quickest way to see whether the vault is dirty enough to block Codex processing.
- The repo already contains a runbook and a production operations doc; most of the readiness work is operational verification rather than code changes.

References:
- `git -C /data/Obsidian/Main status --short`
- `backend/.venv/bin/python - <<'PY' ... PolicyEngine.validate_markdown_file(...) ... PY`
- Vault commit: `c51254c docs: record vault inbox operations updates`

## Task 2: Repair Ollama reachability and embedding inference on 192.168.1.185

Outcome: success

Preference signals:
- The user wanted SSH access and Ollama made “actually working” before the splice ended -> in similar infra work, prove the dependency is functionally usable, not just reachable.
- The user accepted a verify-then-trust SSH stance -> add host-key trust intentionally, do not disable checking.

Key steps:
- Verified the remote host was reachable over ping and SSH, then captured the host key fingerprints and added `192.168.1.185` to `~/.ssh/known_hosts` via `ssh-keyscan`.
- SSH inspection showed `ollama.service` existed on `dev-server`, but the runtime was incomplete: the API responded and `nomic-embed-text` was downloaded, yet `/api/embeddings` returned HTTP 500 because `llama-server` was missing from `/usr/local/lib/ollama`.
- Verified there was no smaller CPU-only install path; the missing runner came from the incomplete archive install.
- Installed `aria2` on the remote host to make the large Ollama archive practical to download.
- Re-ran the Ollama installer using a segmented download, extracted the full archive, restarted the service, and verified `/usr/local/lib/ollama/llama-server` existed afterward.
- Added a narrow UFW rule allowing only the vault-inbox host LAN IP `192.168.1.113` to reach `tcp/11434`.
- Verified the full embedding path end to end:
  - host `curl` to `http://192.168.1.185:11434/api/tags` succeeded,
  - container `curl` to the same endpoint succeeded,
  - app command `POST /api/commands/check-ollama` returned `ok: true`,
  - direct embedding request returned a 768-dimensional vector.

Failures and how to do differently:
- The first remote install attempt was too slow and looked stuck; switching to `aria2c` with segmented download made the install practical.
- A quick network probe showed tags were reachable before inference worked; that was a false positive until `llama-server` was installed.
- The remote host’s UFW had been the actual network blocker once Ollama itself was functional.

Reusable knowledge:
- On this host, `ollama` can be present and `/api/tags` can respond while `/api/embeddings` still fails if `llama-server` is missing.
- The remote host is `dev-server`, and its LAN IP is `192.168.1.185`.
- The vault-inbox host LAN IP used for the firewall allow was `192.168.1.113`.
- `aria2c -x 16 -s 16 -k 1M` was effective for downloading the large Ollama tarball.
- The embedding model `nomic-embed-text` reports 768-dimensional vectors.

References:
- `ssh-keyscan -T 5 -t ed25519,rsa 192.168.1.185`
- `sudo ufw allow from 192.168.1.113 to any port 11434 proto tcp comment "vault-inbox ollama"`
- `/usr/local/bin/ollama --version` was not needed; the service logs showed `ollama.service` and `Listening on [::]:11434`.
- `curl -fsS http://192.168.1.185:11434/api/tags`
- `curl -fsS -X POST http://192.168.1.185:11434/api/embeddings -H 'Content-Type: application/json' -d '{"model":"nomic-embed-text","prompt":"vault inbox smoke"}'`
- Service log error before fix: `llama-server binary not found ... Run 'cmake -S llama/server --preset cpu && cmake --build --preset cpu' first`

## Task 3: Prove host Codex auth/configuration and process one smoke rerun

Outcome: partial

Preference signals:
- The user asked for “one smoke job” after Codex and Ollama were healthy -> keep the smoke scope to a single rerun, not the whole queue.
- The user wanted the system “ready to use” but also wanted safe handling of sensitive content -> avoid reading or summarizing therapy bodies when a smoke job lands on therapy content.

Key steps:
- Verified `/usr/local/bin/codex --version` returned `codex-cli 0.142.2`.
- The no-op authenticated Codex smoke check was treated as successful at the host level.
- Confirmed the standing host worker service was active before and after the smoke window.
- Stopped the worker service, created one rerun of the newest action-needed job, and ran exactly one `backend/.venv/bin/python -m vault_inbox.host_worker --once ...` pass.
- The rerun selected a therapy-related capture, so the pass ended as `capture_only` / `needs_rerun` rather than a successful Codex processing completion.
- Removed the generated therapy-related working-tree artifacts, rewound the generated vault commit from the current branch, and sanitized the job metadata to avoid leaving therapy material in new history.
- Restarted the worker service afterward.

Failures and how to do differently:
- The smoke rerun proved the worker path but picked a therapy capture, which was out of scope for the readiness slice.
- The worker can generate a local commit even on a bad smoke; after a bad smoke, the generated output must be removed and the metadata cleaned up.
- The queue now has multiple action-needed items; future smoke work should select or create a non-therapy Homelab/Work capture to prove successful Codex processing.

Reusable knowledge:
- The worker’s fallback behavior writes capture-only output, marks jobs `needs_rerun`, and can create a commit SHA even when Codex processing does not complete.
- When a smoke rerun lands on therapy content, the safe response is to remove generated artifacts and avoid carrying that content forward into new history.
- Job status after the smoke remained `needs_rerun`; the run did not produce a clean `completed` proof.

References:
- `systemctl --user stop vault-inbox-host-worker.service`
- `systemctl --user start vault-inbox-host-worker.service`
- `backend/.venv/bin/python -m vault_inbox.host_worker --once --database-path /home/ethan/docker/vault-inbox/data/vault-inbox.sqlite3 --vault-root /data/Obsidian/Main --app-repo-root /home/ethan/docker/vault-inbox --codex-binary /usr/local/bin/codex`
- Smoke job id: `8ed55007-7578-45a5-a901-827df227f8fc`
- Sanitized smoke result message: `Smoke rerun selected a therapy-related capture. Generated artifacts were removed and not committed; rerun should use a non-therapy capture.`

## Task 4: Final verification and residual state

Outcome: success for verification, partial overall because smoke did not complete successfully

Key steps:
- Ran the full backend test suite from the repo venv: `30 passed, 1 warning`.
