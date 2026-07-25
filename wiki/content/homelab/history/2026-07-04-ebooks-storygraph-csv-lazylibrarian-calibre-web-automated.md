# 2026-07-04T00-13-04-9UWQ-ebooks_storygraph_csv_lazylibrarian_calibre_web_automated

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f2a78-c070-7a72-819c-f31e2ed1ed28
updated_at: 2026-07-04T20:30:07+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/04/rollout-2026-07-04T00-13-04-019f2a78-c070-7a72-819c-f31e2ed1ed28.jsonl
cwd: /home/ethan

# Ebook stack implemented with StoryGraph CSV-driven wishlist import, LazyLibrarian, Calibre-Web Automated, and an active watcher; final download/search behavior was only partially resolved before the next turn was interrupted.

Rollout context: the user asked to implement a previously approved homelab plan under `/home/ethan/docker/ebooks` to manage ebooks, preserve the existing Calibre library at `/mnt/data_14tb/media/books`, integrate StoryGraph via CSV exports (not API/scraping), use LazyLibrarian and Calibre-Web Automated, and support Send to Kindle through the existing SMTP relay. The environment was the homelab Docker repo in `/home/ethan/docker`.

## Task 1: Design/plan the ebook stack

Outcome: success

Preference signals:
- The user chose `CSV-driven TBR (Recommended)` over unofficial live sync, indicating they prefer a stable, non-scraping StoryGraph workflow.
- The user chose `Auto-download matches`, indicating they want strong matches to proceed automatically rather than requiring manual approval for every wanted item.
- The user chose `Manual button (Recommended)` for Kindle delivery, indicating they prefer Send to Kindle to stay manual rather than fully automatic.
- The user chose to preserve `/mnt/data_14tb/media/books` as the canonical Calibre library, indicating they want existing library data retained and built around rather than replaced.
- The user chose `LazyLibrarian + CWA (Recommended)` over Readarr or a custom bridge, indicating they wanted the stack to reuse existing tools instead of inventing a new app.
- The user chose `LAN/VPN only`, indicating they do not want public exposure for this new stack initially.
- The user chose the existing SMTP relay, indicating the homelab relay should be reused for ebook email delivery.
- The user chose a watched drop folder for StoryGraph CSV ingestion, indicating they prefer a simple file-drop workflow over a manual UI upload or future API automation.

Key steps:
- The environment was inspected for the current Docker stacks, existing LazyLibrarian config, and media/library paths.
- The plan converged on a separate `ebooks/` stack with Calibre-Web Automated plus LazyLibrarian, preserving the existing Calibre DB and using StoryGraph CSV as input.
- The user preferences were gathered one by one and then the resulting plan was presented and later approved.

Failures and how to do differently:
- The first notion of “StoryGraph sync” had to be narrowed; future similar requests should clarify whether the user means CSV export/import, scraping, or API integration before designing.
- Readarr was considered but the user’s choice and the repo context both pointed toward LazyLibrarian, so future similar ebook-manager tasks should check current homelab state first.

Reusable knowledge:
- In this repo, stack directories live under `/home/ethan/docker/<stack>/`, with config kept inside the stack directory and bulk media under `/mnt/data_14tb`.
- The homelab stack inventory and wiki are generated from Git and should be updated when a new stack is added.
- StoryGraph’s practical integration path here is CSV export, not an official live API workflow.

References:
- `/home/ethan/docker/arr-suite/docker-compose.yml` showed the existing qBittorrent/Prowlarr setup the new stack would need to reuse.
- The current Calibre library existed at `/mnt/data_14tb/media/books` with `metadata.db` already present.
- The plan summary included the intended stack shape: separate `ebooks/` stack, preserve Calibre library, LazyLibrarian + CWA, LAN/VPN-only, SMTP relay reuse, watched StoryGraph CSV folder.

## Task 2: Implement the ebook stack and StoryGraph pipeline

Outcome: partial

Preference signals:
- The user asked to “PLEASE IMPLEMENT THIS PLAN,” showing they wanted direct execution once the design was approved.
- The user later said “Continue,” indicating they wanted the agent to keep pushing through blockers rather than stopping at the first partial win.
- The user did not ask to add a new custom ebook app; they wanted the approved stack implemented using existing tools.

Key steps:
- Added `/home/ethan/docker/ebooks/docker-compose.yml` with `calibre-web-automated`, `lazylibrarian`, and a `storygraph-watch` container.
- Added `.env.example`, `README.md`, `scripts/storygraph_wishlist_import.py`, and `tests/test-storygraph-wishlist-import.py`.
- Created and backed up the Calibre metadata before startup: backup at `/mnt/misc_5tb/backups/calibre-metadata/20260704T002416Z`.
- Validated the compose file repeatedly with `docker compose config`.
- Started the stack and verified both UIs responded locally: Calibre-Web Automated on `127.0.0.1:8083` and LazyLibrarian on `127.0.0.1:5299`.
- Confirmed the watcher was running and reading environment from a Docker secret, not exposing the LazyLibrarian API key in rendered compose output.
- Implemented a StoryGraph CSV conversion path that produces a LazyLibrarian-compatible wishlist file and a report; the helper and watcher tests passed.
- Wrote the stack into the generated homelab wiki pages and stack inventory.

