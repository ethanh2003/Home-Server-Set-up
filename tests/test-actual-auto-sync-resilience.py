#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = REPO_ROOT / "actual-budget" / "docker-compose.yml"

result = subprocess.run(
    ["docker", "compose", "-f", str(COMPOSE_FILE), "config", "--format", "json"],
    cwd=REPO_ROOT,
    check=True,
    text=True,
    stdout=subprocess.PIPE,
)
service = json.loads(result.stdout)["services"]["actual-auto-sync"]

assert service.get("restart") == "unless-stopped", (
    "Actual auto-sync is a persistent scheduler and must recover after a failure"
)

memory_limit = (
    service.get("deploy", {})
    .get("resources", {})
    .get("limits", {})
    .get("memory", 0)
)
assert int(memory_limit) >= 512 * 1024 * 1024, (
    "Actual auto-sync previously OOM-killed at 256 MiB; require at least 512 MiB"
)

print("PASS: Actual auto-sync has a restart policy and a corrective memory floor")
