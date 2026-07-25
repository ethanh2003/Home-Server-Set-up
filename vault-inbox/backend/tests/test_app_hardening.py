from pathlib import Path

from fastapi.testclient import TestClient

from vault_inbox.app import create_app
from vault_inbox.config import Settings


def make_client(tmp_path: Path) -> TestClient:
    vault = tmp_path / "vault"
    repo = tmp_path / "repo"
    vault.mkdir()
    repo.mkdir()
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=vault,
        app_repo_root=repo,
        codex_enabled=False,
        smtp_enabled=False,
    )
    return TestClient(create_app(settings=settings))


def test_health_redacts_internal_paths_and_docs_are_disabled_by_default(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    health = client.get("/api/health")

    assert health.status_code == 200
    body = health.json()
    assert body["vault"] == {"ok": True}
    assert "binary" not in body["codex"]
    assert "base_url" not in body["ollama"]
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_command_errors_return_json_detail(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)

    def explode(*args, **kwargs):
        raise RuntimeError("ollama unavailable")

    monkeypatch.setattr("vault_inbox.app.check_ollama", explode)

    response = client.post("/api/commands/check-ollama")

    assert response.status_code == 500
    assert response.json()["detail"] == "ollama unavailable"
