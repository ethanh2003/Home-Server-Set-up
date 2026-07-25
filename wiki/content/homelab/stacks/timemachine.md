# Stack: timemachine

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `timemachine/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: no
- README: yes

## Project Status

- Runtime: not checked
- Project status: operational
- Last verified: 2026-07-04

## Remaining Tasks

- If remote Macs cannot route to `192.168.1.230`, advertise and approve a Tailscale route for `192.168.1.230/32`.
- Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.

## Evidence

- Compose file: `timemachine/docker-compose.yml`
- Compose tracked in Git: yes
- README: yes
- SOPS env: no
- Git status for stack path: omitted
- Live runtime state is monitored in Prometheus and omitted from deterministic wiki output.

## Services

- `timemachine`

## Images

- `mbentley/timemachine:smb`

## Operations

```bash
cd /home/ethan/docker/timemachine
docker compose config
docker compose ps
```

## Notes

# Time Machine

Dockerized macOS Time Machine target backed by the 5TB HDD at `/mnt/misc_5tb`.

## Layout

- Stack: `/home/ethan/docker/timemachine`
- Backup data: `/mnt/misc_5tb/backups/time-machine`
- SMB share: `TimeMachine`
- SMB user: `timemachine`
- Container LAN IP: `192.168.1.230`
- Shared Time Machine size limit: `1500 G`

The container uses a Docker macvlan network so it has its own LAN identity and does not conflict with the host Samba and Avahi services.

## Manage

```bash
cd /home/ethan/docker/timemachine
docker compose config
docker compose up -d
./scripts/create-macvlan-shim.sh
docker compose ps
```

The macvlan shim gives the Docker host a route to the container IP for local health checks. It is also installed as `timemachine-macvlan-shim.service` so the route comes back after reboot.

To read the Time Machine password:

```bash
cd /home/ethan/docker/timemachine
sed -n 's/^PASSWORD=[REDACTED]' .env
```

## Mac Setup

On each Mac, open Time Machine settings and choose the `TimeMachine` network disk. If discovery does not show it, connect manually:

```text
smb://192.168.1.230/TimeMachine
```

Use username `timemachine` and the password from `/home/ethan/docker/timemachine/.env`.

## Tailscale

For remote access, connect manually to:

```text
smb://192.168.1.230/TimeMachine
```

If the Mac cannot route to `192.168.1.230` over Tailscale, advertise and approve a route for `192.168.1.230/32` as a follow-up change.
