#!/usr/bin/env python3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
workflow = (REPO_ROOT / ".github/workflows/iac-deploy.yml").read_text()
trigger_block = workflow.split("\npermissions:", 1)[0]

assert "  workflow_dispatch:" in trigger_block
assert "  push:" not in trigger_block, (
    "IaC auto-deploy must remain disabled until live/GitHub parity is proven; "
    "use workflow_dispatch for approved deployments"
)

print("PASS: IaC deployment is manual-only until parity approval")
