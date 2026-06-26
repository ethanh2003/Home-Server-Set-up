# 2026-06-14T00-44-24-X68g-spotify_stats_import_oauth_session_diagnosis

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019ec396-3e92-7a50-81c9-7fbf1b42fd20
updated_at: 2026-06-14T00:50:32+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/14/rollout-2026-06-14T00-44-24-019ec396-3e92-7a50-81c9-7fbf1b42fd20.jsonl
cwd: /home/ethan

# Diagnosed Spotify Stats import trouble as an OAuth/session problem, not a Mongo/storage problem

Rollout context: The work happened in `/home/ethan/docker/spotify-stats` from the broader homelab workspace at `/home/ethan`. The prior rollout had already switched the app off a bind-mounted Mongo datastore and onto a fresh named Docker volume, so this follow-up focused on why the import UI was still having issues.

## Task 1: Trace why the Spotify import is having issues

Outcome: partial

Preference signals:
- The user asked a direct troubleshooting question: "why is my import having issues" -> in similar situations, they want the specific failure cause traced end-to-end rather than a broad product explanation.
- The user did not ask for a rebuild or redesign; the investigation stayed on logs and runtime state, suggesting a preference for evidence-first debugging before making more changes.

Key steps:
- Checked the memory notes for existing Spotify Stats import/backfill guidance and prior OAuth/Mongo recovery context.
- Inspected `docker logs` for `mongo` and `spotify-stats-server-1`, then confirmed the server process was running and `/imports` returned a login redirect when unauthenticated.
- Found two distinct signals in the server logs:
  - `NotLoggedError` on `/imports` / `/oauth/spotify/me`, indicating the app lacked a valid logged-in session for the import UI.
  - Spotify token exchange requests returning `400 Bad Request` on `accounts.spotify.com/api/token`, which points to an OAuth callback / auth-code problem rather than Mongo being down.
- Also observed the import job itself had already started successfully with `POST /import/full-privacy 200`, and the log stream showed the importer processing a very large export (`262759` rows) while skipping many tracks with messages like `passed, only listened for X seconds`.

Failures and how to do differently:
- The issue was not a database outage; Mongo was healthy and the server process was up. Future debugging should check OAuth/session validity before spending time on storage or proxy layers.
- The import noise is not itself an error: many `passed, only listened for X seconds` lines are normal threshold filtering during Spotify export imports.
- The current evidence supports an auth/session root cause (expired/reused auth code, redirect URI mismatch, or stale browser session/cookie state), but the rollout did not resolve which one yet.

Reusable knowledge:
- For Spotify Stats import issues, the useful separation is:
  - `NotLoggedError` / `/imports` 401 or redirect behavior -> auth/session problem.
  - `POST /import/full-privacy 200` plus lots of `passed` lines -> importer is running normally and filtering short listens.
  - `accounts.spotify.com/api/token` `400 Bad Request` -> OAuth callback/token-exchange failure.
- A healthy-looking server and Mongo do not rule out an import failure; the login/OAuth path can still block the UI.
- The durable import path in this app is Spotify export import (extended streaming history / full privacy export), not a full historical API sync.

References:
- [1] `docker logs --tail 200 spotify-stats-server-1` showed `NotLoggedError` and many `POST /import/full-privacy 200` / `GET /imports 304` lines.
- [2] `docker logs spotify-stats-server-1 | rg -n -C 3 "NotLoggedError|responseUrl: 'https://accounts.spotify.com/api/token|statusCode: 400|Bad Request"` surfaced the OAuth token exchange failure and the login guard.
- [3] `POST /import/full-privacy 200 1880.574 ms - 25` and repeated `Track ... was passed, only listened for X seconds` lines indicated the importer was actively running, not stuck.
- [4] `nl -ba /home/ethan/.codex/memories/MEMORY.md | sed -n '50,62p'` confirmed the stored guidance: Spotify backfill is export-based, and the supported path is extended streaming history / full privacy data export.
