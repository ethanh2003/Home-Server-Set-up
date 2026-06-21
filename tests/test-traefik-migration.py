#!/usr/bin/env python3
import json
import sqlite3
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> str:
    result = subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def create_npm_fixture(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE proxy_host (
            id integer primary key,
            created_on datetime not null,
            modified_on datetime not null,
            owner_user_id integer not null,
            is_deleted integer not null default 0,
            domain_names json not null,
            forward_host varchar(255) not null,
            forward_port integer not null,
            access_list_id integer not null default 0,
            certificate_id integer not null default 0,
            ssl_forced integer not null default 0,
            caching_enabled integer not null default 0,
            block_exploits integer not null default 0,
            advanced_config text not null default '',
            meta json not null,
            allow_websocket_upgrade integer not null default 0,
            http2_support integer not null default 0,
            forward_scheme varchar(255) not null default 'http',
            enabled integer not null default 1,
            locations json,
            hsts_enabled integer not null default 0,
            hsts_subdomains integer not null default 0,
            trust_forwarded_proto tinyint not null default 0
        )
        """
    )
    rows = [
        (1, ["app.example.test"], "http", "app", 8080, 1, 1, 0),
        (2, ["lan.example.test", "alt.example.test"], "https", "192.168.1.10", 443, 1, 0, 1),
    ]
    for row_id, domains, scheme, host, port, ssl_forced, h2, ws in rows:
        cur.execute(
            """
            INSERT INTO proxy_host (
                id, created_on, modified_on, owner_user_id, is_deleted,
                domain_names, forward_host, forward_port, access_list_id,
                certificate_id, ssl_forced, caching_enabled, block_exploits,
                advanced_config, meta, allow_websocket_upgrade, http2_support,
                forward_scheme, enabled, locations, hsts_enabled, hsts_subdomains,
                trust_forwarded_proto
            ) VALUES (?, '2026-01-01', '2026-01-01', 1, 0, ?, ?, ?, 0, 1, ?, 0, 0, '', '{}', ?, ?, ?, 1, '[]', 0, 0, 0)
            """,
            (row_id, json.dumps(domains), host, port, ssl_forced, ws, h2, scheme),
        )
    con.commit()
    con.close()


def main() -> int:
    tmpdir = Path(sys.argv[1])
    db_path = tmpdir / "npm.sqlite"
    inventory = tmpdir / "inventory.yml"
    dynamic = tmpdir / "dynamic.yml"

    create_npm_fixture(db_path)

    run("python3", "scripts/npm-export.py", "--db", str(db_path), "--output", str(inventory))
    exported = inventory.read_text()
    assert "app.example.test" in exported
    assert "lan.example.test" in exported
    assert "forward_host: app" in exported
    assert "forward_host: 192.168.1.10" in exported

    run("python3", "scripts/traefik-generate-dynamic.py", "--inventory", str(inventory), "--output", str(dynamic))
    rendered = dynamic.read_text()
    assert "http:" in rendered
    assert "router-npm-1" in rendered
    assert "router-npm-2" in rendered
    assert "Host(`lan.example.test`) || Host(`alt.example.test`)" in rendered
    assert "url: https://192.168.1.10:443" in rendered
    assert "passHostHeader: true" in rendered

    print("PASS: traefik migration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
