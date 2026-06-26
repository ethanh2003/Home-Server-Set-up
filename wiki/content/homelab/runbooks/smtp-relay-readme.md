# smtp-relay/README.md

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

# SMTP Relay

Docker-local SMTP relay for services that need outbound email.

## Service Endpoint

Containers on `proxy_net` should use:

- Host: `smtp-relay`
- Port: `587`
- TLS/auth from app to relay: off

The relay forwards outbound mail to Google Workspace:

- Upstream: `smtp-relay.gmail.com:587`
- Sender domain: `ethan-herring.com`
- HELO hostname: `smtp.ethan-herring.com`

No Gmail app password is stored in this stack. Google Workspace must trust this
server's public IP for SMTP relay.

Until the Google Workspace relay rule is active, test messages will be accepted
by the Docker relay and then bounced by Google with `Mail relay denied
[24.148.58.137]`.

## Google Workspace Setup

In Google Admin:

1. Go to `Apps -> Google Workspace -> Gmail -> Routing`.
2. Open `SMTP relay service`.
3. Add a relay rule for this Docker host.
4. Allow only sender addresses in `ethan-herring.com`.
5. Authenticate by specified IP address.
6. Add this server public IP: `24.148.58.137`.
7. Require TLS encryption.

Use a real mailbox, group, or alias in Google Workspace for the app sender, such
as `no-reply@ethan-herring.com`.

## Commands

```bash
docker compose -f /home/ethan/docker/smtp-relay/docker-compose.yml up -d
docker compose -f /home/ethan/docker/smtp-relay/docker-compose.yml logs --tail 100
```

## Test From Docker

After the Google Workspace relay rule is active:

```bash
docker run --rm --network proxy_net alpine:3 sh -lc '
  apk add --no-cache curl >/dev/null &&
  printf "Subject: SMTP relay test\r\n\r\nTest from Docker SMTP relay.\r\n" > /tmp/message &&
  curl -v --url smtp://smtp-relay:587 \
    --mail-from no-reply@ethan-herring.com \
    --mail-rcpt you@example.com \
    --upload-file /tmp/message
'
```
