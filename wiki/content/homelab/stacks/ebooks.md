# Stack: ebooks

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `ebooks/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: yes

## Project Status

- Runtime: not checked
- Project status: in progress
- Last verified: 2026-07-04

## Remaining Tasks

- Finish first-run application configuration in Calibre-Web Automated and LazyLibrarian.
- Verify StoryGraph watcher behavior after adding a real export CSV.
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

## Evidence

- Compose file: `ebooks/docker-compose.yml`
- Compose tracked in Git: yes
- README: yes
- SOPS env: no
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

## Services

- `calibre-web-automated`
- `lazylibrarian`
- `storygraph-watch`

## Images

- `crocodilestick/calibre-web-automated:latest`
- `lscr.io/linuxserver/lazylibrarian:latest`
- `python:3.12-alpine`

## Operations

```bash
cd /home/ethan/docker/ebooks
docker compose config
docker compose ps
```

## Notes

# Ebook Stack

LAN/VPN-only ebook management stack for the existing Calibre library at
`/mnt/data_14tb/media/books`.

## Services

- `calibre-web-automated`: web library UI, CWA ingest processing, and manual
  Send to Kindle.
- `lazylibrarian`: wanted-book tracking, provider searches, qBittorrent handoff,
  and ebook post-processing.

Nginx Proxy Manager routes:

- `calibre.ethanh.online`
- `calibre.ethan-herring.com`
- `lazylibrarian.ethanh.online`
- `lazylibrarian.ethan-herring.com`

## Paths

- Calibre library: `/mnt/data_14tb/media/books`
- CWA ingest: `/data/staging/ebooks/cwa-ingest`
- LazyLibrarian downloads: `/mnt/data_14tb/media/downloads/ebooks`
- StoryGraph CSV drop folder: `imports/storygraph/`
- Import reports: `reports/`

CWA upstream warns not to download directly into `/cwa-book-ingest`; completed
files should be moved there after the downloader finishes.

## First Start

```bash
cd /home/ethan/docker/ebooks
cp .env.example .env
mkdir -p config/calibre-web-automated config/lazylibrarian imports/storygraph reports
mkdir -p /data/staging/ebooks/cwa-ingest /mnt/data_14tb/media/downloads/ebooks
docker compose config
docker compose up -d
```

Before the first `up -d`, back up the Calibre metadata files:

```bash
mkdir -p /mnt/misc_5tb/backups/calibre-metadata
ts=$(date -u +%Y%m%dT%H%M%SZ)
cp -a /mnt/data_14tb/media/books/metadata.db* /mnt/misc_5tb/backups/calibre-metadata/$ts/
```

## StoryGraph CSV Import

Drop a StoryGraph export CSV into `imports/storygraph/`, then run:

```bash
./scripts/storygraph_wishlist_import.py
```

The script writes a LazyLibrarian-compatible wishlist CSV to
`imports/storygraph/lazylibrarian-eBook-wishlist.csv` and a review report to
`reports/storygraph-wishlist-report.md`.

The `storygraph-watch` container polls the drop folder every 60 seconds and runs
the same import automatically when the newest CSV changes. It stores the last
processed source fingerprint in `state/storygraph-watch.state`.

To ask LazyLibrarian to import wanted books via its API, set
`LAZYLIBRARIAN_API_KEY` in the shell or untracked `.env`, then run:

```bash
./scripts/storygraph_wishlist_import.py --import-lazylibrarian --search
```

By default, the script searches LazyLibrarian by title/author, adds strong
matches by BookID, queues them as `Wanted`, runs `forceBookSearch` when
`--search` is set, and appends unmatched or failed matches to the report. This
avoids LazyLibrarian's CSV importer getting stuck after a prior failed import
leaves author-only records behind. The generated CSV still uses
`Title,Author,ISBN13` and can be imported manually if needed:

```bash
./scripts/storygraph_wishlist_import.py --import-lazylibrarian --lazylibrarian-import-mode csv --search
```

The script does not store StoryGraph credentials.

For automatic LazyLibrarian API import, enable API access in LazyLibrarian, set
`LAZYLIBRARIAN_API_KEY`, then set:

```env
STORYGRAPH_IMPORT_LAZYLIBRARIAN=true
STORYGRAPH_SEARCH_AFTER_IMPORT=true
```

## Initial UI Configuration

In Calibre-Web Automated:

- Log in with the upstream default admin account, then change the password.
- Enable uploads if needed.
- Configure SMTP for Send to Kindle using `smtp-relay:587` on `proxy_net`.
- Leave Send to Kindle as a manual action.

In LazyLibrarian:

- Enable API access and put the API key only in untracked `.env` or your shell.
- Set qBittorrent as the download client at `host.docker.internal:8080`.
- Use a dedicated qBittorrent category such as `ebooks`.
- Set Prowlarr/Torznab providers through `host.docker.internal:9696`.
- Set the base book folder to `/books`.
- Use `/downloads` for completed downloads and `/cwa-book-ingest` only for
  completed files ready for CWA import.
