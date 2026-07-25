# Stack: spotify-stats

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `spotify-stats/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: yes
- README: yes

## Project Status

- Runtime: not checked
- Project status: in progress
- Last verified: 2026-07-04

## Remaining Tasks

- Finish hardening large Your Spotify imports beyond the current cache and `/tmp/imports` fixes.
- Decide whether the upstream checkout changes should become a local patch, fork, or discardable hotfix.

## Evidence

- Compose file: `spotify-stats/docker-compose.yml`
- Compose tracked in Git: yes
- README: yes
- SOPS env: yes
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

## Services

- `server`
- `web`
- `mongo`

## Images

- `mongo:7`

## Operations

```bash
cd /home/ethan/docker/spotify-stats
docker compose config
docker compose ps
```

## Notes

# Your Spotify

This stack builds Your Spotify from a pinned upstream checkout because the live
server carries three small import-performance fixes.

Bootstrap the build context before the first deployment:

```bash
git clone https://github.com/Yooooomi/your_spotify.git upstream-your_spotify
git -C upstream-your_spotify checkout 641af14a8e32c871b5de652364707987ea1d9df8
git -C upstream-your_spotify apply ../patches/your-spotify-local.patch
docker compose build
docker compose up -d
```

Runtime credentials belong in `.env`; do not commit that file. MongoDB data is
stored in the `spotify-stats_mongo_data` named volume and is covered by the
application-consistent export job.
