# 2026-07-04T00-13-04-9UWQ-ebooks_stack_storygraph_csv_lazylibrarian_calibre_web_automa

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f2a78-c070-7a72-819c-f31e2ed1ed28
updated_at: 2026-07-04T00:31:41+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/04/rollout-2026-07-04T00-13-04-019f2a78-c070-7a72-819c-f31e2ed1ed28.jsonl
cwd: /home/ethan

# Implemented a new LAN/VPN-only ebook stack under `/home/ethan/docker/ebooks` and verified it starts, serves, and preserves the existing Calibre library.

Rollout context: The user wanted an ebook management setup that uses StoryGraph as the source of truth, LazyLibrarian or Readarr for finding/downloading EPUBs, Calibre for library management, and Send to Kindle; the approved plan settled on a separate `ebooks` stack with LazyLibrarian + Calibre-Web Automated (CWA), CSV-driven StoryGraph imports, no public exposure, and reuse of the existing SMTP relay.

## Task 1: Design and scope the ebook stack

Outcome: success

Preference signals:
- The user answered the sync question with `CSV-driven TBR (Recommended)` -> avoid designing around fragile/unofficial StoryGraph login/scraping and prefer import/export workflows.
- The user chose `Auto-download matches` -> the pipeline should allow unattended grabs for confident matches, with review for ambiguity.
- The user chose `Manual button (Recommended)` for Kindle delivery -> keep Send to Kindle manual rather than auto-emailing every import.
- The user chose `Yes, preserve it (Recommended)` for `/mnt/data_14tb/media/books` -> treat that as the canonical Calibre library and back it up before writes.
- The user chose `LazyLibrarian + CWA (Recommended)` -> prefer LazyLibrarian over Readarr for this homelab flow.
- The user chose `LAN/VPN only (Recommended)` -> do not add public reverse-proxy exposure for the new ebook stack.
- The user chose `Existing SMTP relay (Recommended)` -> wire Send to Kindle through the existing relay rather than a new mail path.
- The user chose `Watched drop folder (Recommended)` -> StoryGraph CSVs should enter via a mounted drop folder, not a manual UI upload.

Key steps:
- Inspected the live `arr-suite` and host layout first.
- Confirmed `arr-suite` currently runs only `gluetun`, `qbittorrent`, `prowlarr`, `radarr`, and `sonarr`.
- Confirmed `/mnt/data_14tb/media/books` already exists and contains a Calibre `metadata.db`.
- Confirmed older LazyLibrarian config still exists at `/home/ethan/docker/lazylibrarian_config` even though it is no longer in the active compose stack.
- Confirmed StoryGraph’s official API is not the basis for this design; CSV export is the intended durable bridge.

Failures and how to do differently:
- The rollout showed that prior LazyLibrarian usage existed in the repo but not in the active stack, so future work should verify current compose state rather than assume an older stack still exists.
- Public route assumptions would have been wrong here; the user’s LAN/VPN-only choice should be treated as a hard default for similar work.

Reusable knowledge:
- `/home/ethan/docker` is the homelab IaC root, and stack docs/inventory live there.
- The repo’s storage convention is: config/db under the stack directory, bulk media on `/mnt/data_14tb`, staging under `/data/staging`.
- `manage-stacks.sh` discovers any subdirectory containing `docker-compose.yml`, so adding a new stack directory automatically brings it into all-stack operations.

References:
- [1] Current stack check: `docker compose config --services` in `/home/ethan/docker/arr-suite` returned `gluetun`, `qbittorrent`, `prowlarr`, `radarr`, `sonarr`.
- [2] Existing library evidence: `/mnt/data_14tb/media/books/metadata.db` existed before implementation.
- [3] User choices: CSV-driven StoryGraph TBR, auto-download matches, manual Kindle button, preserve Calibre library, LazyLibrarian + CWA, LAN/VPN-only, existing SMTP relay, watched drop folder.

## Task 2: Implement the ebook stack and StoryGraph import helper

Outcome: success

Preference signals:
- The user’s plan explicitly required preserving `/mnt/data_14tb/media/books`, a watched StoryGraph CSV folder, and no public reverse proxy exposure -> keep those as hard implementation constraints.
- The user’s plan said `Do not store Kindle addresses, app passwords, SMTP credentials, or Amazon account details in committed files` -> keep secrets runtime-only.

Key steps:
- Added `ebooks/docker-compose.yml` with `calibre-web-automated` and `lazylibrarian`.
- Added `ebooks/.env.example` with non-secret path/port defaults.
- Added `ebooks/README.md` documenting first start, backup, StoryGraph import flow, and UI setup.
- Added `ebooks/scripts/storygraph_wishlist_import.py` to convert StoryGraph CSV exports into a LazyLibrarian-compatible wishlist CSV and review report.
- Added `ebooks/imports/storygraph/.gitignore` and `ebooks/reports/.gitignore` so dropped CSVs and generated reports do not pollute git status.
- Added tests in `tests/test-storygraph-wishlist-import.py` for CSV normalization, Calibre duplicate skipping, malformed rows, and `.env` loading.
- Updated `STACKS_README.md` and generated wiki content to include the new `ebooks` stack.
- Backed up Calibre metadata before first container start.
- Started the stack and verified both UIs come up.

