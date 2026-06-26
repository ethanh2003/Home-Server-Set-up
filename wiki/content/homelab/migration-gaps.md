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

Committed wiki content omits raw dirty-status output so `wiki-sync --check` is reproducible.
Check live drift from the IaC root with:

```bash
git status --short -- . ':(exclude)wiki/content'
```

Current generated-live status:

```text
omitted; set WIKI_SYNC_INCLUDE_DIRTY=1 for an ad hoc live snapshot
```
