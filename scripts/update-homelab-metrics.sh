#!/usr/bin/env bash
set -Eeuo pipefail

umask 022

OUTPUT_DIR="${OUTPUT_DIR:-/home/ethan/docker/monitoring-stack/node_exporter_textfile}"
OUTPUT_FILE="${OUTPUT_FILE:-$OUTPUT_DIR/homelab.prom}"
DOCKER_BIN="${DOCKER_BIN:-docker}"
SMARTCTL_BIN="${SMARTCTL_BIN:-smartctl}"

mkdir -p "$OUTPUT_DIR"
temporary=$(mktemp "$OUTPUT_DIR/.homelab.prom.tmp.XXXXXX")
trap 'rm -f -- "$temporary"' EXIT

docker_unhealthy=0
docker_oom_killed=0
docker_latest_oom_timestamp=0
gluetun_healthy=0

mapfile -t container_ids < <("$DOCKER_BIN" ps -aq)
if ((${#container_ids[@]} > 0)); then
    while IFS='|' read -r name running health oom_killed finished_at; do
        [[ -n "$name" ]] || continue
        if [[ "$running" == "true" && "$health" == "unhealthy" ]]; then
            docker_unhealthy=$((docker_unhealthy + 1))
        fi
        if [[ "$oom_killed" == "true" ]]; then
            docker_oom_killed=$((docker_oom_killed + 1))
            if oom_timestamp=$(date --date="$finished_at" +%s 2>/dev/null); then
                if ((oom_timestamp > docker_latest_oom_timestamp)); then
                    docker_latest_oom_timestamp=$oom_timestamp
                fi
            fi
        fi
        if [[ "$name" == "/gluetun" && "$running" == "true" && "$health" == "healthy" ]]; then
            gluetun_healthy=1
        fi
    done < <(
        "$DOCKER_BIN" inspect \
            --format '{{.Name}}|{{.State.Running}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}|{{.State.OOMKilled}}|{{.State.FinishedAt}}' \
            "${container_ids[@]}"
    )
fi

kopia_query_success=0
kopia_latest_errors=0
kopia_latest_end_timestamp=0
if snapshot_json=$("$DOCKER_BIN" exec kopia_backup kopia snapshot list --all --json 2>/dev/null); then
    read -r kopia_latest_errors kopia_latest_end_timestamp < <(
        python3 -c '
import datetime
import json
import sys

snapshots = json.load(sys.stdin)
latest = {}
for snapshot in sorted(snapshots, key=lambda item: item.get("startTime", "")):
    source = (snapshot.get("source") or {}).get("path")
    if source:
        latest[source] = snapshot

errors = 0
latest_timestamp = 0
for snapshot in latest.values():
    summary = ((snapshot.get("rootEntry") or {}).get("summ") or {})
    errors += int(summary.get("numFailed") or 0)
    end_time = snapshot.get("endTime")
    if end_time:
        parsed = datetime.datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        latest_timestamp = max(latest_timestamp, int(parsed.timestamp()))

print(errors, latest_timestamp)
' <<<"$snapshot_json"
    )
    kopia_query_success=1
fi

{
    echo '# HELP homelab_docker_unhealthy_containers Number of running Docker containers reporting unhealthy.'
    echo '# TYPE homelab_docker_unhealthy_containers gauge'
    printf 'homelab_docker_unhealthy_containers %s\n' "$docker_unhealthy"
    echo '# HELP homelab_docker_oom_killed_containers Number of containers whose current state records an OOM kill.'
    echo '# TYPE homelab_docker_oom_killed_containers gauge'
    printf 'homelab_docker_oom_killed_containers %s\n' "$docker_oom_killed"
    echo '# HELP homelab_docker_latest_oom_timestamp_seconds Latest recorded Docker OOM termination time.'
    echo '# TYPE homelab_docker_latest_oom_timestamp_seconds gauge'
    printf 'homelab_docker_latest_oom_timestamp_seconds %s\n' "$docker_latest_oom_timestamp"
    echo '# HELP homelab_gluetun_healthy Whether the Gluetun container is currently healthy.'
    echo '# TYPE homelab_gluetun_healthy gauge'
    printf 'homelab_gluetun_healthy %s\n' "$gluetun_healthy"
    echo '# HELP homelab_kopia_query_success Whether Kopia snapshot status was read successfully.'
    echo '# TYPE homelab_kopia_query_success gauge'
    printf 'homelab_kopia_query_success %s\n' "$kopia_query_success"
    echo '# HELP homelab_kopia_latest_snapshot_errors Errors across the latest snapshot for each protected source.'
    echo '# TYPE homelab_kopia_latest_snapshot_errors gauge'
    printf 'homelab_kopia_latest_snapshot_errors %s\n' "$kopia_latest_errors"
    echo '# HELP homelab_kopia_latest_snapshot_end_timestamp_seconds Latest protected snapshot completion time.'
    echo '# TYPE homelab_kopia_latest_snapshot_end_timestamp_seconds gauge'
    printf 'homelab_kopia_latest_snapshot_end_timestamp_seconds %s\n' "$kopia_latest_end_timestamp"

    while read -r device_name device_type; do
        [[ "$device_type" == "disk" ]] || continue
        device="/dev/$device_name"
        smart_json=$(sudo -n "$SMARTCTL_BIN" -a -j "$device" 2>/dev/null || true)
        [[ -n "$smart_json" ]] || continue
        python3 -c '
import json
import sys

device = sys.argv[1]
payload = json.load(sys.stdin)
passed = (payload.get("smart_status") or {}).get("passed")
healthy = 1 if passed is True else 0
pending = 0
uncorrectable = 0
temperature = (payload.get("temperature") or {}).get("current")
for item in ((payload.get("ata_smart_attributes") or {}).get("table") or []):
    attribute_id = item.get("id")
    raw = (item.get("raw") or {}).get("value")
    if not isinstance(raw, int):
        continue
    if attribute_id == 197:
        pending = raw
    elif attribute_id == 198:
        uncorrectable = raw

print(f'\''homelab_smart_device_healthy{{device="{device}"}} {healthy}'\'')
print(f'\''homelab_smart_pending_sectors{{device="{device}"}} {pending}'\'')
print(f'\''homelab_smart_uncorrectable_sectors{{device="{device}"}} {uncorrectable}'\'')
if isinstance(temperature, (int, float)):
    print(f'\''homelab_smart_temperature_celsius{{device="{device}"}} {temperature}'\'')
' "$device" <<<"$smart_json"
    done < <(lsblk -dn -o NAME,TYPE)
} >"$temporary"

chmod 644 "$temporary"
mv -f -- "$temporary" "$OUTPUT_FILE"
trap - EXIT
