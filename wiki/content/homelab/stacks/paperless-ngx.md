# Stack: paperless-ngx

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.


## IaC Status

- Compose file: `paperless-ngx/docker-compose.yml`
- Compose tracked in Git: yes
- Has SOPS env: yes
- README: yes

## Services

- `broker`
- `webserver`
- `gotenberg`
- `tika`
- `davmail`

## Images

- `docker.io/apache/tika:latest`
- `docker.io/gotenberg/gotenberg:8.25`
- `docker.io/library/redis:8`
- `ghcr.io/paperless-ngx/paperless-ngx:latest`
- `jberrenberg/davmail:latest`

## Operations

```bash
cd /home/ethan/docker/paperless-ngx
docker compose config
docker compose ps
```

## Notes

# Paperless-ngx

## Email

Paperless sends outbound email through the shared Docker SMTP relay:

- Host: `smtp-relay`
- Port: `587`
- Sender: `no-reply@ethan-herring.com`
- App SMTP username/password: [REDACTED]
- TLS/SSL from Paperless to relay: disabled

The relay container forwards to Google Workspace. DavMail remains in this stack
for mailbox/Exchange bridging and is not part of the outbound SMTP relay
migration.

## Verify Email

```bash
docker exec paperless python manage.py shell -c "from django.core.mail import send_mail; send_mail('Paperless SMTP relay test','Test through shared smtp-relay.','no-reply@ethan-herring.com',['no-reply@ethan-herring.com'],fail_silently=False)"
docker logs --since 2m smtp-relay | rg 'paperless|status=sent|status=bounced|Mail relay denied'
```