Failures and how to do differently:
- LazyLibrarian’s CSV importer path turned out brittle; the user-facing workflow ended up needing an API-based search/add/queue path rather than plain `importCSVwishlist`.
- `docker compose config` will happily render values from `.env`/`env_file`; using a Docker secret file for the API key was necessary to keep secrets out of rendered config.
- LazyLibrarian provider-array booleans were finicky: `writeCFG` and simple file edits did not reliably set `Enabled`; the provider had to be enabled through LazyLibrarian’s provider API (`changeProvider`) and the config file verified afterward.
- The current search flow is functional but not fully “done” because provider rate-limiting and result quality still caused misses/stalls; future similar work should treat provider availability, rate limits, and result quality as separate failure modes.

Reusable knowledge:
- LazyLibrarian API endpoints used successfully here:
  - `writeCFG` for flat settings like `DOWNLOAD_DIR`, `QBITTORRENT_HOST`, and `QBITTORRENT_LABEL`.
  - `changeProvider` for provider-array entries such as Torznab slots.
  - `listNabProviders` and `listProviders` for truth-checking provider state.
  - `forceBookSearch` for wanted-book searching once a Torznab provider is enabled.
- qBittorrent was reachable from LazyLibrarian through the `gluetun` container at `http://gluetun:8080`.
- Prowlarr’s EBookBay indexer initially rate-limited with HTTP 429; adding additional book-capable Prowlarr Torznab providers gave the search more than one route, but the release availability was still mixed.
- The live qBittorrent ebook path that worked is `/data/downloads/ebooks` inside qBittorrent, backed by `/mnt/data_14tb/media/downloads/ebooks` on the host.
- The watcher reads the LazyLibrarian API key from a secret file, not from a rendered environment variable, which avoids secret leakage in `docker compose config` output.

References:
- `ebooks/docker-compose.yml`
- `ebooks/.env.example`
- `ebooks/README.md`
- `ebooks/scripts/storygraph_wishlist_import.py`
- `tests/test-storygraph-wishlist-import.py`
- `wiki/content/homelab/stacks/ebooks.md`
- `wiki/content/homelab/runbooks/ebooks-readme.md`
- `wiki/content/homelab/index.md`
- `wiki/content/homelab/migration-gaps.md`
- LazyLibrarian API state confirmed by `listNabProviders` after enabling provider slots: Prowlarr Torznab providers were present and enabled.
- `docker compose exec -T lazylibrarian ...` showed `wanted_books 9` and later qBittorrent showed 1–2 ebook torrents under the `ebooks` category.
- The stack reached a real download state: LazyLibrarian marked `Dune` and `Lightlark` as `Snatched`, and qBittorrent showed at least one active torrent saving to `/data/downloads/ebooks`.

## Task 3: Continue debugging the ebook search/download path

Outcome: partial

Preference signals:
- When the rollout hit a blocker, the user said “Continue,” indicating they wanted the agent to keep iterating rather than stopping after the first partial result.

Key steps:
- Probed the provider path and confirmed LazyLibrarian could reach Prowlarr and qBittorrent through `gluetun`.
- Discovered the initial Torznab provider state was still reported as disabled until explicitly enabled through the LazyLibrarian API.
- Enabled multiple Prowlarr book-capable Torznab providers: EBookBay, Internet Archive, BitSearch, and Torrent Downloads.
- Confirmed LazyLibrarian could now execute `forceBookSearch` and that it started queueing and snatching books.
- Verified at least one torrent (`frank-herbert-dune-01-2020`) was added to qBittorrent and later another torrent for `Lightlark` was actively downloading.
- Confirmed the ebook torrent path used qBittorrent category `ebooks` and save path `/data/downloads/ebooks`.

Failures and how to do differently:
- The first provider configuration only yielded `No search methods set` or `No nzb providers are available`; the real issue was that provider-array entries were not actually enabled.
- Prowlarr EBookBay sometimes returned HTTP 429, so depending on a single provider was not robust enough.
- Even after successful snatches, one torrent stalled at 0% while another progressed; future similar work should distinguish “snatched,” “downloading,” and “completed/imported” as separate verification stages.
- The rollout was interrupted before confirming a full post-processing/import completion, so the final state should be treated as partial, not fully done.

Reusable knowledge:
- LazyLibrarian’s search logic reported `Searching 1 provider ['nzb'] for 9 eBooks` until provider mode/settings were corrected; once multiple providers were enabled, it searched more providers and began snatching books.
- Provider enablement had to be done with the API call `changeProvider` using the internal names `Torznab_0`, `Torznab_1`, etc., not just by editing the config file.
- `listNabProviders` was the best truth source for what LazyLibrarian actually considered enabled.
- A direct Prowlarr/Torznab test for Dune produced HTTP 429 from one indexer endpoint, proving the provider was reachable but rate-limited.

References:
