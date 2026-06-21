#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from typing import Any


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith('"') and value.endswith('"'):
        return json.loads(value)
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def parse_inventory(path: Path) -> list[dict[str, Any]]:
    hosts: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_domains = False
    in_advanced = False
    advanced_lines: list[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == "proxy_hosts:":
            continue
        if stripped.startswith("- id:"):
            if current is not None:
                current["advanced_config"] = "\n".join(advanced_lines).rstrip("\n")
                hosts.append(current)
            current = {"id": int(stripped.split(":", 1)[1].strip()), "domains": []}
            in_domains = False
            in_advanced = False
            advanced_lines = []
            continue
        if current is None:
            continue
        if stripped == "domains:":
            in_domains = True
            in_advanced = False
            continue
        if in_domains and stripped.startswith("- "):
            current["domains"].append(parse_scalar(stripped[2:]))
            continue
        in_domains = False
        if in_advanced and raw_line.startswith("      "):
            advanced_lines.append(raw_line[6:])
            continue
        in_advanced = False
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if key == "advanced_config" and value.strip() == "|-":
            in_advanced = True
            advanced_lines = []
            continue
        current[key] = parse_scalar(value)

    if current is not None:
        current["advanced_config"] = "\n".join(advanced_lines).rstrip("\n")
        hosts.append(current)
    return hosts


def yaml_quote(value: str) -> str:
    return json.dumps(value)


def router_rule(domains: list[str]) -> str:
    return " || ".join(f"Host(`{domain}`)" for domain in domains)


def write_dynamic(hosts: list[dict[str, Any]], output: Path) -> None:
    lines = [
        "# Generated from nginx-proxy-manager/npm-migration-inventory.yml.",
        "http:",
        "  routers:",
    ]
    enabled_hosts = [host for host in hosts if host.get("enabled", True)]
    for host in enabled_hosts:
        rid = f"npm-{host['id']}"
        lines.append(f"    router-{rid}:")
        lines.append(f"      rule: {yaml_quote(router_rule(host['domains']))}")
        lines.append("      entryPoints:")
        lines.append("        - web")
        lines.append(f"      service: service-{rid}")
        if host.get("websocket"):
            lines.append("      middlewares:")
            lines.append("        - websocket-headers")

    lines.append("  services:")
    for host in enabled_hosts:
        rid = f"npm-{host['id']}"
        lines.append(f"    service-{rid}:")
        lines.append("      loadBalancer:")
        lines.append("        passHostHeader: true")
        lines.append("        servers:")
        lines.append(f"          - url: {host['forward_scheme']}://{host['forward_host']}:{host['forward_port']}")

    lines.append("  middlewares:")
    lines.append("    websocket-headers:")
    lines.append("      headers:")
    lines.append("        customRequestHeaders:")
    lines.append("          X-Forwarded-Proto: http")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Traefik dynamic config from NPM migration inventory.")
    parser.add_argument("--inventory", required=True, help="NPM migration inventory YAML")
    parser.add_argument("--output", required=True, help="Output Traefik dynamic YAML path")
    args = parser.parse_args()

    hosts = parse_inventory(Path(args.inventory))
    write_dynamic(hosts, Path(args.output))
    print(f"Generated Traefik dynamic config for {len(hosts)} proxy hosts at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
