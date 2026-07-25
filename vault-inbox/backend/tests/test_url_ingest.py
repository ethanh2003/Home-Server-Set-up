import socket

import pytest

from vault_inbox.url_ingest import UnsafeUrlError, fetch_url_summary


def test_url_ingest_blocks_localhost_before_fetch(monkeypatch) -> None:
    def fake_getaddrinfo(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("127.0.0.1", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    with pytest.raises(UnsafeUrlError, match="private"):
        fetch_url_summary("http://example.test/private")


def test_url_ingest_blocks_non_http_schemes() -> None:
    with pytest.raises(UnsafeUrlError, match="http"):
        fetch_url_summary("file:///etc/passwd")
