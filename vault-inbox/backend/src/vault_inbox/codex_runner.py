from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings
from .git_ops import GitOps
from .policy import PolicyEngine, ValidationError


def build_codex_prompt(*, capture: dict[str, str], related_notes: list[dict[str, str]]) -> str:
    related = "\n".join(f"- {item['path']}: {item['title']}" for item in related_notes[:12])
    return f"""You are processing one vault-inbox capture for Ethan's Obsidian vault.

Hard guardrails:
- Edit only allowed Markdown paths in Vault Admin, Personal, Work, Homelab, or current Therapy Intake.
- Do not read or modify old Therapy transcripts, summaries, archive notes, hidden folders, plugin configs, or secrets.
- Preserve a daily Vault Admin inbox trail and add YAML frontmatter to new notes.
- Use sparse controlled tags, wikilinks, and Obsidian Tasks checkbox syntax when tasks are explicit.
- If uncertain, make the smallest useful update and leave an audit note.

Capture ID: {capture['id']}
Created: {capture['created_at']}
Hint: {capture.get('hint') or ''}
Source URL: {capture.get('source_url') or ''}

Capture:
{capture['content']}

Candidate related notes:
{related or '- none'}
"""


class CodexRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, *, capture: dict[str, str], related_notes: list[dict[str, str]], job_id: str) -> dict[str, object]:
        log_dir = self.settings.app_repo_root / "logs" / "codex"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        prompt_path = log_dir / f"{timestamp}-{job_id}.prompt.md"
        output_path = log_dir / f"{timestamp}-{job_id}.output.log"
        prompt = build_codex_prompt(capture=capture, related_notes=related_notes)
        prompt_path.write_text(prompt, encoding="utf-8")
        command = [
            self.settings.codex_binary,
            "exec",
            "-C",
            str(self.settings.vault_root),
            "--sandbox",
            "workspace-write",
            "--skip-git-repo-check",
            "-",
        ]
        proc = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=self.settings.codex_timeout_seconds,
        )
        output_path.write_text(proc.stdout + "\n\nSTDERR:\n" + proc.stderr, encoding="utf-8")
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "prompt_path": str(prompt_path),
            "output_path": str(output_path),
            "stderr": proc.stderr[-4000:],
        }

    def run_and_validate(
        self,
        *,
        capture: dict[str, str],
        related_notes: list[dict[str, str]],
        job_id: str,
        commit_message: str,
    ) -> dict[str, object]:
        git = GitOps(self.settings.vault_root)
        git.ensure_repo()
        policy = PolicyEngine.default(vault_root=self.settings.vault_root)
        ignored_before = set(git.changed_paths(include_ignored=True))
        protected_before = self._protected_snapshot(policy)
        dirty_before = git.changed_paths(include_ignored=False)
        if dirty_before:
            return {
                "ok": False,
                "returncode": None,
                "changed_paths": dirty_before,
                "validation_errors": [
                    {
                        "code": "preexisting_dirty_vault",
                        "path": path,
                        "message": "Vault has uncommitted changes before Codex processing.",
                    }
                    for path in dirty_before
                ],
                "commit_sha": None,
                "stderr": "Vault has uncommitted changes before Codex processing.",
            }

        result = self.run(capture=capture, related_notes=related_notes, job_id=job_id)
        changed_paths = self._changed_paths_since(
            git=git,
            ignored_before=ignored_before,
            protected_before=protected_before,
            policy=policy,
        )
        result["changed_paths"] = changed_paths
        if not result["ok"]:
            result["validation_errors"] = []
            result["commit_sha"] = None
            return result

        errors = self._validate_changed_paths(changed_paths, policy=policy)
        result["validation_errors"] = [error.__dict__ for error in errors]
        if errors:
            result["ok"] = False
            result["commit_sha"] = None
            return result

        committable = git.changed_paths(include_ignored=False)
        result["commit_sha"] = git.commit_paths(committable, commit_message)
        return result

    def _changed_paths_since(
        self,
        *,
        git: GitOps,
        ignored_before: set[str],
        protected_before: dict[str, tuple[int, int]],
        policy: PolicyEngine,
    ) -> list[str]:
        visible_changes = set(git.changed_paths(include_ignored=False))
        ignored_delta = set(git.changed_paths(include_ignored=True)) - ignored_before
        protected_after = self._protected_snapshot(policy)
        protected_delta = {
            path
            for path in set(protected_before) | set(protected_after)
            if protected_before.get(path) != protected_after.get(path)
        }
        return sorted(visible_changes | ignored_delta | protected_delta)

    def _protected_snapshot(self, policy: PolicyEngine) -> dict[str, tuple[int, int]]:
        paths: dict[str, tuple[int, int]] = {}
        protected_roots = policy.protected_prefixes + policy.therapy_history_prefixes
        for root_name in protected_roots:
            root = self.settings.vault_root / root_name.rstrip("/")
            if not root.exists():
                continue
            self._add_snapshot_path(root, paths, policy=policy)
            if root.is_dir():
                for child in root.rglob("*"):
                    self._add_snapshot_path(child, paths, policy=policy)
        return paths

    def _add_snapshot_path(
        self,
        path: Path,
        paths: dict[str, tuple[int, int]],
        *,
        policy: PolicyEngine,
    ) -> None:
        try:
            stat = path.stat()
        except FileNotFoundError:
            return
        normalized = policy.normalize_path(path)
        if path.is_dir():
            normalized = f"{normalized.rstrip('/')}/"
        paths[normalized] = (stat.st_mtime_ns, stat.st_size)

    def _validate_changed_paths(self, paths: list[str], *, policy: PolicyEngine | None = None) -> list[ValidationError]:
        policy = policy or PolicyEngine.default(vault_root=self.settings.vault_root)
        errors: list[ValidationError] = []
        for path in paths:
            path_errors = policy.validate_changed_paths([path], workflow="capture")
            errors.extend(path_errors)
            full_path = self.settings.vault_root / path
            if not path_errors and full_path.suffix == ".md" and full_path.exists():
                errors.extend(policy.validate_markdown_file(full_path))
        return errors
