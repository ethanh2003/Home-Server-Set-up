# 2026-06-29T21-43-48-mRhR-device_wide_unfinished_project_audit

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f1556-a735-7c40-bab1-77dce8d6f1f7
updated_at: 2026-06-29T21:46:12+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/29/rollout-2026-06-29T21-43-48-019f1556-a735-7c40-bab1-77dce8d6f1f7.jsonl
cwd: /home/ethan

# Device-wide unfinished-project audit from /home/ethan

Rollout context: The user asked for a list of all unfinished projects on this device. The agent used the required superpowers startup workflow, then verified live filesystem evidence under `/home/ethan` rather than relying only on prior memory. The main signal sources were git status, presence of plan/handoff docs, TODO/blocked markers, and missing/partial source files.

## Task 1: Audit `/home/ethan` for unfinished projects

Outcome: success

Preference signals:

- The user asked broadly for “all the unfinished projects on this device,” which implies future similar requests should be answered by evidence-based inventorying across the device rather than only naming known repos from memory.
- The user did not specify a narrow subset, so the agent treated “unfinished” as requiring concrete signals like dirty git trees, unchecked plan docs, no initial commit, or explicit blocked/remaining work, instead of listing every directory on disk.

Key steps:

- Read the required `superpowers:using-superpowers` skill first.
- Searched `/home/ethan` for git repos and plan/task docs, then narrowed to likely user-owned workspaces.
- Checked git status for the main candidate repos: `/home/ethan/chicago-dashboard`, `/home/ethan/docker`, `/home/ethan/docker/actual-budget/actual-auto-sync-src`, `/home/ethan/docker/spotify-stats/upstream-your_spotify`, and `/home/ethan/arr-multi-user`.
- Inspected plan docs and handoff docs in `chicago-dashboard` and `arr-multi-user` to distinguish “in-progress” from “complete”.
- Did a shallow check of non-git project-looking directories such as `/home/ethan/dymo-label`, `/home/ethan/file-server`, `/home/ethan/sync-files`, then filtered out runtime/data folders.

Failures and how to do differently:

- A broad `rg` over `/home/ethan` produced a huge amount of noise from vendored packages and runtime directories; future audits should exclude dependency/data trees earlier to avoid irrelevant matches.
- Some `.git` directories belonged to vendored or nested tool data, so the agent had to separate real user workspaces from caches and bundled dependencies.
- The audit was necessarily conservative for “unfinished”: several Docker stack directories had local edits, but those looked like completed stack additions rather than active unfinished projects, so they were not all listed as unfinished.

Reusable knowledge:

- In this environment, useful unfinished-work signals included:
  - dirty git trees with untracked/modified files,
  - plan documents with unchecked steps or “blocked” prerequisites,
  - no initial commit in a repo that already has scaffolded files,
  - frontends importing missing files,
  - repository handoff docs explicitly mentioning remaining work.
- `git status --short --branch` was the fastest way to split obvious repos into clean/dirty categories.
- For `chicago-dashboard`, the plans directory is the strongest signal that the app is mid-build: `maps-adapter` is marked complete, while `eta-engine`, `cta-adapter`, `weather-adapter`, `calendar-adapter`, `prefs-api-db`, and `cross-plan-consistency` are still implementation plans.
- For `arr-multi-user`, `AGENTS.md` plus `docs/superpowers/plans/2026-06-24-00-project-plan-index.md` and `docs/implementation/agent-handoff.md` show a repo in active setup/implementation with required remaining plan files and validation steps.
- `/home/ethan/dymo-label/AGENTS.md` explicitly says there was no git repo initialized there when written, and `frontend/src/App.tsx` imports `./stores/appStore`, `./components/Login`, and `./components/Editor`; the missing imports are a strong “unfinished frontend” signal.

References:

- [1] `git -C /home/ethan/chicago-dashboard status --short --branch` → `main...origin/main` with `M .env.example`, `M package-lock.json`, `M package.json`, and untracked `.deploy-*` plus `server.js`.
- [2] `git -C /home/ethan/docker status --short --branch` → `main...gitlab/main [ahead 13]` with many modified/removed/untracked files across Traefik/NPM/Home Assistant/Paperless/Wiki/stack tooling.
- [3] `git -C /home/ethan/arr-multi-user status --short --branch` → `No commits yet on master`, `A  .gitmodules`, `Am services/lidarr`, and many untracked repo files.
- [4] `sed -n '1,220p' /home/ethan/arr-multi-user/docs/superpowers/plans/2026-06-24-00-project-plan-index.md` showed unchecked steps and expected failing contract tests until the full companion plan set exists.
- [5] `/home/ethan/dymo-label/AGENTS.md` states: “There is no git repository initialized in this directory at the time this file was written.”
- [6] `/home/ethan/dymo-label/frontend/src/App.tsx` imports `./stores/appStore`, `./components/Login`, and `./components/Editor`, while `find /home/ethan/dymo-label/frontend/src -maxdepth 3 -type f` only showed `App.tsx`, `index.css`, `main.tsx`, and `vite-env.d.ts`.
- [7] `/home/ethan/docker/timemachine/README.md` includes a follow-up note: “If the Mac cannot route to `192.168.1.230` over Tailscale, advertise and approve a route for `192.168.1.230/32` as a follow-up change.” This is a durable example of a documented follow-up, but the overall stack was not treated as broadly unfinished.
- [8] The agent’s final user-facing list included: `chicago-dashboard`, `arr-multi-user`, `docker` homelab migration work, `home-assistant`, `actual-auto-sync-src`, `spotify-stats`/`upstream-your_spotify`, and `dymo-label`.

## Task 2: Distinguish true unfinished work from runtime/data folders

Outcome: success

Preference signals:

- The user asked for “projects on this device,” which led the agent to avoid counting every service directory or runtime data folder as a project.
- The agent explicitly separated completed stack additions like Pingvin, SMTP relay, Stash, Obsidian LiveSync, and LinkStack from the unfinished list, implying future audits should prefer strong evidence over directory presence alone.

Key steps:

- Performed shallow filesystem scans of `/home/ethan/dymo-label`, `/home/ethan/file-server`, and `/home/ethan/sync-files` to see whether they were actual projects or just data/runtime folders.
- Noted that `sync-files` contained secrets-like runtime files and no clear project scaffolding, so it should not be treated as a project by default.
- Noted that `file-server` did not surface enough project metadata to include it in the final unfinished-project list.

Failures and how to do differently:

- A naive directory scan would overcount data folders and vendored packages; future audits should combine structural evidence with git/plan evidence before listing something as a project.

Reusable knowledge:

- `/home/ethan/docker` contains many stack directories, but not all of them are unfinished work. Local modifications alone do not prove incompleteness.
- Good inclusion signals for “unfinished” are: explicit plan docs, missing source files, no initial commit, or clear blocked/remaining-work notes.

References:

- [1] `find /home/ethan -maxdepth 2 -mindepth 1 -type d ...` surfaced top-level project-like directories such as `/home/ethan/chicago-dashboard`, `/home/ethan/arr-multi-user`, `/home/ethan/docker`, `/home/ethan/dymo-label`, `/home/ethan/file-server`, and `/home/ethan/sync-files`.
- [2] `find /home/ethan/dymo-label -maxdepth 3 -type f ...` showed a real app structure with backend/frontend files, but no git repo.
- [3] `find /home/ethan/sync-files -maxdepth 2 -type f` showed runtime-like files (`idm.boltdb`, `ldap.crt`, `ldap.key`, `encryption.key`, `private-key.pem`) rather than a code project.
