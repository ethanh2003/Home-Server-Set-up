from pathlib import Path

from fastapi.testclient import TestClient

from vault_inbox.app import create_app
from vault_inbox.config import Settings
from vault_inbox.commands import validate_vault
from vault_inbox.store import Store


def test_command_center_exposes_named_actions(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=tmp_path / "vault",
        app_repo_root=tmp_path / "repo",
        codex_enabled=False,
        smtp_enabled=False,
    )
    settings.vault_root.mkdir()
    settings.app_repo_root.mkdir()
    client = TestClient(create_app(settings=settings))

    response = client.get("/api/commands")

    assert response.status_code == 200
    actions = {action["id"] for action in response.json()["actions"]}
    assert {
        "validate-vault",
        "sync-policies",
        "init-git",
        "process-next",
        "reindex-notes",
        "test-smtp",
        "check-ollama",
        "queue-reruns",
    }.issubset(actions)


def test_validate_vault_separates_app_health_from_legacy_cleanup_backlog(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "AGENTS.md").write_text("# Agent instructions\n", encoding="utf-8")
    legacy = vault / "Homelab" / "Projects" / "legacy.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("# Legacy note without frontmatter\n", encoding="utf-8")
    managed = vault / "Vault Admin" / "Inbox" / "2026-07-05.md"
    managed.parent.mkdir(parents=True)
    managed.write_text(
        "---\nnote_type: vault_inbox_daily\nstatus: active\ntags:\n  - vault-inbox\n---\n# Daily Inbox\n",
        encoding="utf-8",
    )

    result = validate_vault(vault)

    assert result["ok"] is True
    assert result["failure_count"] == 0
    assert result["legacy_backlog_count"] == 1
    assert result["ignored_count"] == 1


def test_command_center_queues_action_needed_jobs_without_duplicates(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=tmp_path / "vault",
        app_repo_root=tmp_path / "repo",
        codex_enabled=False,
        smtp_enabled=False,
    )
    settings.vault_root.mkdir()
    settings.app_repo_root.mkdir()
    store = Store(settings.database_path)
    capture = store.create_capture(content="Needs AI organization.", hint=None, content_type="text")
    old_job = store.create_job(capture_id=capture["id"], job_type="capture")
    store.update_job(old_job["id"], status="needs_rerun", last_error="Codex disabled")
    client = TestClient(create_app(settings=settings))

    first = client.post("/api/commands/queue-reruns")
    second = client.post("/api/commands/queue-reruns")

    assert first.status_code == 200
    assert first.json()["queued"] == 1
    assert second.status_code == 200
    assert second.json()["queued"] == 0
    jobs = Store(settings.database_path).list_jobs()
    assert sum(1 for job in jobs if job["status"] == "queued") == 1


def test_command_center_does_not_queue_superseded_action_needed_jobs(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=tmp_path / "vault",
        app_repo_root=tmp_path / "repo",
        codex_enabled=False,
        smtp_enabled=False,
    )
    settings.vault_root.mkdir()
    settings.app_repo_root.mkdir()
    store = Store(settings.database_path)
    capture = store.create_capture(content="Already handled later.", hint=None, content_type="text")
    old_job = store.create_job(capture_id=capture["id"], job_type="capture")
    store.update_job(old_job["id"], status="needs_review", last_error="Old validation failure")
    newer_job = store.create_job(capture_id=capture["id"], job_type="capture")
    store.update_job(newer_job["id"], status="completed", commit_sha="abc1234")
    client = TestClient(create_app(settings=settings))

    response = client.post("/api/commands/queue-reruns")

    assert response.status_code == 200
    assert response.json()["queued"] == 0
    jobs = Store(settings.database_path).list_jobs()
    assert sum(1 for job in jobs if job["status"] == "queued") == 0
