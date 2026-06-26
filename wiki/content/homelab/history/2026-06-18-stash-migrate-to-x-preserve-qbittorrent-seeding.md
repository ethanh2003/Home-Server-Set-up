# 2026-06-18T22-19-02-0g8R-stash_migrate_to_x_preserve_qbittorrent_seeding

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019edcd0-f46e-7fb3-b02d-d34e1c2ff465
updated_at: 2026-06-18T22:27:51+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/18/rollout-2026-06-18T22-19-02-019edcd0-f46e-7fb3-b02d-d34e1c2ff465.jsonl
cwd: /home/ethan/docker
git_branch: main

# Stash migration from `porn` to `x` while keeping qBittorrent seeding

Rollout context: The user first asked where the Stash compose file was, then asked to migrate Stash from the old `porn` media root to `x` so they would not have to delete in two places. The critical constraint became preserving qBittorrent seeding; the user briefly considered stopping qBittorrent, then reversed that and explicitly said to continue qBittorrent and begin the Stash update. The work happened in `/home/ethan/docker`.

## Task 1: Locate and restore Stash compose, then migrate Stash to `x`

Outcome: success

Preference signals:
- The user said they "cant find the stash compose" -> in similar cases, look for the compose file in the live service path and validate against the running container, not only repo files.
- The user said they wanted to "migrate stash to X, while maintaing the file structure and database linked to the porn folder, so i don't have to delete in 2 places" -> they care about keeping Stash's library structure intact and avoiding duplicate cleanup across folders.
- When the qBittorrent constraint emerged, the user clarified "yes, but i also need qbittorent to stay connected and seeding" -> future migrations should treat torrent seeding as a first-class constraint, not an afterthought.
- The user later said "actually i am just going to stop qbittorrent, i can live with a ratio drop" and then reversed again with "continue qbittorrent its fine now, and update stash, begin" -> the effective default is to keep qBittorrent running if possible, but user may temporarily relax that if needed; confirm the final choice before destructive changes.

Key steps:
- Found that the active Stash container already had Compose labels pointing to `/home/ethan/docker/stash/docker-compose.yml`, even though the file was missing.
- Recreated `/home/ethan/docker/stash/docker-compose.yml` from the live container’s actual image, port, and mounts.
- Confirmed the old Stash library root was `/mnt/data_14tb/media/porn` and qBittorrent already used `/mnt/data_14tb/media/x` for its current seeded downloads.
- Backed up Stash config/database to `/home/ethan/docker/stash/backups/config-20260618-222511.tar.gz` before moving anything.
- Stopped only Stash, moved the top-level contents of `/mnt/data_14tb/media/porn` into `/mnt/data_14tb/media/x`, updated the compose mount to `/mnt/data_14tb/media/x:/data`, then restarted Stash.
- Verified Stash via `docker compose config`, `curl http://127.0.0.1:9999/`, Stash GraphQL, `docker inspect`, and a filesystem existence check on sampled scene paths.

Failures and how to do differently:
- The first attempt to inspect skills used a bad path; the agent corrected it and continued.
- `jq` and `sqlite3` were not installed on the host; the agent switched to Python for JSON and SQLite inspection instead of trying to install tools.
- The first GraphQL query used the wrong Stash schema shape and returned validation errors; the agent retried with the current query shape and confirmed the API was live.
- Raw DB path verification showed many stale or legacy records that did not resolve, especially under `.stash_metadata`, `Delete`, and some older `Uncategorized`/`Studios` entries. The agent did not blindly rewrite the database; instead it verified through the live API and filesystem and avoided risky database edits.

Reusable knowledge:
- The live Stash container labels can reveal the expected Compose file path even when the file is missing: `com.docker.compose.project.config_files=/home/ethan/docker/stash/docker-compose.yml` and `com.docker.compose.project.working_dir=/home/ethan/docker/stash`.
- The working Stash service was `stashapp/stash:latest`, port `9999:9999`, with mounts `/mnt/data_14tb/media/x:/data`, `/mnt/data_14tb/media/.stash_metadata:/metadata`, and `./config:/root/.stash`.
- qBittorrent in `arr-suite` is mounted at `/mnt/data_14tb/media` as `/data`, so moving Stash from `porn` to `x` did not break torrent path consistency for the current seeding tree.
- qBittorrent config showed category `X` with `save_path: "/data/x/downloads"`, and the live API reported 23 `X` torrents seeding from that path plus 105 torrents at `/data/downloads`.
- For Stash DB validation, the schema uses `folders.path` plus `files.basename`; there is no `files.path` column in this schema version.
- Stash GraphQL on this version accepted `findScenes(filter: { per_page: 20 sort: "updated_at" direction: DESC }) { count scenes { id files { path } } }`, and sampled `files.path` values all resolved under the new `/mnt/data_14tb/media/x` mount.

References:
- [1] Deleted old compose source found in git history: `stash-komga/docker-compose.yml` from commit `486df64cec8abc6f63769a7b83af249348ff21bb`.
- [2] Recreated compose file content:
  - `image: stashapp/stash:latest`
  - `container_name: stash`
  - `restart: unless-stopped`
  - `ports: ["9999:9999"]`
  - `volumes: ["/mnt/data_14tb/media/x:/data", "/mnt/data_14tb/media/.stash_metadata:/metadata", "./config:/root/.stash"]`
- [3] Backup artifact: `/home/ethan/docker/stash/backups/config-20260618-222511.tar.gz`
- [4] Final verification command produced `VERIFICATION_PASSED` with these checks:
  - `compose_config_exit 0`
  - `compose_has_x_mount True`
  - `stash_http_status 200`
  - `stash_scene_count 17056`
  - `sample_files_checked 26`
  - `sample_missing_files 0`
  - `stash_inspect_exit 0` and mount mapping `/mnt/data_14tb/media/x=>/data`
  - `qbittorrent_state running healthy`
  - `old_porn_dir_empty True`
