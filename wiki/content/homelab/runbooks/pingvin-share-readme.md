# pingvin-share/README.md

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

# Pingvin Share

Self-hosted file sharing through Pingvin Share X.

## URLs

- https://share.ethanh.online
- https://share.ethan-herring.com
- https://share.pup-percy.com

`share.ethanh.online` is the canonical Pingvin `appUrl`, so generated share links use that hostname even when the app is opened through the other domains.

## Stack

```bash
docker compose -f /home/ethan/docker/pingvin-share/docker-compose.yml up -d
```

Persistent data lives in `/home/ethan/docker/pingvin-share/data`.
Redis data lives in `/home/ethan/docker/pingvin-share/redis-data`.

Configuration is managed through the Pingvin admin UI. Do not mount
`config.yaml` into the container unless you intentionally want to lock admin UI
configuration edits.

## First Setup

1. Open `https://share.ethanh.online`.
2. Create the first admin account while registration is enabled.
3. After the account exists, disable registration in the Pingvin admin settings.

## Email

Pingvin uses the Docker-local SMTP relay:

- Host: `smtp-relay`
- Port: `587`
- Sender: `no-reply@ethan-herring.com`

The relay stack lives in `/home/ethan/docker/smtp-relay` and forwards mail to
Google Workspace for `ethan-herring.com`. Keep Pingvin configuration UI-managed;
do not remount `config.yaml`.

## Redis

Pingvin uses the internal Redis service for shared cache:

- Host: `redis`
- Port: `6379`
- URL: `redis://redis:6379`

The cache settings remain UI-managed in Pingvin's database.

## Proxy

Nginx Proxy Manager routes:

- `101`: `share.ethanh.online -> pingvin-share:3000`, certificate `4`
- `102`: `share.ethan-herring.com -> pingvin-share:3000`, certificate `4`
- `103`: `share.pup-percy.com -> pingvin-share:3000`, certificate `5`

Each route forces HTTPS and sets upload-friendly proxy options:

```nginx
client_max_body_size 0;
proxy_request_buffering off;
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
```

## Verification

```bash
docker compose -f /home/ethan/docker/pingvin-share/docker-compose.yml config
docker inspect pingvin-share --format 'health={{.State.Health.Status}} status={{.State.Status}}'
docker exec pingvin-share curl -fsS http://localhost:3000/api/health
docker exec pingvin-share test ! -e /opt/app/config.yaml
docker exec pingvin-redis redis-cli ping
docker exec npm nginx -t
curl -I https://share.ethanh.online/
curl -I https://share.ethan-herring.com/
curl -I https://share.pup-percy.com/
```
