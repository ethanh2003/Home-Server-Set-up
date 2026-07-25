# 2026-07-04T22-00-31-Eg8V-vault_inbox_agents_md_contributor_guide

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f2f25-c310-7140-a387-74cfd3118019
updated_at: 2026-07-05T02:11:08+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/04/rollout-2026-07-04T22-00-31-019f2f25-c310-7140-a387-74cfd3118019.jsonl
cwd: /home/ethan/obsidian-notes

# Added a concise contributor guide for the `vault-inbox` repository and verified it met the requested constraints.

Rollout context: The user explicitly asked for a new `AGENTS.md` contributor guide for `/home/ethan/docker/vault-inbox`, titled `Repository Guidelines`, 200-400 words, with clear sections covering structure, commands, style, testing, commits/PRs, and security notes. The repository is the self-hosted `vault-inbox` stack (FastAPI backend, React/Vite frontend, Docker Compose, SQLite, Obsidian vault mount), and the guide should reflect that current layout and safety defaults.

## Task 1: Create repository contributor guide

Outcome: success

Preference signals:
- The user asked for a specific file type and location: `Generate a file named AGENTS.md that serves as a contributor guide for this repository` -> future repo-documentation tasks should default to creating a concise `AGENTS.md` when requested, rather than proposing alternatives first.
- The user required a fixed tone/shape: `Title the document "Repository Guidelines"`, `Keep the document concise. 200-400 words is optimal.`, `Provide examples where helpful` -> future writeups should be short, instructional, and example-backed instead of broad or essay-like.
- The user wanted the guide to be specific to this project’s current stack (backend, frontend, Docker, SQLite, mounted vault, policies) -> future contributor docs should be grounded in actual repo structure rather than generic template language.

Key steps:
- Confirmed the target repo was `/home/ethan/docker/vault-inbox` after checking the initially referenced empty `/home/ethan/obsidian-notes` directory.
- Inspected the repo’s `README.md`, backend/frontend package metadata, Docker Compose, and file layout to align the guide with the real project structure.
- Wrote `AGENTS.md` with sections for project structure, build/test/dev commands, coding style, testing, commit/PR guidance, and security/config tips.
- Verified the final file with `wc -w`, `sed`, a secret-pattern grep, and Git status.

Failures and how to do differently:
- The first pass correctly detected that `/home/ethan/obsidian-notes` was empty and not the target repo. Future similar requests should verify the actual repository root before writing documentation.
- No functional code failures occurred for the file itself; the only caution is that the parent `/home/ethan/docker` repo is very dirty, so status checks there are noisy and should be interpreted carefully.

Reusable knowledge:
- The `vault-inbox` repo already has a practical split: backend in `backend/src/vault_inbox/`, tests in `backend/tests/`, frontend in `frontend/src/`, build output in `frontend/dist/`, policies in `policies/`, and runtime data in `data/` and `logs/`.
- `docker compose build` and `docker compose up -d` are the main deployment commands for the stack; `pytest` and `npm run build` are the key validation commands.
- `VAULT_INBOX_CODEX_ENABLED=false` is the safe default documented in the repo guide.

References:
- [1] Created `/home/ethan/docker/vault-inbox/AGENTS.md` with title `# Repository Guidelines` and the requested sections.
- [2] Verification: `wc -w /home/ethan/docker/vault-inbox/AGENTS.md` returned `314` words.
- [3] Verification: `sed -n '1,220p' /home/ethan/docker/vault-inbox/AGENTS.md` showed the expected content and structure.
- [4] Safety check: `grep -Ein '(api[_-]?key|token|password|secret|BEGIN .*PRIVATE KEY|cookie|session)'` matched only instruction text, not actual secrets.
- [5] Git status: `git -C /home/ethan/docker status --short vault-inbox/AGENTS.md` showed the file as untracked in the parent repo (`?? vault-inbox/AGENTS.md`).
