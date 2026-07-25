# 2026-06-26T18-07-59-PiXg-jellyfin_nic_s2s_streaming_debug_and_router_fix

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f051d-fff9-7c72-8500-4775709523fa
updated_at: 2026-06-26T23:32:20+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/26/rollout-2026-06-26T18-07-59-019f051d-fff9-7c72-8500-4775709523fa.jsonl
cwd: /home/ethan

# Diagnosed and partially fixed a Jellyfin/Nic streaming problem in the homelab, then refined the fix when Shrek still froze.

Rollout context: The user wanted help with Nic’s Jellyfin playback issues over a VPN/S2S path, using Grafana and logs to figure out why larger files failed. Work happened in `/home/ethan` against the Jellyfin stack under `/home/ethan/docker/jellyfin` and Ethan’s router at `192.168.1.1`.

## Task 1: Diagnose Nic’s large-file streaming failure

Outcome: partial

Preference signals:
- The user asked to use “grafana and any other logs” to find the issue, implying future similar incidents should start with logs/metrics correlation rather than guessing from symptoms.
- The user interrupted and said “continue,” indicating they were okay with the same evidence trail being extended rather than restarting the investigation.

Key steps:
- Queried Jellyfin system/user/device/session data via the Jellyfin MCP tools.
- Checked local Docker topology, Jellyfin config files, and Prometheus/Grafana stack layout.
- Read Jellyfin playback logs and FFmpeg transcode/direct-stream logs for Nic’s sessions.
- Confirmed Nic’s playback history on the server and correlated it with router/NPM access logs.

Failures and how to do differently:
- Early evidence showed Jellyfin saw Nic sessions as coming from proxy/router IPs (`172.25.0.20`, later `192.168.1.1`) rather than Nic’s true client network, so the first root cause turned out to be networking/NAT rather than media format alone.
- The playback path for large files bounced between direct play, direct stream, and transcode attempts, so future troubleshooting should explicitly separate “source-IP/routing” from “codec/bitrate” causes instead of assuming one explains everything.

Reusable knowledge:
- Jellyfin session/playback logs plus NPM access logs were enough to distinguish client-source-IP problems from transcoding problems.
- Prometheus/Grafana were present and healthy, but the decisive evidence came from Jellyfin logs and NPM access logs more than from aggregate metrics.

References:
- `/home/ethan/docker/jellyfin/config/jellyfin/log/log_20260626.log`
- `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/logs/proxy-host-2_access.log`
- Jellyfin session evidence repeatedly showed Nic/user id `fd9b28b5be294cccb446faf945ed5b63`.

## Task 2: Remove router-side SNAT and preserve Nic source IP

Outcome: success

Preference signals:
- The user approved a plan to remove the duplicate `Masquerade-Main-to-IoT` NAT entries and explicitly asked for implementation.
- They also asked to “try now” on router access, indicating they expect the agent to retry blocked infrastructure access instead of stopping early.

Key steps:
- Backed up Ethan router firewall state and saved router artifacts under `/root/backups/nic-jellyfin-s2s-20260626T232142Z`.
- Removed the two exact `config nat` sections named `Masquerade-Main-to-IoT` with `src='lan'`, `dest='guest'`, `target='MASQUERADE'` from Ethan router firewall config.
- Reloaded firewall and verified `zone_lan_postrouting` no longer contained the unconditional MASQUERADE rules.
- Verified a Nic-router-origin request to `https://jellyfin.ethanh.online/System/Info/Public` was logged by NPM as `[Client 172.30.55.2]` instead of `[Client 192.168.1.1]`.
- Verified a synthetic request using Nic LAN source `192.168.8.1` was logged by NPM as `192.168.8.1`, confirming the S2S path preserved source IPs.

Failures and how to do differently:
- Initial router NAT inspection used the wrong shape on the first pass; the useful confirmation was `uci show firewall` plus `iptables -t nat -S zone_lan_postrouting`.
- Firewall reload emitted many pre-existing GL.iNet/OpenWrt warnings, but those did not invalidate the specific NAT change; future similar runs should distinguish “noisy but existing” from “newly introduced” errors.

