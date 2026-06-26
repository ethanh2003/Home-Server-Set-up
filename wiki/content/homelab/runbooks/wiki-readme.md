# wiki/README.md

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

# Homelab Wiki

Wiki.js is the UI for homelab documentation. Git remains the source of truth:
edit files in `/home/ethan/docker`, regenerate `wiki/content/`, then publish to
Wiki.js.

## URLs

- https://wiki.ethan-herring.com
- https://wiki.pup-percy.com
- https://wiki.ethanh.online

## First Setup

```bash
cd /home/ethan/docker
./scripts/secrets-decrypt.sh --stack wiki
cd wiki
docker compose up -d
```

Open one wiki URL, create the first local Wiki.js admin user, then create a
Wiki.js API key in the admin UI. Put that API key in `wiki/.env.sops` as
`WIKIJS_API_TOKEN`, decrypt again, and run:

```bash
cd /home/ethan/docker
./scripts/wiki-sync.sh --backfill
WIKIJS_API_TOKEN=[REDACTED] ./scripts/wiki-sync.sh --backfill --publish
```

## Content Model

- Generated Git source lives in `wiki/content/`.
- `/homelab/index` is the landing page.
- `/homelab/stacks/<stack>` is the current focus page for each stack.
- `/homelab/history/*` contains safe backdated history.
- `/homelab/migration-gaps` tracks incomplete IaC coverage.

Manual wiki edits are not authoritative. If a page should persist, update Git
and republish.

## MCP

The `wiki-mcp` service is profile-gated because MCP clients usually run stdio
servers directly. After the API key exists, Codex or another MCP client can use
the existing `wikijs-mcp` package with:

```bash
uvx wikijs-mcp
```

Environment:

- `WIKIJS_URL=https://wiki.ethan-herring.com`
- `WIKIJS_API_KEY=[REDACTED] API key>`

## Validation

```bash
docker compose config
./scripts/wiki-sync.sh --check
./scripts/iac-validate.sh
```
