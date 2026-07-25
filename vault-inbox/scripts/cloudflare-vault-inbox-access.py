#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass

import requests


API_BASE = "https://api.cloudflare.com/client/v4"


@dataclass(frozen=True)
class Config:
    token: str
    account_id: str
    zone_id: str
    tunnel_id: str
    hostname: str
    service: str
    allowed_email: str
    team_name: str | None


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def load_config() -> Config:
    return Config(
        token=required_env("CLOUDFLARE_API_TOKEN"),
        account_id=required_env("CLOUDFLARE_ACCOUNT_ID"),
        zone_id=required_env("CLOUDFLARE_ZONE_ID"),
        tunnel_id=required_env("CLOUDFLARE_TUNNEL_ID"),
        hostname=os.environ.get("VAULT_INBOX_HOSTNAME", "inbox.ethan-herring.com"),
        service=os.environ.get("VAULT_INBOX_TUNNEL_SERVICE", "http://vault-inbox:8080"),
        allowed_email=os.environ.get("VAULT_INBOX_ACCESS_EMAIL", "echerring.ech@gmail.com"),
        team_name=os.environ.get("CLOUDFLARE_ZERO_TRUST_TEAM_NAME"),
    )


def request(config: Config, method: str, path: str, *, payload: dict | None = None, dry_run: bool = False) -> dict:
    url = f"{API_BASE}{path}"
    if dry_run:
        print(json.dumps({"method": method, "url": url, "payload": payload}, indent=2, sort_keys=True))
        return {}
    response = requests.request(
        method,
        url,
        headers={"Authorization": f"Bearer {config.token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    if not body.get("success", False):
        raise RuntimeError(json.dumps(body, indent=2))
    return body.get("result") or {}


def create_access_application(config: Config, *, dry_run: bool) -> dict:
    payload = {
        "name": "vault-inbox",
        "domain": config.hostname,
        "type": "self_hosted",
        "session_duration": "24h",
        "allowed_idps": [],
        "auto_redirect_to_identity": False,
    }
    return request(
        config,
        "POST",
        f"/accounts/{config.account_id}/access/apps",
        payload=payload,
        dry_run=dry_run,
    )


def create_access_policy(config: Config, app_id: str, *, dry_run: bool) -> dict:
    payload = {
        "name": "Allow Ethan",
        "decision": "allow",
        "precedence": 1,
        "include": [{"email": {"email": config.allowed_email}}],
    }
    return request(
        config,
        "POST",
        f"/accounts/{config.account_id}/access/apps/{app_id}/policies",
        payload=payload,
        dry_run=dry_run,
    )


def add_dns_route(config: Config, *, dry_run: bool) -> dict:
    payload = {
        "type": "CNAME",
        "name": config.hostname,
        "content": f"{config.tunnel_id}.cfargotunnel.com",
        "proxied": True,
        "ttl": 1,
    }
    return request(config, "POST", f"/zones/{config.zone_id}/dns_records", payload=payload, dry_run=dry_run)


def tunnel_access_origin_request(config: Config, app: dict) -> dict:
    aud = app.get("aud") or app.get("aud_tag") or "<ACCESS_AUD_TAG_FROM_APP>"
    access = {"audTag": [aud], "required": True}
    if config.team_name:
        access["teamName"] = config.team_name
    return {"access": access}


def get_tunnel_configuration(config: Config) -> dict:
    return request(config, "GET", f"/accounts/{config.account_id}/cfd_tunnel/{config.tunnel_id}/configurations")


def put_tunnel_configuration(config: Config, tunnel_config: dict, *, dry_run: bool) -> dict:
    return request(
        config,
        "PUT",
        f"/accounts/{config.account_id}/cfd_tunnel/{config.tunnel_id}/configurations",
        payload=tunnel_config,
        dry_run=dry_run,
    )


def upsert_tunnel_route(config: Config, app: dict, *, dry_run: bool) -> dict:
    route = {
        "hostname": config.hostname,
        "service": config.service,
        "originRequest": tunnel_access_origin_request(config, app),
    }
    if dry_run:
        payload = {
            "config": {
                "ingress": [
                    route,
                    {"service": "http_status:404"},
                ]
            }
        }
        return put_tunnel_configuration(config, payload, dry_run=True)

    current = get_tunnel_configuration(config)
    tunnel_config = current.get("config") or {}
    ingress = tunnel_config.get("ingress") or []
    catch_all = [item for item in ingress if "hostname" not in item]
    named = [item for item in ingress if item.get("hostname") != config.hostname and "hostname" in item]
    tunnel_config["ingress"] = named + [route] + (catch_all or [{"service": "http_status:404"}])
    return put_tunnel_configuration(config, {"config": tunnel_config}, dry_run=False)


def print_tunnel_step(config: Config, app: dict) -> None:
    aud = app.get("aud") or app.get("aud_tag") or "<ACCESS_AUD_TAG_FROM_APP>"
    print(
        "\nTunnel public hostname configuration required:\n"
        f"- Hostname: {config.hostname}\n"
        f"- Service: {config.service}\n"
        "- Protect with Access: enabled\n"
        f"- Access audTag: {aud}\n"
        f"- Access teamName: {config.team_name or '<your Zero Trust team name>'}\n"
        "- Access required: true\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Cloudflare Access shell for vault-inbox.")
    parser.add_argument("--apply", action="store_true", help="Apply changes. Default is dry-run.")
    parser.add_argument(
        "--skip-tunnel-config",
        action="store_true",
        help="Do not add or update the remote-managed Tunnel ingress route.",
    )
    args = parser.parse_args()
    config = load_config()
    dry_run = not args.apply
    app = create_access_application(config, dry_run=dry_run)
    app_id = app.get("id", "<ACCESS_APP_ID_FROM_DRY_RUN>")
    create_access_policy(config, app_id, dry_run=dry_run)
    add_dns_route(config, dry_run=dry_run)
    if not args.skip_tunnel_config:
        upsert_tunnel_route(config, app, dry_run=dry_run)
    print_tunnel_step(config, app)
    if dry_run:
        print("Dry run only. Re-run with --apply after reviewing payloads.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.HTTPError as exc:
        print(f"Cloudflare API request failed: {exc}", file=sys.stderr)
        if exc.response is not None:
            print(exc.response.text, file=sys.stderr)
        raise SystemExit(1)