Reusable knowledge:
- On Ethan router `192.168.1.1`, `wg1` carried the S2S route for `192.168.8.0/24` and the problematic SNAT came from duplicate LAN-to-guest masquerade NAT sections.
- After deletion, `iptables -t nat -S zone_lan_postrouting` showed only the custom rule-chain jump, no MASQUERADE entries.

References:
- Backup directory: `/root/backups/nic-jellyfin-s2s-20260626T232142Z`
- Ethan router route evidence: `192.168.8.0/24 dev wg1 scope link metric 80`
- NPM log evidence:
  - before fix: `[Client 192.168.1.1]`
  - after fix: `[Client 172.30.55.2]`
  - Nic LAN simulation: `[Client 192.168.8.1]`

## Task 3: Fix Jellyfin classification for Nic’s remote playback and tighten bitrate

Outcome: success

Preference signals:
- The user then reported Shrek still frozen, which implied the networking fix alone was not enough and the next default should be to re-check playback classification/bitrate.
- The user asked whether playback could be forced on Nic’s account, implying they expect the agent to understand the difference between an active session and a closed client.

Key steps:
- Inspected Shrek playback logs and FFmpeg output.
- Confirmed Shrek is a large remux (`~45 Mbps`) with many audio/subtitle tracks.
- Saw Jellyfin start a transcode path, then switch to a very high-bitrate copy/HLS path; this matched the frozen-screen symptom.
- Updated `/home/ethan/docker/jellyfin/config/jellyfin/network.xml` to narrow local classification from `192.168.0.0/16` to `192.168.1.0/24`, so Nic’s `192.168.8.x` clients would no longer be treated as local.
- Updated Nic’s `RemoteClientBitrateLimit` to `20000000`.
- Backed up the Jellyfin DB and network config before editing and restarted Jellyfin cleanly.
- Verified Nic’s policy now shows `RemoteClientBitrateLimit: 20000000` and Jellyfin stayed healthy after restart.

Failures and how to do differently:
- The first post-fix test showed the network path was fine, but the stream still froze because Jellyfin was still allowing an effectively local/high-bitrate playback path; future similar issues should check the local-network classification before concluding it is a pure bandwidth problem.
- When the user asked to force-start Shrek, the agent discovered Nic had no active controllable session. Future attempts should first verify `get_sessions` shows an active Nic client before trying remote-play commands.

Reusable knowledge:
- `network.xml` originally had `<string>192.168.0.0/16</string>` in `LocalNetworkSubnets`; that was too broad for this setup because it included Nic’s VPN/LAN path.
- The relevant stream symptom in logs was a Shrek HLS/transcode attempt that reached very high bitrate segments, matching the frozen playback.
- Jellyfin MCP exposes a remote play endpoint (`/Sessions/{sessionId}/Playing`) but it only works when Nic has an active session.

References:
- Backups:
  - `/home/ethan/docker/jellyfin/config/jellyfin/network.xml.bak-20260626T232950Z-nic-remote-subnet`
  - `/home/ethan/docker/jellyfin/config/jellyfin/data/data/jellyfin.db.bak-20260626T232950Z-nic-remote-subnet`
- Edited file: `/home/ethan/docker/jellyfin/config/jellyfin/network.xml`
- Nic policy after change: `RemoteClientBitrateLimit: 20000000`
- Important log artifacts:
  - Shrek playback info request from Nic source `192.168.8.153`
  - Shrek transcode command using `/data/movies/Shrek (2001)/Shrek (2001) Remux-1080p.mkv`
  - Warning: `cannot serve ... as it doesn't exist and no transcode is running`

## Task 4: Attempt to force-start Shrek on Nic’s account

Outcome: uncertain

Preference signals:
- The user asked, “any way you can force start shrek on their account?” which suggests future similar cases should check for a live client session and try a remote-control playback command if one exists.

Key steps:
- Inspected the Jellyfin MCP implementation and found support for `/Sessions/{sessionId}/Playing` with `playCommand`.
- Queried sessions and confirmed Nic had no active controllable Jellyfin client session at the moment.
- Determined a force-start was not possible without an active Nic session.

Failures and how to do differently:
- Do not promise remote playback control unless `get_sessions` shows Nic’s session is active and supports remote control.
- If the user wants a forced start, ask them to open Jellyfin/Moonfin on Nic’s device first, then send the play command to that live session.
