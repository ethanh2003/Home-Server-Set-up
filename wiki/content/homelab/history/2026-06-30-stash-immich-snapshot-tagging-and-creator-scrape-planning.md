# 2026-06-30T13-55-57-u2Ot-stash_immich_snapshot_tagging_and_creator_scrape_planning

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f18d0-af49-7e51-88c1-fc010f663c61
updated_at: 2026-06-30T18:23:19+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/30/rollout-2026-06-30T13-55-57-019f18d0-af49-7e51-88c1-fc010f663c61.jsonl
cwd: /home/ethan

# Stash/Immich media-organization planning, aborted snapshot import, and creator-scrape discussion

Rollout context: Work centered on `/home/ethan` homelab stacks, especially `/home/ethan/docker/stash` and `/home/ethan/docker/immich`. The user first asked to optimize Stash setup and investigate why metadata appears in search results on `stash.ethanh.online`; later the thread shifted to linking Immich media into Stash in a way that is easy to filter/tag; then it was aborted and rolled back at the user’s request. A final question asked whether OF/Twitter performer profiles can be scraped.

## Task 1: Stash optimization / metadata pollution / automation plan

Outcome: partial

Preference signals:
- The user said: "I need to optomize my stash setup, ask questions and query stash's config and setup to create a improvement plan" and later "everything except for 4. i need daily scans to also generate the previews, hashes, thumbnails, etc but dont care which one, honestl'y would be nicer if it could watch the file system and run on update" -> they wanted a concrete plan grounded in live config, but with daily generation preserved and ideally watcher-triggered updates.
- The user accepted a hybrid model where Stash Scheduler stays as the nightly safety net and FileMonitor can watch the filesystem, but they preferred the watcher to be lighter and not necessarily full-generation driven.

Key steps:
- The agent queried the live Stash stack, config, plugin settings, NPM, and logs; it found Stash running `stashapp/stash:latest` with `/data` bound to `/mnt/data_14tb/media/x` and metadata under `/mnt/data_14tb/media/.stash_metadata`.
- The agent found a large amount of stale database linkage to `/data/.stash_metadata` and confirmed that the current config already excluded `.stash_metadata/`, so the issue was stale library state rather than a missing filter alone.
- The agent also confirmed duplicate NPM proxy rows for Stash and that the live generated NPM vhost still pointed at the Docker service name `stash`.
- The user later shifted the plan from “just live watcher vs nightly scans” to a hybrid: daily Stash Scheduler plus host-side FileMonitor for immediate updates.

Failures and how to do differently:
- The initial suggested “version pinning” item was explicitly rejected by the user and should not be treated as part of the default plan for similar requests.
- FileMonitor’s own scheduler should not be assumed to be the primary automation path; the user preferred daily generation to remain in Stash Scheduler, with watcher-driven updates as a complement.
- FileMonitor cannot be started from inside Docker; the log explicitly said this is unsupported and it must run on the host.

Reusable knowledge:
- In this homelab, Stash’s practical routing truth source is both NPM’s SQLite DB and generated vhost files; for Stash itself, the active service is under `/home/ethan/docker/stash` with bind mounts for `/data`, `/metadata`, and `/root/.stash`.
- Stash GraphQL schema on this version includes `metadataScan`, `metadataGenerate`, `metadataClean`, `metadataCleanGenerated`, `bulkImageUpdate`, `bulkSceneUpdate`, `tagCreate`, `tagUpdate`, and `bulkTagUpdate`; `ScanMetadataInput` supports flags like `scanGenerateCovers`, `scanGeneratePreviews`, `scanGenerateImagePreviews`, `scanGenerateSprites`, `scanGeneratePhashes`, `scanGenerateImagePhashes`, `scanGenerateThumbnails`, and `scanGenerateClipPreviews`.
- Stash currently only had the built-in `Freeones` performer scraper registered; no OF/Twitter scraper was already available.

References:
- Stash compose: `/home/ethan/docker/stash/docker-compose.yml`
- Stash config: `/home/ethan/docker/stash/config/config.yml`
- NPM vhost: `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/nginx/proxy_host/10.conf`
- NPM DB rows: active row `id=10` with `forward_host=stash`, stale duplicate row `id=72` with `forward_host=192.168.1.102`
- GraphQL introspection confirmed `metadataScan`, `metadataGenerate`, `bulkImageUpdate`, `bulkSceneUpdate`, `tagCreate`, `bulkTagUpdate`

## Task 2: One-time Immich admin snapshot into Stash with review tags

Outcome: fail

Preference signals:
- The user chose: "Admin account, include videos" when asked which Immich account to use, then chose "Copy/export snapshot" and then "One-time snapshot" when asked about cadence.
- The user chose: "Timeline only (Recommended)" for Immich asset filtering.
- The user then explicitly said: "We need to ensure these are added to stash in an easy to filter/tag way so i can work through them easier" and chose the "Queue + media tags (Recommended)" tagging strategy.
- The user later interrupted with: "stop and delete what you did,, i need to clear out some images" -> the partial import should be treated as aborted and removed, not preserved as a completed workflow.

