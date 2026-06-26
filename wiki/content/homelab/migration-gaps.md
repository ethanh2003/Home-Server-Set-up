# Migration Gaps

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## Stack IaC Coverage

| Stack | Compose | Compose tracked | SOPS env | README |
| --- | --- | --- | --- | --- |
| actual-budget | `actual-budget/docker-compose.yml` | yes | yes | no |
| arr-suite | `arr-suite/docker-compose.yml` | yes | yes | no |
| cloudflared | `cloudflared/docker-compose.yml` | yes | yes | no |
| github-runner | `github-runner/docker-compose.yml` | yes | no | no |
| glances | `glances/docker-compose.yml` | yes | no | no |
| home-assistant | `home-assistant/docker-compose.yml` | yes | yes | yes |
| immich | `immich/docker-compose.yml` | yes | yes | no |
| jellyfin | `jellyfin/docker-compose.yml` | yes | yes | no |
| kopia | `kopia/docker-compose.yml` | yes | yes | no |
| linkstack | `linkstack/compose.yml` | no | no | no |
| Minecraft | `Minecraft/docker-compose.yml` | yes | yes | no |
| monitoring-stack | `monitoring-stack/docker-compose.yml` | yes | yes | no |
| nginx-proxy-manager | `nginx-proxy-manager/docker-compose.yml` | yes | no | no |
| obsidian-livesync | `obsidian-livesync/docker-compose.yml` | no | yes | no |
| paperless-ngx | `paperless-ngx/docker-compose.yml` | yes | yes | yes |
| pingvin-share | `pingvin-share/docker-compose.yml` | no | no | yes |
| sftp | `sftp/docker-compose.yml` | yes | yes | no |
| smtp-relay | `smtp-relay/docker-compose.yml` | no | no | yes |
| spotify-stats | `spotify-stats/docker-compose.yml` | no | yes | no |
| stash | `stash/docker-compose.yml` | no | no | no |
| traefik | `traefik/docker-compose.yml` | yes | no | no |
| wiki | `wiki/docker-compose.yml` | yes | yes | yes |

## Reverse Proxy State

- Target state: Traefik owns IaC routing.
- Transition state may still have NPM live on ports `80/443` until Cloudflared cutover is verified.
- Wiki routes are defined for all three wiki hostnames.

## Dirty Worktree Snapshot

```text
A  .github/workflows/wiki-sync.yml
M  .gitignore
M  GEMINI.md
M  STACKS_GEMINI.md
M  STACKS_README.md
M  docs/iac-runbook.md
M  docs/traefik-migration.md
 M generate_nginx_confs.py
 M home-assistant/docker-compose.yml
 D homebox/docker-compose.yml
 D kimai/docker-compose.yml
 M kopia/docker-compose.yml
 D maintenance/docker-compose.yml
 M manage-stacks.sh
 M paperless-ngx/docker-compose.yml
A  scripts/install-wiki-hooks.sh
M  scripts/lib/iac-common.sh
AM scripts/wiki-sync.py
A  scripts/wiki-sync.sh
 D sure-budgeting/docker-compose.yml
M  tests/test-iac-scripts.sh
M  tests/test-secret-hygiene.py
A  tests/test-wiki-sync.py
A  traefik/dynamic/wiki.yml
 D trilium/docker-compose.yml
 M update_npm_db.py
A  wiki/.env.example
A  wiki/.env.sops
A  wiki/README.md
A  wiki/docker-compose.yml
?? actual-budget/actual-auto-sync-src/
?? home-assistant/.env.example
?? home-assistant/README.md
?? home-assistant/docs/
?? home-assistant/scripts/
?? home-assistant/secrets.example.yaml
?? linkstack/
?? obsidian-livesync/docker-compose.yml
?? obsidian-livesync/init-couchdb.sh
?? paperless-ngx/README.md
?? paperless-ngx/docker-compose.yml.bak-smtp-20260624T035400Z
?? paperless-ngx/docker-compose.yml.codex-bak-20260625-135049
?? pingvin-share/
?? smtp-relay/
?? spotify-stats/docker-compose.yml
?? spotify-stats/upstream-your_spotify/
?? spotify-stats/your_spotify_db.corrupt-20260612/
?? stash/
```
