from pathlib import Path
from datetime import date

from vault_inbox.config import Settings
from vault_inbox.git_ops import GitOps
from vault_inbox.store import Store
from vault_inbox.worker import Worker


def test_worker_capture_only_fallback_writes_inbox_and_marks_action_needed(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=vault,
        app_repo_root=tmp_path / "repo",
        codex_enabled=False,
        smtp_enabled=False,
    )
    settings.app_repo_root.mkdir()
    store = Store(settings.database_path)
    capture = store.create_capture(content="A second-brain thought", hint=None, content_type="text")
    job = store.create_job(capture_id=capture["id"], job_type="capture")

    result = Worker(settings=settings, store=store).process_next()

    inbox_note = vault / "Vault Admin" / "Inbox" / f"{date.today().isoformat()}.md"
    assert result is not None
    assert result["status"] == "capture_only"
    assert inbox_note.exists()
    assert "A second-brain thought" in inbox_note.read_text(encoding="utf-8")
    assert store.get_job(job["id"])["status"] == "needs_rerun"
    assert (vault / ".git").exists()


def test_capture_only_writer_is_idempotent_for_same_capture(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=vault,
        app_repo_root=tmp_path / "repo",
        codex_enabled=False,
        smtp_enabled=False,
    )
    settings.app_repo_root.mkdir()
    store = Store(settings.database_path)
    capture = store.create_capture(content="Do not duplicate this capture.", hint=None, content_type="text")
    worker = Worker(settings=settings, store=store)

    worker._write_capture_only(job_id="job-1", capture=capture)
    worker._write_capture_only(job_id="job-1", capture=capture)

    note = vault / "Vault Admin" / "Inbox" / f"{date.today().isoformat()}.md"
    assert note.read_text(encoding="utf-8").count(capture["id"]) == 1


def test_codex_enabled_worker_allows_preexisting_ignored_vault_dirs(tmp_path: Path, monkeypatch) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / ".obsidian").mkdir()
    (vault / ".obsidian" / "workspace.json").write_text("{}", encoding="utf-8")
    settings = Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=vault,
        app_repo_root=tmp_path / "repo",
        codex_enabled=True,
        smtp_enabled=False,
    )
    settings.app_repo_root.mkdir()
    store = Store(settings.database_path)
    capture = store.create_capture(content="A thought to organize", hint=None, content_type="text")
    job = store.create_job(capture_id=capture["id"], job_type="capture")
    calls = []

    class FakeCodexRunner:
        def __init__(self, runner_settings: Settings) -> None:
            self.settings = runner_settings

        def run_and_validate(self, **kwargs):
            calls.append(kwargs)
            git = GitOps(self.settings.vault_root)
            commit_sha = git.commit_paths(
                git.changed_paths(include_ignored=False),
                kwargs["commit_message"],
            )
            return {"ok": True, "commit_sha": commit_sha}

    monkeypatch.setattr("vault_inbox.worker.CodexRunner", FakeCodexRunner)

    result = Worker(settings=settings, store=store).process_next()

    assert result == {"job_id": job["id"], "status": "completed"}
    assert calls
    assert store.get_job(job["id"])["status"] == "completed"
