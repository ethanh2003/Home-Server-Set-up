import os
import subprocess
import sys
from pathlib import Path

from vault_inbox.codex_runner import CodexRunner
from vault_inbox.config import Settings
from vault_inbox.git_ops import GitOps


def make_settings(tmp_path: Path) -> Settings:
    vault = tmp_path / "vault"
    repo = tmp_path / "repo"
    vault.mkdir()
    repo.mkdir()
    return Settings(
        database_path=tmp_path / "vault-inbox.sqlite3",
        vault_root=vault,
        app_repo_root=repo,
        codex_enabled=True,
        smtp_enabled=False,
    )


def write_fake_codex(tmp_path: Path, body: str) -> Path:
    script = tmp_path / "fake_codex.py"
    script.write_text(body, encoding="utf-8")
    script.chmod(0o755)
    return script


def test_codex_runner_uses_current_exec_flags_and_stdin(tmp_path: Path, monkeypatch) -> None:
    settings = make_settings(tmp_path)
    settings.codex_binary = "/usr/local/bin/codex"
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CodexRunner(settings).run(
        capture={
            "id": "capture-1",
            "created_at": "2026-07-05T00:00:00+00:00",
            "content": "Remember this.",
            "hint": None,
            "source_url": None,
        },
        related_notes=[],
        job_id="job-1",
    )

    command, kwargs = calls[0]
    assert result["ok"] is True
    assert command == [
        "/usr/local/bin/codex",
        "exec",
        "-C",
        str(settings.vault_root),
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        "-",
    ]
    assert "--ask-for-approval" not in command
    assert kwargs["input"].startswith("You are processing one vault-inbox capture")


def test_codex_runner_rejects_protected_changed_paths(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    GitOps(settings.vault_root).ensure_repo()
    fake_codex = write_fake_codex(
        tmp_path,
        """#!/usr/bin/env python3
import pathlib
import sys
vault = pathlib.Path(sys.argv[sys.argv.index("-C") + 1])
(vault / ".obsidian").mkdir(exist_ok=True)
(vault / ".obsidian" / "config.md").write_text("secret-ish config", encoding="utf-8")
""",
    )
    settings.codex_binary = str(fake_codex)

    result = CodexRunner(settings).run_and_validate(
        capture={
            "id": "capture-1",
            "created_at": "2026-07-05T00:00:00+00:00",
            "content": "Write a protected file.",
            "hint": None,
            "source_url": None,
        },
        related_notes=[],
        job_id="job-1",
        commit_message="vault-inbox codex job job-1",
    )

    assert result["ok"] is False
    assert result["commit_sha"] is None
    assert result["validation_errors"][0]["code"] == "protected_path"
    assert ".obsidian/" in GitOps(settings.vault_root).changed_paths(include_ignored=True)


def test_codex_runner_allows_preexisting_ignored_vault_dirs(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    GitOps(settings.vault_root).ensure_repo()
    (settings.vault_root / ".obsidian").mkdir()
    (settings.vault_root / ".obsidian" / "workspace.json").write_text("{}", encoding="utf-8")
    fake_codex = write_fake_codex(
        tmp_path,
        """#!/usr/bin/env python3
import pathlib
import sys
vault = pathlib.Path(sys.argv[sys.argv.index("-C") + 1])
note = vault / "Homelab" / "Memory" / "Existing Ignored Dirs.md"
note.parent.mkdir(parents=True, exist_ok=True)
note.write_text(
    "---\\nnote_type: homelab_memory\\ntags:\\n  - homelab/memory\\n---\\n# Existing Ignored Dirs\\n\\nSaved by test.\\n",
    encoding="utf-8",
)
""",
    )
    settings.codex_binary = str(fake_codex)

    result = CodexRunner(settings).run_and_validate(
        capture={
            "id": "capture-1",
            "created_at": "2026-07-05T00:00:00+00:00",
            "content": "Write a valid note with normal vault metadata present.",
            "hint": None,
            "source_url": None,
        },
        related_notes=[],
        job_id="job-1",
        commit_message="vault-inbox codex job job-1",
    )

    assert result["ok"] is True
    assert result["commit_sha"]
    assert result["changed_paths"] == ["Homelab/Memory/Existing Ignored Dirs.md"]


def test_codex_runner_rejects_changes_inside_preexisting_protected_dirs(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    GitOps(settings.vault_root).ensure_repo()
    (settings.vault_root / ".obsidian").mkdir()
    (settings.vault_root / ".obsidian" / "workspace.json").write_text("{}", encoding="utf-8")
    fake_codex = write_fake_codex(
        tmp_path,
        """#!/usr/bin/env python3
import pathlib
import sys
vault = pathlib.Path(sys.argv[sys.argv.index("-C") + 1])
(vault / ".obsidian" / "workspace.json").write_text("{\\"changed\\": true}", encoding="utf-8")
""",
    )
    settings.codex_binary = str(fake_codex)

    result = CodexRunner(settings).run_and_validate(
        capture={
            "id": "capture-1",
            "created_at": "2026-07-05T00:00:00+00:00",
            "content": "Try to edit Obsidian config.",
            "hint": None,
            "source_url": None,
        },
        related_notes=[],
        job_id="job-1",
        commit_message="vault-inbox codex job job-1",
    )

    assert result["ok"] is False
    assert result["commit_sha"] is None
    assert result["validation_errors"][0]["code"] == "protected_path"
    assert result["validation_errors"][0]["path"] == ".obsidian/workspace.json"


def test_codex_runner_commits_allowed_valid_markdown_changes(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    GitOps(settings.vault_root).ensure_repo()
    fake_codex = write_fake_codex(
        tmp_path,
        """#!/usr/bin/env python3
import pathlib
import sys
vault = pathlib.Path(sys.argv[sys.argv.index("-C") + 1])
note = vault / "Homelab" / "Memory" / "Codex Test.md"
note.parent.mkdir(parents=True, exist_ok=True)
note.write_text(
    "---\\nnote_type: homelab_memory\\ntags:\\n  - homelab/memory\\n---\\n# Codex Test\\n\\nSaved by test.\\n",
    encoding="utf-8",
)
""",
    )
    settings.codex_binary = str(fake_codex)

    result = CodexRunner(settings).run_and_validate(
        capture={
            "id": "capture-1",
            "created_at": "2026-07-05T00:00:00+00:00",
            "content": "Write a valid note.",
            "hint": None,
            "source_url": None,
        },
        related_notes=[],
        job_id="job-1",
        commit_message="vault-inbox codex job job-1",
    )

    assert result["ok"] is True
    assert result["commit_sha"]
    assert GitOps(settings.vault_root).status_short() == []
    committed = subprocess.run(
        ["git", "-C", str(settings.vault_root), "show", "--name-only", "--format=", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    assert "Homelab/Memory/Codex Test.md" in committed
