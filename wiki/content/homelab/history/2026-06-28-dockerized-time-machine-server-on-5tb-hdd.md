# 2026-06-28T23-38-08-i9OE-dockerized_time_machine_server_on_5tb_hdd

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f1098-fac8-76a3-bd5d-d1a1441325a8
updated_at: 2026-06-28T23:52:06+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/28/rollout-2026-06-28T23-38-08-019f1098-fac8-76a3-bd5d-d1a1441325a8.jsonl
cwd: /home/ethan

# Dockerized Time Machine server setup on the 5TB HDD

Rollout context: The user wanted a Time Machine server for two Macs backed by the 5TB HDD at `/mnt/misc_5tb`, first explored a host-level Samba option, then explicitly changed course to prefer Docker for easier management and direct Apple integration. The work ended up as a Docker Compose stack in `/home/ethan/docker/timemachine` using a macvlan LAN IP plus a host shim for local verification.

## Task 1: Decide the Time Machine architecture and quotas

Outcome: success

Preference signals:
- The user first said they wanted to "add a time machine server from two mac's to the 5tb hhd" and later corrected the design with "I want docker for easier management and direct apple integration" -> future similar requests should default toward a Dockerized solution when the user emphasizes manageability and Apple-native integration.
- The user corrected the quota twice: first "1.5 total not per mac" and then accepted a shared pool -> future similar setups should not assume per-device quotas; clarify whether the number is total or per-machine.
- The user chose the generic names `TimeMachine_1 + TimeMachine_2` at first, but then the design shifted to a shared 1.5T pool and later a single container-backed share -> in similar work, watch for naming choices being superseded by a better storage model.

Key steps:
- Confirmed the 5TB disk is `/mnt/misc_5tb` and that Samba/Avahi were already installed and active on the host.
- Checked existing Samba config and discovered the host already exposed `/mnt/misc_5tb` as `Misc_5TB`, with Apple-specific fruit settings commented out.
- Explored a Docker-friendly approach after the user explicitly asked for Docker and direct Apple integration.

Failures and how to do differently:
- The initial host-Samba plan was superseded by the user's Docker preference, so future agents should treat this kind of user correction as a hard pivot and stop optimizing the earlier architecture.
- The time-machine quota needed multiple clarifications; ask whether the quota is total shared space or per-Mac before designing the stack.

Reusable knowledge:
- On this host, the practical mounting target for the Time Machine data was the ext4 filesystem at `/mnt/misc_5tb`, with ample free space.
- Existing host Samba/Avahi presence meant Docker needed a network strategy that would not fight the host for SMB discovery.

References:
- [1] `findmnt` / `lsblk` showed `/mnt/misc_5tb` mounted from `/dev/sdg1` with about 3.5T free.
- [2] `testparm -s` showed the host Samba config already included `[Misc_5TB]` for `/mnt/misc_5tb`.
- [3] The user's correction: "I want docker for easier management and direct apple integration".
- [4] The user's correction: "1.5 total not per mac".

## Task 2: Implement the Docker Time Machine stack and verify SMB access

Outcome: success

Preference signals:
- The user said "PLEASE IMPLEMENT THIS PLAN" after approving the Docker design -> in similar situations, move directly into implementation once the user explicitly asks for it.
- The user wanted "direct apple integration" -> future similar work should prioritize Avahi/mDNS-friendly SMB exposure instead of a generic Docker bridge-only service.

Key steps:
- Created `/home/ethan/docker/timemachine` with:
  - `docker-compose.yml`
  - `.env.example`
  - `.env` (ignored, runtime secret)
  - `README.md`
  - `scripts/create-macvlan-shim.sh`
  - `systemd/timemachine-macvlan-shim.service`
- Used `mbentley/timemachine:smb` with a macvlan network on `enp1s0` so the container had its own LAN identity at `192.168.1.230`.
- Added a host-side macvlan shim at `192.168.1.229` so the Docker host could reach the container IP for local verification.
- Mounted `/mnt/misc_5tb/backups/time-machine` into `/opt/timemachine` and created it with `drwxrws---` permissions.
- Configured the container with a single SMB user `timemachine`, share name `TimeMachine`, and `fruit:time machine max size = 1500 G`.
- Verified the stack with `docker compose config`, `docker compose up -d`, `ping 192.168.1.230`, open TCP 445, `testparm -s` inside the container, and actual SMB client operations from a temporary Alpine container.

Failures and how to do differently:
- The host did not have `smbclient`, so SMB verification had to be done from a temporary Alpine container with `samba-client` installed. In similar future work, expect to use a disposable client container when host tooling is missing.
- One container log warning said it could not become a local master browser; that did not block the intended Time Machine share or SMB access, so future agents should distinguish harmless Samba noise from real failures.
- The first write test inside the container ran as root and was less meaningful; the more useful check was a UID/GID `1000:1000` write test plus an actual SMB `mkdir/rmdir` round-trip.

Reusable knowledge:
- The working stack path is `/home/ethan/docker/timemachine`.
- The container IP is `192.168.1.230`, the host shim is `192.168.1.229`, and the LAN parent interface is `enp1s0` on `192.168.1.0/24`.
- The generated Samba config inside the container included `fruit:aapl = yes`, `fruit:model = TimeCapsule8,119`, `fruit:time machine = yes`, and `fruit:time machine max size = 1500 G`.
- The backed-up data path is writable by the container user and was SMB-testable end to end.
- The systemd unit `timemachine-macvlan-shim.service` was enabled and active so the host shim persists across reboot.

References:
- [1] `docker-compose.yml` under `/home/ethan/docker/timemachine`.
- [2] `docker compose config --quiet` passed.
- [3] `docker compose ps` showed `timemachine` running on `mbentley/timemachine:smb`.
- [4] `docker exec timemachine testparm -s` showed `fruit:model = TimeCapsule8,119`, `fruit:aapl = yes`, `vfs objects = fruit streams_xattr`, `[TimeMachine]`, `fruit:time machine max size = 1500 G`, and `fruit:time machine = yes`.
- [5] `docker run --rm --env-file .env alpine:3.20 ... smbclient -L //192.168.1.230 -U timemachine%...` returned `Disk|TimeMachine|`.
- [6] `docker run --rm --env-file .env alpine:3.20 ... smbclient //192.168.1.230/TimeMachine ... -c "mkdir ...; rmdir ..."` succeeded.
- [7] `systemctl is-enabled timemachine-macvlan-shim.service` and `systemctl is-active timemachine-macvlan-shim.service` both returned active/enabled.
- [8] `nmblookup -A 192.168.1.230` returned the `TIMEMACHINE` name and `WORKGROUP` entries, showing the share was discoverable on the LAN.
