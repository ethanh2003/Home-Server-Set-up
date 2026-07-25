# 2026-07-23T15-09-21-mpwj-smtp_relay_obsidian_note_lan_only_exposure

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f8f86-27d4-71b1-8054-b50b0a01a937
updated_at: 2026-07-23T15:21:25+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/23/rollout-2026-07-23T15-09-21-019f8f86-27d4-71b1-8054-b50b0a01a937.jsonl
cwd: /home/ethan

# The user tried to get the shared SMTP relay documented, then asked to expose it to the LAN only; the rollout mostly verified current network state and found the service was still internal-only.

Rollout context: working directory was `/home/ethan`. The SMTP relay stack lived in `/home/ethan/docker/smtp-relay`, with Obsidian notes in `/data/Obsidian/Main/Homelab/Projects/smtp-relay.md`. The user first asked to "write my smtp server info into obsidian" and then clarified they wanted the login included, then later corrected the intent to leave the needed info for another LAN software client, and finally asked: "can you expose it to lan only? i can add it to npm if the secure domain would help".

## Task 1: Document SMTP relay info in Obsidian

Outcome: partial

Preference signals:

- The user first asked to "write my smtp server info into obsidian" and then pushed on the login/credential details, indicating they wanted the Obsidian note to be practical for future setup, not just descriptive.
- When the assistant only wrote that no login file existed, the user corrected: "you were meant to leaeve the needed info for me to connect to the stmp from another software on my lan" -> future notes should prioritize client connection details for other LAN software, not just internal relay metadata.

Key steps:

- Searched the vault and docker tree for smtp-related notes and configs.
- Found `/home/ethan/docker/smtp-relay/docker-compose.yml`, `/home/ethan/docker/smtp-relay/README.md`, and `/data/Obsidian/Main/Homelab/Projects/smtp-relay.md`.
- Updated the Obsidian note to explicitly say the relay was internal-only on the Docker network, with no published LAN port.

Failures and how to do differently:

- The first note update focused on where credentials were not stored, which did not satisfy the user's goal of connecting other software to the relay.
- Future work should extract the actual client-facing settings first: host, port, auth requirement, TLS mode, and whether the service is reachable on the LAN at all.

Reusable knowledge:

- The relay stack does not store an app password in the stack.
- The docker compose and README showed the in-container client contract is `host=smtp-relay`, `port=587`, no app-side SMTP auth, no TLS from app to relay, and the relay forwards upstream to `smtp-relay.gmail.com:587`.
- The Obsidian note path used for this homelab stack was `/data/Obsidian/Main/Homelab/Projects/smtp-relay.md`.

References:

- `/home/ethan/docker/smtp-relay/docker-compose.yml`
- `/home/ethan/docker/smtp-relay/README.md`
- `/data/Obsidian/Main/Homelab/Projects/smtp-relay.md`
- Updated note text: "Current deployment is internal-only on the Docker network; port `587` is not published to the LAN."

## Task 2: Assess LAN-only exposure for smtp-relay

Outcome: partial

Preference signals:

- The user asked: "can you expose it to lan only?" and added "i can add it to npm if the secure domain would help" -> future default should consider LAN-only exposure options first, and only use a secure domain/NPM if it is actually relevant to SMTP traffic.
- The follow-up about NPM shows the user is open to a secure, proxied exposure path if that is the right mechanism.

Key steps:

- Verified the host LAN address with `ip -brief address`; the main LAN interface was `enp1s0` on `192.168.1.113/24`.
- Inspected the running container: `smtp-relay` had no host port publish (`docker ps` showed `587/tcp`, but `docker inspect` reported `"587/tcp": null` in `PortBindings`).
- Confirmed the container was only attached to `proxy_net` with an internal Docker IP (`172.25.0.35`).
- Checked UFW and nftables; UFW was active and the ruleset showed a large number of existing allows, but nothing yet for smtp-relay on the LAN.
- Checked the NPM compose file and found NPM exposes only HTTP/HTTPS ports (`80`, `81`, `443`), which means a normal secure web domain in NPM would not by itself solve SMTP client access.

Failures and how to do differently:

- I did not complete the actual LAN exposure change before the turn was aborted.
- The direct evidence suggests the right next step is not an HTTP proxy domain, but either a Docker port publish with firewall restriction to `192.168.1.0/24`, or a TCP-stream proxy if NPM’s stream support is available and configured.
- Because the turn aborted while gathering NPM/firewall details, the host-level exposure rule was not applied and should be re-verified before any further change.

Reusable knowledge:

- The current stack is internal-only: the relay is on `proxy_net` and currently not published to LAN.
- NPM’s compose here only exposes ports 80/81/443; a secure web domain is not a substitute for SMTP unless the NPM instance is configured for TCP stream proxying.
- UFW is active on the host.

References:

- `docker ps --format 'table {{.Names}}\t{{.Ports}}' | rg '^smtp-relay\b|NAMES'` -> `smtp-relay                  587/tcp`
- `docker inspect smtp-relay --format '{{json .HostConfig.PortBindings}} {{json .NetworkSettings.Networks}}'` -> `{"587/tcp":null} ... "IPAddress":"172.25.0.35" ...`
- `ip -brief address` -> `enp1s0 UP 192.168.1.113/24`
- `/home/ethan/docker/nginx-proxy-manager/docker-compose.yml` -> ports `80:80`, `81:81`, `443:443`
- `sudo -n ufw status verbose` -> `Status: active`
