#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "cloudflare-tunnel-cutover.py"

spec = importlib.util.spec_from_file_location("cloudflare_tunnel_cutover", SCRIPT_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main() -> int:
    config = {
        "originRequest": {"connectTimeout": 30},
        "ingress": [
            {
                "hostname": "jellyfin.example.test",
                "service": "http://npm:80",
                "originRequest": {"noTLSVerify": True},
            },
            {"hostname": "grafana.example.test", "service": "http://npm:80"},
            {"hostname": "jellyfin.example.test", "path": "/socket", "service": "http://npm:80"},
            {"service": "http_status:404"},
        ],
    }

    updated, removed = module.filter_public_ingress(
        config,
        {"jellyfin.example.test"},
    )

    assert [rule.get("hostname") for rule in updated["ingress"]] == [
        "jellyfin.example.test",
        "jellyfin.example.test",
        None,
    ]
    assert updated["ingress"][0]["originRequest"] == {"noTLSVerify": True}
    assert updated["originRequest"] == {"connectTimeout": 30}
    assert removed == ["grafana.example.test"]
    assert config["ingress"][1]["hostname"] == "grafana.example.test"

    no_fallback = {
        "ingress": [
            {"hostname": "allowed.example.test", "service": "http://service:80"},
        ]
    }
    updated, removed = module.filter_public_ingress(
        no_fallback,
        {"allowed.example.test"},
    )
    assert removed == []
    assert updated["ingress"][-1] == {"service": "http_status:404"}

    print("PASS: Cloudflare ingress allowlist preserves approved routes and a 404 fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