Failures and how to do differently:
- The first implementation of the StoryGraph importer treated any review row as a failure; that was corrected so only malformed rows (`missing_title`, `missing_author`) return a nonzero exit.
- A syntax typo (`return values+`) was introduced during the `.env` loader patch and then fixed; future edits in the helper should be syntax-checked immediately.
- `wiki-sync --stack ebooks --check` is not a valid combination in this repo; the tool accepts `--stack` or `--check`, not both.
- The global wiki freshness check already fails because of unrelated stale generated pages elsewhere in the repo; that is not specific to the ebook work.

Reusable knowledge:
- CWA upstream wants completed files moved into `/cwa-book-ingest`; do not download directly into that path.
- LazyLibrarian’s install/config files show that the important config keys are real LazyLibrarian keys like `API_ENABLED`, `API_KEY`, `QBITTORRENT_HOST`, `QBITTORRENT_PORT`, `QBITTORRENT_LABEL`, `QBITTORRENT_DIR`, `IMP_CALIBREDB`, `EBOOK_DIR`, and `DOWNLOAD_DIR`.
- The StoryGraph helper successfully normalizes a CSV with `Title,Authors,ISBN,Read Status` into a LazyLibrarian wishlist CSV with columns `Title,Author,isbn`.
- The helper now supports loading `LAZYLIBRARIAN_URL` and `LAZYLIBRARIAN_API_KEY` from an untracked `.env` file, with shell environment intended to take precedence.

References:
- [1] New stack: `/home/ethan/docker/ebooks/docker-compose.yml` with `calibre-web-automated` and `lazylibrarian`.
- [2] New helper: `/home/ethan/docker/ebooks/scripts/storygraph_wishlist_import.py`.
- [3] Tests: `/home/ethan/docker/tests/test-storygraph-wishlist-import.py` ran and passed (`Ran 4 tests ... OK`).
- [4] Backup created at `/mnt/misc_5tb/backups/calibre-metadata/20260704T002416Z`.
- [5] Compose validation passed: `docker compose config` in `/home/ethan/docker/ebooks`.
- [6] Runtime checks passed: `http://127.0.0.1:8083/` returned 200 at login redirect; `http://127.0.0.1:5299/` returned 200 on LazyLibrarian’s authors page.
- [7] Calibre DB integrity check returned `ok` and `books 0`.

## Task 3: Verify runtime and documentation state

Outcome: partial

Preference signals:
- The user asked for implementation, but the rollout also revealed a durable operational preference: keep similar homelab stacks documented in Git/wiki and verify them with compose/config/runtime checks before claiming done.

Key steps:
- Ran `docker compose config` for the new stack successfully.
- Started both services and confirmed they stay up.
- Verified CWA and LazyLibrarian HTTP responses locally.
- Verified the Calibre database integrity.
- Updated generated wiki content for the new stack and runbook.

Failures and how to do differently:
- `./scripts/wiki-sync.sh --check` failed globally because unrelated stale wiki content and missing pages already exist in the repo; this should not be read as a failure of the ebook stack itself.
- The new `ebooks` stack is not fully configured at the application level yet: CWA admin password, SMTP Send to Kindle settings, Kindle recipient, LazyLibrarian API enablement, qBittorrent provider settings, and provider/API keys still need UI/runtime setup.
- The new LazyLibrarian container is only on `ebooks_default`; it does not join `proxy_net`, so no new public proxy route was added.

Reusable knowledge:
- CWA was healthy after first-start initialization and exposed a login redirect on `127.0.0.1:8083`.
- LazyLibrarian initialized its database, installed its optional mods, and served its authors page on `127.0.0.1:5299`.
- The stack’s intended runtime separation is: CWA on `proxy_net` for SMTP relay access, LazyLibrarian on a private network, and no added public ingress.

References:
- [1] `docker compose ps` showed `calibre-web-automated` healthy and `lazylibrarian` running.
- [2] `curl` checks: `cwa 200 http://127.0.0.1:8083/login?next=%2F` and `lazylibrarian 200 http://127.0.0.1:5299/authors`.
- [3] `docker inspect` showed CWA on `proxy_net` and LazyLibrarian on `ebooks_default`.
- [4] `./scripts/wiki-sync.sh --check` reported stale wiki content plus missing unrelated pages; it also expected unrelated existing diffs, so the check is repo-wide noisy, not ebook-specific.