Key steps:
- The agent inspected the live Immich stack under `/home/ethan/docker/immich`, confirmed the database uses `asset` and `user` tables, and identified the admin account’s UUID and counts.
- It generated a manifest of 10,207 active timeline assets from Immich admin: 7,138 images and 3,069 videos.
- It backed up the Stash DB/config, stopped the host watcher service, and started a manifest-driven copy into `/mnt/data_14tb/media/x/immich/admin-snapshot`.
- The copy progressed to 1,250/10,207 before the user interrupted; the partial tree reached about 2.7 GiB / 3,093 files.
- On rollback, the agent killed the copy process, removed `/mnt/data_14tb/media/x/immich/admin-snapshot`, deleted the temp run directory, restarted the watcher, and verified Stash had 0 image/scene records under `/data/immich/admin-snapshot`.

Failures and how to do differently:
- The copy operation should be treated as unsafe to continue once the user interrupts for cleanup; abort immediately and remove partial destination files.
- The temporary run directory and partial snapshot path must both be removed on rollback; Stash scan/tagging had not started, so no metadata cleanup in Stash was needed.
- The watcher service was hung in `deactivating` and needed to be SIGKILLed before cleanup could finish; plain `systemctl stop` was not sufficient in this run.

Reusable knowledge:
- Immich host data lives at `/mnt/data_14tb/Images/immich/library/admin`; Stash cannot see that path directly without a new mount.
- Immich schema on this setup uses `asset.originalPath`, `asset.ownerId`, `asset.deletedAt`, `asset.status`, and `asset.visibility`.
- The admin account had 7,138 active timeline images and 3,069 active timeline videos; hidden videos were a separate 18-item set.
- Stash can target-import and later filter work items by tags plus `organized=false`; the plan discussed tags like `Immich Admin Snapshot`, `Needs Review`, `Immich Image`, and `Immich Video`.

References:
- Immich compose: `/home/ethan/docker/immich/docker-compose.yml`
- Immich host mount: `/mnt/data_14tb/Images/immich`
- Stash import destination that was created then removed: `/mnt/data_14tb/media/x/immich/admin-snapshot`
- Backup/run dir created then removed: `/home/ethan/docker/stash/backups/immich-admin-snapshot-20260630T152703Z`
- Watcher service: `stash-update-watcher.service`
- Manifest counts verified: `manifest_rows=10207`, `IMAGE=7138`, `VIDEO=3069`, `missing_source_count=0`, `outside_admin_library_count=0`

## Task 3: OF / Twitter creator profile scraping feasibility

Outcome: uncertain

Preference signals:
- The user said: "is it possible to add something that scrapes for OF or twitter performer profiles?" and clarified: "most of my downloads are OF scrapes or twitter creators which are hard to get data for" -> they want tooling that handles weak/public metadata for creator-heavy downloads.
- The user’s emphasis suggests they care less about perfect public database coverage and more about making creator-heavy downloads usable in Stash despite sparse metadata.

Key steps:
- The agent checked the local Stash plugin/scraper state and found only the built-in `Freeones` performer scraper registered.
- It inspected the Stash plugin code and local download/library paths and found that the library contains a lot of creator-named folders and a few sidecar files, but not a robust metadata sidecar ecosystem yet.
- Based on that, the agent concluded that a source-aware enrichment workflow is more realistic than a single scraper.

Failures and how to do differently:
- Do not assume Stash already has OF/Twitter scrapers just because it can scrape performers generally; on this install it did not.
- For OF/Twitter-heavy libraries, live scraping alone is likely fragile; preserve source metadata and infer handles/creator identities from folder/file naming and sidecars whenever possible.

Reusable knowledge:
- Stash currently had only `builtin_freeones` registered for performer scraping (`urls`: `freeones.xxx`, `freeones.com`, `supported_scrapes`: `NAME`, `URL`).
- Existing library structure already includes creator-like folder naming under `/mnt/data_14tb/media/x/downloads` and some sidecars such as `info.json`/`list.txt`, which makes a future enrichment tool viable.
- A practical path would be a Stash creator-enrichment workflow: preserve source URLs/handles in sidecars for future imports, infer handles from folders/files for existing items, and add tags like `Source: OnlyFans`, `Source: Twitter/X`, `Needs Review`, etc.

References:
- `listScrapers(types: [PERFORMER])` returned only `builtin_freeones`
- Local sidecars/folder examples observed under `/mnt/data_14tb/media/x`: `info.json`, `list.txt`, creator-named directories like `.../[Onlyfans] ...`, `.../onlyfans`, `.../twitter`-style creator paths were discussed as targets for inference
- Relevant plugin clue: `stash-downloader` supports performer auto-creation and filename templating, but not a built-in OF/Twitter performer scraper
