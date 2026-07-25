from __future__ import annotations

import subprocess
from pathlib import Path


VAULT_GITIGNORE = """# vault-inbox protected paths
.obsidian/
.trash/
.claude/
.claudian/
Therapy/Transcripts/
Therapy/Summaries/
Therapy/Archive/

# secrets and local state
*.key
*.pem
*.crt
*.p12
*.pfx
.env
*.env
"""


class GitOps:
    def __init__(self, vault_root: Path) -> None:
        self.vault_root = vault_root

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.vault_root), *args],
            check=True,
            text=True,
            capture_output=True,
        )

    def is_repo(self) -> bool:
        return (self.vault_root / ".git").exists()

    def ensure_repo(self) -> dict[str, object]:
        self.vault_root.mkdir(parents=True, exist_ok=True)
        initialized = False
        if not self.is_repo():
            subprocess.run(["git", "init", str(self.vault_root)], check=True, text=True, capture_output=True)
            initialized = True
        subprocess.run(
            ["git", "config", "--global", "--add", "safe.directory", str(self.vault_root)],
            check=False,
            text=True,
            capture_output=True,
        )
        self._run("config", "user.name", "vault-inbox")
        self._run("config", "user.email", "vault-inbox@ethan-herring.com")
        gitignore_changed = self._ensure_gitignore()
        if gitignore_changed:
            self._run("add", "--", ".gitignore")
            staged = self._run("diff", "--cached", "--name-only").stdout.strip()
            if staged:
                self._run("commit", "-m", "vault-inbox initialize protected gitignore")
        return {"ok": True, "initialized": initialized, "path": str(self.vault_root)}

    def _ensure_gitignore(self) -> bool:
        path = self.vault_root / ".gitignore"
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        additions = []
        for line in VAULT_GITIGNORE.splitlines():
            if line and line not in existing:
                additions.append(line)
        if additions:
            separator = "\n" if existing and not existing.endswith("\n") else ""
            path.write_text(existing + separator + "\n".join(additions) + "\n", encoding="utf-8")
            return True
        return False

    def status_short(self) -> list[str]:
        if not self.is_repo():
            return []
        result = self._run("status", "--short")
        return [line for line in result.stdout.splitlines() if line.strip()]

    def changed_paths(self, *, include_ignored: bool = False) -> list[str]:
        if not self.is_repo():
            return []
        args = ["status", "--porcelain=v1", "-z", "--untracked-files=all"]
        if include_ignored:
            args.append("--ignored=matching")
        output = self._run(*args).stdout
        paths: list[str] = []
        parts = [part for part in output.split("\0") if part]
        index = 0
        while index < len(parts):
            entry = parts[index]
            status = entry[:2]
            path = entry[3:]
            if status.startswith("R") or status.startswith("C"):
                index += 1
                if index < len(parts):
                    path = parts[index]
            paths.append(path)
            index += 1
        return paths

    def commit_paths(self, paths: list[str], message: str) -> str | None:
        self.ensure_repo()
        if not paths:
            return None
        self._run("add", "--", *paths)
        staged = self._run("diff", "--cached", "--name-only").stdout.strip()
        if not staged:
            return None
        self._run("commit", "-m", message)
        return self._run("rev-parse", "--short", "HEAD").stdout.strip()
