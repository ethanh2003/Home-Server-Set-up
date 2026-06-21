#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB = Path("/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite")


def yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if text == "" or any(ch in text for ch in ":#[]{}&,*!|>'\"%@`") or text.strip() != text:
        return json.dumps(text)
    return text


def write_inventory(rows: list[dict[str, Any]], output: Path) -> None:
    lines = [
        "# Generated from Nginx Proxy Manager. Review before using for cutover.",
        "proxy_hosts:",
    ]
    for row in rows:
        lines.append(f"  - id: {row['id']}")
        lines.append("    domains:")
        for domain in row["domains"]:
            lines.append(f"      - {yaml_scalar(domain)}")
        for key in (
            "forward_scheme",
            "forward_host",
            "forward_port",
            "enabled",
            "ssl_forced",
            "http2_support",
            "websocket",
            "certificate_id",
        ):
            lines.append(f"    {key}: {yaml_scalar(row[key])}")
        if row["advanced_config"]:
            lines.append("    advanced_config: |-")
            for line in row["advanced_config"].splitlines():
                lines.append(f"      {line}")
        else:
            lines.append('    advanced_config: ""')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_hosts(db_path: Path) -> list[dict[str, Any]]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = []
    for row in con.execute(
        """
        SELECT id, domain_names, forward_scheme, forward_host, forward_port,
               enabled, ssl_forced, http2_support, allow_websocket_upgrade,
               certificate_id, advanced_config
        FROM proxy_host
        WHERE is_deleted = 0
        ORDER BY id
        """
    ):
        rows.append(
            {
                "id": row["id"],
                "domains": json.loads(row["domain_names"]),
                "forward_scheme": row["forward_scheme"],
                "forward_host": row["forward_host"],
                "forward_port": row["forward_port"],
                "enabled": bool(row["enabled"]),
                "ssl_forced": bool(row["ssl_forced"]),
                "http2_support": bool(row["http2_support"]),
                "websocket": bool(row["allow_websocket_upgrade"]),
                "certificate_id": row["certificate_id"],
                "advanced_config": row["advanced_config"] or "",
            }
        )
    con.close()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Export NPM proxy hosts into migration inventory YAML.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Path to NPM database.sqlite")
    parser.add_argument("--output", required=True, help="Output inventory YAML path")
    args = parser.parse_args()

    rows = export_hosts(Path(args.db))
    write_inventory(rows, Path(args.output))
    print(f"Exported {len(rows)} proxy hosts to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
