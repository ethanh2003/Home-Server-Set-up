from pathlib import Path
from datetime import date, datetime, timedelta, timezone
import time

from fastapi.testclient import TestClient

from vault_inbox.app import create_app
from vault_inbox.config import Settings
from vault_inbox.store import Store


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=tmp_path / "vault",
        app_repo_root=tmp_path / "repo",
        codex_enabled=False,
        smtp_enabled=False,
    )
    settings.vault_root.mkdir()
    settings.app_repo_root.mkdir()
    return TestClient(create_app(settings=settings))


def test_create_capture_persists_capture_and_job(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/api/captures",
        json={"content": "Remember to make vault-inbox a second brain.", "hint": "project"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["capture"]["content_type"] == "text"
    assert body["job"]["status"] == "queued"

    store = Store(tmp_path / "vault-inbox.sqlite3")
    assert store.list_jobs()[0]["capture_id"] == body["capture"]["id"]


def test_store_claims_next_queued_job_once(tmp_path: Path) -> None:
    store = Store(tmp_path / "vault-inbox.sqlite3")
    capture = store.create_capture(content="Claim me once.", hint=None, content_type="text")
    job = store.create_job(capture_id=capture["id"], job_type="capture")

    claimed = store.claim_next_queued_job()
    second_claim = store.claim_next_queued_job()

    assert claimed is not None
    assert claimed["id"] == job["id"]
    assert claimed["status"] == "running"
    assert claimed["attempts"] == 1
    assert second_claim is None
    assert store.get_job(job["id"])["status"] == "running"


def test_store_requeues_only_stale_running_jobs(tmp_path: Path) -> None:
    store = Store(tmp_path / "vault-inbox.sqlite3")
    old_capture = store.create_capture(content="Old running job.", hint=None, content_type="text")
    old_job = store.create_job(capture_id=old_capture["id"], job_type="capture")
    fresh_capture = store.create_capture(content="Fresh running job.", hint=None, content_type="text")
    fresh_job = store.create_job(capture_id=fresh_capture["id"], job_type="capture")
    store.claim_next_queued_job()
    store.claim_next_queued_job()
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    with store.connect() as conn:
        conn.execute("UPDATE jobs SET updated_at = ? WHERE id = ?", (stale_time, old_job["id"]))

    requeued = store.requeue_stale_running_jobs(older_than_seconds=1800)

    assert [job["id"] for job in requeued] == [old_job["id"]]
    assert store.get_job(old_job["id"])["status"] == "queued"
    assert store.get_job(fresh_job["id"])["status"] == "running"


def test_store_marks_older_jobs_as_superseded(tmp_path: Path) -> None:
    store = Store(tmp_path / "vault-inbox.sqlite3")
    capture = store.create_capture(content="Track current state.", hint=None, content_type="text")
    old_job = store.create_job(capture_id=capture["id"], job_type="capture")
    store.update_job(old_job["id"], status="needs_review", last_error="Old failure")
    new_job = store.create_job(capture_id=capture["id"], job_type="capture")
    store.update_job(new_job["id"], status="completed", commit_sha="abc1234")

    jobs = store.list_jobs()

    by_id = {job["id"]: job for job in jobs}
    assert by_id[new_job["id"]]["superseded"] is False
    assert by_id[old_job["id"]]["superseded"] is True


def test_health_reports_codex_disabled_and_vault_present(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["vault"]["ok"] is True
    assert body["codex"]["enabled"] is False


def test_search_indexes_markdown_notes_without_hidden_paths(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    note = tmp_path / "vault" / "Personal" / "Resources" / "Topics" / "Second Brain.md"
    note.parent.mkdir(parents=True)
    note.write_text(
        "---\nnote_type: personal_topic\ntags:\n  - personal/topic\n---\n# Second Brain\n\nVault inbox captures ideas.\n",
        encoding="utf-8",
    )
    hidden = tmp_path / "vault" / ".obsidian" / "config.md"
    hidden.parent.mkdir()
    hidden.write_text("# secret config\n", encoding="utf-8")

    response = client.get("/api/search", params={"q": "captures"})

    assert response.status_code == 200
    results = response.json()["results"]
    assert [result["path"] for result in results] == [
        "Personal/Resources/Topics/Second Brain.md"
    ]


def test_background_worker_processes_queued_capture(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=tmp_path / "vault",
        app_repo_root=tmp_path / "repo",
        codex_enabled=False,
        smtp_enabled=False,
        worker_enabled=True,
        worker_interval_seconds=0.05,
    )
    settings.vault_root.mkdir()
    settings.app_repo_root.mkdir()

    with TestClient(create_app(settings=settings)) as client:
        response = client.post(
            "/api/captures",
            json={"content": "Background worker should preserve this.", "content_type": "text"},
        )
        assert response.status_code == 201
        job_id = response.json()["job"]["id"]

        deadline = time.time() + 2
        status = "queued"
        while time.time() < deadline:
            jobs = client.get("/api/jobs").json()["jobs"]
            status = next(job["status"] for job in jobs if job["id"] == job_id)
            if status == "needs_rerun":
                break
            time.sleep(0.05)

    assert status == "needs_rerun"
    assert (settings.vault_root / "Vault Admin" / "Inbox" / f"{date.today().isoformat()}.md").exists()
