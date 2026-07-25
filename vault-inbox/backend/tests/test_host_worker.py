from pathlib import Path

from vault_inbox.config import Settings
from vault_inbox.host_worker import process_once


def test_host_worker_forces_codex_enabled_for_processing(tmp_path: Path, monkeypatch) -> None:
    seen = {}

    class FakeWorker:
        def __init__(self, *, settings, store) -> None:
            seen["settings"] = settings
            seen["store"] = store

        def process_next(self):
            return {"job_id": "job-1", "status": "completed"}

    monkeypatch.setattr("vault_inbox.host_worker.Worker", FakeWorker)
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=tmp_path / "vault",
        app_repo_root=tmp_path / "repo",
        codex_enabled=False,
        smtp_enabled=False,
    )
    settings.vault_root.mkdir()
    settings.app_repo_root.mkdir()

    result = process_once(settings)

    assert result == {"job_id": "job-1", "status": "completed"}
    assert seen["settings"].codex_enabled is True
