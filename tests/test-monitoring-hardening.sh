#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

required_files=(
    "$REPO_ROOT/monitoring-stack/prometheus_config/rules/homelab-alerts.yml"
    "$REPO_ROOT/monitoring-stack/blackbox_config/blackbox.yml"
    "$REPO_ROOT/scripts/update-homelab-metrics.sh"
)

for path in "${required_files[@]}"; do
    if [[ ! -f "$path" ]]; then
        echo "FAIL: missing monitoring file $path" >&2
        exit 1
    fi
done

bash -n "$REPO_ROOT/scripts/update-homelab-metrics.sh"

python3 - "$REPO_ROOT" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])


def compose(path: Path) -> dict:
    result = subprocess.run(
        ["docker", "compose", "-f", str(path), "config", "--format", "json"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def assert_rotated(service: dict, name: str) -> None:
    logging = service.get("logging") or {}
    assert logging.get("driver") == "json-file", f"{name}: missing json-file logging"
    options = logging.get("options") or {}
    assert options.get("max-size") == "10m", f"{name}: max-size is not 10m"
    assert str(options.get("max-file")) == "3", f"{name}: max-file is not 3"


monitoring = compose(root / "monitoring-stack" / "docker-compose.yml")
for name, service in monitoring["services"].items():
    assert_rotated(service, f"monitoring/{name}")

node = monitoring["services"]["node-exporter"]
assert "--collector.textfile.directory=/textfile" in node["command"]
assert any(
    volume["target"] == "/textfile" and volume.get("read_only")
    for volume in node["volumes"]
)

cadvisor = monitoring["services"]["cadvisor"]
assert cadvisor["image"] == "ghcr.io/google/cadvisor:v0.57.0"
assert "--docker_only=true" in cadvisor["command"]
assert "--housekeeping_interval=15s" in cadvisor["command"]
assert "--store_container_labels=false" in cadvisor["command"]
assert (
    "--whitelisted_container_labels="
    "com.docker.compose.project,com.docker.compose.service"
) in cadvisor["command"]
assert "--enable_metrics=cpu,memory,network,diskIO,oom_event" in cadvisor["command"]
assert any(
    volume["source"].rstrip("/") == "/var/lib/containerd"
    and volume["target"] == "/var/lib/containerd"
    and volume.get("read_only")
    for volume in cadvisor["volumes"]
)

grafana_env = monitoring["services"]["grafana"]["environment"]
assert str(grafana_env["GF_SMTP_ENABLED"]).lower() == "true"
assert grafana_env["GF_SMTP_HOST"] == "smtp-relay:25"

spotify = compose(root / "spotify-stats" / "docker-compose.yml")
assert_rotated(spotify["services"]["mongo"], "spotify-stats/mongo")

stash = compose(root / "stash" / "docker-compose.yml")
assert_rotated(stash["services"]["stash"], "stash/stash")

prometheus = (root / "monitoring-stack/prometheus_config/prometheus.yml").read_text()
assert "rule_files:" in prometheus
assert "blackbox_public" in prometheus
assert "scrape_interval: 15s" in prometheus
assert "scrape_timeout: 10s" in prometheus
assert prometheus.count("https://") >= 15

alerts = (
    root
    / "monitoring-stack"
    / "prometheus_config"
    / "rules"
    / "homelab-alerts.yml"
).read_text()
assert "HomelabCadvisorContainerMetricsMissing" in alerts
assert "HomelabSmartDiskTemperatureHigh" in alerts
assert "time() - homelab_docker_latest_oom_timestamp_seconds < 900" in alerts
assert "or homelab_docker_oom_killed_containers > 0" not in alerts

metrics_script = (root / "scripts" / "update-homelab-metrics.sh").read_text()
assert "homelab_docker_latest_oom_timestamp_seconds" in metrics_script
assert "homelab_smart_temperature_celsius" in metrics_script

print(
    "PASS: monitoring, cAdvisor discovery, SMTP, probes, textfile metrics, "
    "and log rotation are configured"
)
PY

docker run --rm \
    --entrypoint /bin/promtool \
    -v "$REPO_ROOT/monitoring-stack/prometheus_config/rules:/rules:ro" \
    prom/prometheus:latest \
    check rules /rules/homelab-alerts.yml
