# 2026-07-06T21-15-39-GODs-immich_outside_lan_redirect_loop_fix

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f3949-6729-7d33-a9e7-964afd614ef6
updated_at: 2026-07-06T21:18:03+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/06/rollout-2026-07-06T21-15-39-019f3949-6729-7d33-a9e7-964afd614ef6.jsonl
cwd: /home/ethan/Documents/Codex/2026-07-06-immich-ethanh-online-isnt-working-outside

# Immich public access worked on LAN but failed off-LAN because NPM was forcing HTTPS inside a Cloudflare tunnel path.

Rollout context: The user reported `Immich.ethanh.online isnt working outside of lan`. The host already had Immich, Nginx Proxy Manager (NPM), and cloudflared running; the debugging had to distinguish a LAN/local path from the public Cloudflare path.

## Task 1: Diagnose and fix `immich.ethanh.online` outside-LAN access

Outcome: success

Preference signals:
- The user gave a terse outage report (`"Immich.ethanh.online isnt working outside of lan"`), which fits the established homelab pattern that the next agent should immediately do live incident response rather than ask for a redesign or more context.
- The previous homelab memory strongly framed public-host fixes as edge-to-backend debugging first; this rollout followed that pattern and confirms it is appropriate for similar incidents.

Key steps:
- Checked the live stack: Immich containers were healthy, NPM was up, and cloudflared was running.
- Verified that `https://immich.ethanh.online/` returned `200` from the local machine when it resolved to the LAN IP `192.168.1.113`.
- Inspected Cloudflare tunnel logs and found `immich.ethanh.online` was routed to `http://npm:80`.
- Verified the live NPM DB and generated vhost agreed on Immich routing: proxy host `3` mapped `immich.ethanh.online` and `immich.ethan-herring.com` to `immich_server:2283`, and proxy host `108` mapped `immich.pup-percy.com` to the same upstream.
- Reproduced the off-LAN path by forcing curl to Cloudflare edge IPs; the response was a repeating `301` back to the same HTTPS URL.
- Confirmed the loop source: the Immich NPM vhost had `ssl_forced` enabled, so NPM’s `force-ssl` logic redirected requests even though Cloudflare Tunnel was already presenting the public HTTPS endpoint.
- Fixed it by setting `ssl_forced=0` for the Immich proxy hosts in the live NPM SQLite DB, updating `npm-migration-inventory.yml` to prevent drift, and regenerating the NPM config.
- Validation after the fix: `nginx -t` passed, Cloudflare-edge curl to `https://immich.ethanh.online/` returned `HTTP/2 200`, and `/api/server/about` reached Immich and returned `Authentication required` as expected without a session.

Failures and how to do differently:
- The first local `curl` could not reveal the bug because the host resolver pointed `immich.ethanh.online` at the LAN IP, bypassing the off-LAN behavior entirely.
- `dig` was unavailable on the host, so DNS checks had to use `cloudflare-dns.com/dns-query` instead.
- A plain host-side test against the hostname was misleading until Cloudflare edge IPs were forced with `--resolve`.
- The initial assumption that the issue might be upstream health was wrong; the upstream Immich server was healthy and reachable from inside NPM.

Reusable knowledge:
- In this homelab, `immich.ethanh.online` can resolve locally to `192.168.1.113`, so LAN curl tests may bypass Cloudflare and hide public-edge problems.
- When Cloudflare Tunnel sends a hostname to `http://npm:80`, NPM `ssl_forced=true` can create an HTTPS redirect loop at the edge even if the upstream app is healthy.
- The practical routing truth source remains both the NPM SQLite DB and the generated vhost files under `nginx-proxy-manager/nginx_config/data/nginx/proxy_host/`.
- Immich proxy host `3` uses `immich_server:2283` for `immich.ethanh.online` and `immich.ethan-herring.com`; proxy host `108` uses the same upstream for `immich.pup-percy.com`.
- Backups were created before mutation under `/home/ethan/docker/nginx-proxy-manager/backups/`.

References:
- [1] `curl -kIsv --max-time 12 https://immich.ethanh.online/` initially resolved to `192.168.1.113` and returned `HTTP/2 200` from the LAN path.
- [2] `docker logs --tail=120 cloudflared_tunnel` showed the tunnel config entry: `{"hostname":"immich.ethanh.online","service":"http://npm:80"}`.
- [3] NPM DB query for Immich hosts returned proxy host `3` with `domain_names=["immich.ethanh.online", "immich.ethan-herring.com"]`, `forward_host=immich_server`, `forward_port=2283`, `certificate_id=4`, `ssl_forced=1` before the fix.
- [4] Generated vhost `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/nginx/proxy_host/3.conf` contained `set $server "immich_server";`, `set $port 2283;`, and `server_name immich.ethanh.online immich.ethan-herring.com;`.
- [5] The off-LAN repro was `curl -kIL --max-time 20 --max-redirs 5 --resolve immich.ethanh.online:443:104.21.0.179 https://immich.ethanh.online/`, which looped with repeated `HTTP/2 301` responses until `curl: (47) Maximum (5) redirects followed`.
- [6] Final verification: `curl -kIs --resolve immich.ethanh.online:443:104.21.0.179 https://immich.ethanh.online/` returned `HTTP/2 200`, and `curl ... /api/server/about` returned `{"message":"Authentication required"}`.
