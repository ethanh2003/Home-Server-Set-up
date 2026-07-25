import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from vault_inbox.app import create_app
from vault_inbox.config import Settings
from vault_inbox.git_ops import GitOps
from vault_inbox.policy_sync import sync_policies_to_vault


def test_git_init_creates_local_repo_and_ignores_protected_paths(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    result = GitOps(vault).ensure_repo()

    assert result["initialized"] is True
    assert (vault / ".git").exists()
    gitignore = (vault / ".gitignore").read_text(encoding="utf-8")
    assert ".obsidian/" in gitignore
    assert "Therapy/Transcripts/" in gitignore
    assert subprocess.run(["git", "-C", str(vault), "status", "--short"], check=True, capture_output=True).returncode == 0


def test_policy_sync_writes_readable_vault_admin_copy(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    repo = tmp_path / "repo"
    (repo / "policies").mkdir(parents=True)
    vault.mkdir()
    (repo / "policies" / "capture.yml").write_text(
        "id: capture\nversion: 1\nsummary: Capture policy\n",
        encoding="utf-8",
    )

    written = sync_policies_to_vault(app_repo_root=repo, vault_root=vault)

    assert written == ["Vault Admin/Policies/capture.md"]
    body = (vault / "Vault Admin" / "Policies" / "capture.md").read_text(encoding="utf-8")
    assert "Policy: capture" in body
    assert "version: 1" in body


def test_command_center_validate_and_sync_policies(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "policies").mkdir(parents=True)
    (repo / "policies" / "capture.yml").write_text(
        "id: capture\nversion: 1\nsummary: Capture policy\n",
        encoding="utf-8",
    )
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=tmp_path / "vault",
        app_repo_root=repo,
        codex_enabled=False,
        smtp_enabled=False,
    )
    settings.vault_root.mkdir()
    client = TestClient(create_app(settings=settings))

    validate = client.post("/api/commands/validate-vault")
    sync = client.post("/api/commands/sync-policies")

    assert validate.status_code == 200
    assert validate.json()["ok"] is True
    assert sync.status_code == 200
    assert sync.json()["written"] == ["Vault Admin/Policies/capture.md"]
