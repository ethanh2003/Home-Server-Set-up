# Stack: arr-suite

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `arr-suite/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: yes
- README: no

## Services

- `gluetun`
- `qbittorrent`
- `prowlarr`
- `radarr`
- `sonarr`

## Images

- `lscr.io/linuxserver/prowlarr:latest`
- `lscr.io/linuxserver/qbittorrent:latest`
- `lscr.io/linuxserver/radarr:latest`
- `lscr.io/linuxserver/sonarr:latest`
- `qmcgaw/gluetun:latest`

## Operations

```bash
cd /home/ethan/docker/arr-suite
docker compose config
docker compose ps
```

## Notes

No stack README exists yet.
