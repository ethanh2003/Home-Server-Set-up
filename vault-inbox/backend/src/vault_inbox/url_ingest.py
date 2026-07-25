from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

import httpx


TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


class UnsafeUrlError(ValueError):
    pass


def _validate_url_target(url: str, *, allow_private_networks: bool) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("Only http and https URLs can be fetched.")
    if not parsed.hostname:
        raise UnsafeUrlError("URL must include a hostname.")
    if allow_private_networks:
        return
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Could not resolve URL hostname: {exc}") from exc
    for address in addresses:
        host = address[4][0]
        ip = ipaddress.ip_address(host)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise UnsafeUrlError("URL resolves to a private or otherwise unsafe network address.")


def fetch_url_summary(url: str, timeout: float = 8.0, *, allow_private_networks: bool = False) -> dict[str, str]:
    _validate_url_target(url, allow_private_networks=allow_private_networks)
    response = httpx.get(url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    text = response.text
    title_match = TITLE_RE.search(text)
    title = " ".join(title_match.group(1).split()) if title_match else response.url.host or url
    body = TAG_RE.sub(" ", text)
    readable = " ".join(body.split())[:8000]
    return {
        "url": str(response.url),
        "title": title,
        "content": readable,
    }
