#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


API_BASE = "https://api.cloudflare.com/client/v4"
DEFAULT_OLD_SERVICES = ("http://npm:80", "http://nginx-proxy-manager:80")
WIKI_HOSTS = ("wiki.ethan-herring.com", "wiki.pup-percy.com", "wiki.ethanh.online")
DOMAIN_RE = re.compile(r"^\s+-\s+([A-Za-z0-9_.-]+)\s*$")
HOSTNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$")


def read_inventory_hosts(path: Path) -> tuple[str, ...]:
    hosts: list[str] = []
    in_domains = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped == "domains:":
            in_domains = True
            continue
        if in_domains and raw_line.startswith("      - "):
            match = DOMAIN_RE.match(raw_line)
            if match and match.group(1) not in hosts:
                hosts.append(match.group(1))
            continue
        if stripped and not raw_line.startswith("      "):
            in_domains = False
    return tuple(hosts)


def read_allowlist_hosts(path: Path) -> set[str]:
    hosts: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        hostname = raw_line.split("#", 1)[0].strip().lower().rstrip(".")
        if not hostname:
            continue
        if not HOSTNAME_RE.fullmatch(hostname):
            raise RuntimeError(f"Invalid hostname in {path}: {hostname}")
        hosts.add(hostname)
    if not hosts:
        raise RuntimeError(f"Public hostname allowlist is empty: {path}")
    return hosts


def filter_public_ingress(
    config: dict[str, Any],
    allowed_hosts: set[str],
) -> tuple[dict[str, Any], list[str]]:
    updated = json.loads(json.dumps(config))
    ingress = updated.setdefault("ingress", [])
    filtered: list[dict[str, Any]] = []
    removed: list[str] = []
    has_fallback = False

    for rule in ingress:
        hostname = rule.get("hostname")
        if not hostname:
            filtered.append(rule)
            has_fallback = True
            continue
        normalized = str(hostname).lower().rstrip(".")
        if normalized in allowed_hosts:
            filtered.append(rule)
        elif hostname not in removed:
            removed.append(hostname)

    if not has_fallback:
        filtered.append({"service": "http_status:404"})

    updated["ingress"] = filtered
    return updated, removed


def rewrite_config(
    config: dict[str, Any],
    target_service: str,
    old_services: tuple[str, ...] = DEFAULT_OLD_SERVICES,
    wiki_hosts: tuple[str, ...] = WIKI_HOSTS,
    inventory_hosts: tuple[str, ...] = (),
) -> tuple[dict[str, Any], list[str]]:
    updated = json.loads(json.dumps(config))
    ingress = updated.setdefault("ingress", [])
    changed: list[str] = []
    inventory_host_set = set(inventory_hosts)

    for rule in ingress:
        hostname = rule.get("hostname")
        service = rule.get("service")
        if hostname and (service in old_services or hostname in inventory_host_set):
            rule["service"] = target_service
            changed.append(hostname)

    existing_hosts = {rule.get("hostname") for rule in ingress if rule.get("hostname")}
    fallback_index = next((i for i, rule in enumerate(ingress) if "hostname" not in rule), len(ingress))
    for host in wiki_hosts:
        if host in existing_hosts:
            continue
        ingress.insert(fallback_index, {"hostname": host, "service": target_service})
        fallback_index += 1
        changed.append(host)

    return updated, changed


def request_json(method: str, path: str, token: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudflare API {method} {path} failed: {exc.code} {message}") from exc

    if not payload.get("success"):
        raise RuntimeError(f"Cloudflare API {method} {path} returned errors: {payload.get('errors')}")
    return payload


def write_backup(backup_dir: Path, payload: dict[str, Any]) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    path = backup_dir / f"tunnel-config-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return path


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Back up and rewrite Cloudflare Tunnel public hostname services.")
    parser.add_argument("--target-service", default="http://traefik:80")
    parser.add_argument("--backup-dir", default="cloudflared/backups")
    parser.add_argument("--inventory", default="nginx-proxy-manager/npm-migration-inventory.yml")
    parser.add_argument(
        "--public-allowlist",
        help="Keep only hostnames listed in this file plus the catch-all ingress rule.",
    )
    parser.add_argument("--apply", action="store_true", help="Write the updated config to Cloudflare.")
    parser.add_argument("--rollback", help="Restore a previously saved tunnel configuration JSON backup.")
    args = parser.parse_args()

    token = required_env("CLOUDFLARE_API_TOKEN")
    account_id = required_env("CLOUDFLARE_ACCOUNT_ID")
    tunnel_id = required_env("CLOUDFLARE_TUNNEL_ID")
    path = f"/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations"

    if args.rollback:
        backup_payload = json.loads(Path(args.rollback).read_text(encoding="utf-8"))
        config = backup_payload.get("result", backup_payload).get("config", backup_payload)
        if not args.apply:
            print(f"DRY RUN rollback from {args.rollback}; pass --apply to write it.")
            return 0
        request_json("PUT", path, token, {"config": config})
        print(f"Restored Cloudflare Tunnel configuration from {args.rollback}.")
        return 0

    current = request_json("GET", path, token)
    backup_path = write_backup(Path(args.backup_dir), current)
    current_config = current["result"]["config"]

    print(f"Backed up current Cloudflare Tunnel configuration to {backup_path}.")
    if args.public_allowlist:
        allowed_hosts = read_allowlist_hosts(Path(args.public_allowlist))
        updated_config, removed = filter_public_ingress(current_config, allowed_hosts)
        retained = {
            str(rule["hostname"]).lower().rstrip(".")
            for rule in updated_config.get("ingress", [])
            if rule.get("hostname")
        }
        missing = sorted(allowed_hosts - retained)
        if missing:
            raise RuntimeError(
                "Allowlisted public hostnames are absent from the current tunnel: "
                + ", ".join(missing)
            )
        print(f"Allowlisted public hostnames retained: {len(retained)}")
        print(f"Non-allowlisted public hostnames removed: {len(removed)}")
        for hostname in removed:
            print(f"- {hostname}")
    else:
        inventory_hosts = read_inventory_hosts(Path(args.inventory))
        updated_config, changed = rewrite_config(
            current_config,
            args.target_service,
            inventory_hosts=inventory_hosts,
        )
        print(f"Routes changed or verified for target {args.target_service}: {len(changed)}")
        for hostname in changed:
            print(f"- {hostname}")

    if not args.apply:
        print("DRY RUN only; pass --apply to write the updated tunnel configuration.")
        return 0

    request_json("PUT", path, token, {"config": updated_config})
    print("Updated Cloudflare Tunnel configuration.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
