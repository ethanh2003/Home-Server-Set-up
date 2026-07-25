from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

import frontmatter


@dataclass(frozen=True)
class ValidationError:
    code: str
    path: str
    message: str


class PolicyEngine:
    """Machine-enforced guardrails for Codex-created vault changes."""

    protected_prefixes = (
        ".obsidian/",
        ".trash/",
        ".claude/",
        ".claudian/",
    )
    secret_suffixes = (
        ".key",
        ".pem",
        ".crt",
        ".p12",
        ".pfx",
        ".env",
        "id_rsa",
        "id_ed25519",
    )
    therapy_history_prefixes = (
        "Therapy/Transcripts/",
        "Therapy/Summaries/",
        "Therapy/Archive/",
    )
    allowed_write_prefixes = (
        "Vault Admin/",
        "Personal/",
        "Work/",
        "Homelab/",
        "Therapy/Intake/",
        "Therapy/Topics/",
        "Therapy/People/",
    )

    def __init__(self, vault_root: Path) -> None:
        self.vault_root = vault_root

    @classmethod
    def default(cls, vault_root: Path) -> "PolicyEngine":
        return cls(vault_root=vault_root)

    def normalize_path(self, path: str | Path) -> str:
        raw = str(path)
        candidate = Path(raw)
        if candidate.is_absolute():
            try:
                raw = str(candidate.relative_to(self.vault_root))
            except ValueError:
                raw = str(candidate)
        return PurePosixPath(raw).as_posix().lstrip("/")

    def is_hidden_or_protected(self, path: str | Path) -> bool:
        normalized = self.normalize_path(path)
        return any(
            normalized == prefix.rstrip("/") or normalized.startswith(prefix)
            for prefix in self.protected_prefixes
        )

    def is_secret_like(self, path: str | Path) -> bool:
        normalized = self.normalize_path(path).lower()
        name = PurePosixPath(normalized).name
        return any(normalized.endswith(suffix) or name == suffix for suffix in self.secret_suffixes)

    def is_therapy_history(self, path: str | Path) -> bool:
        normalized = self.normalize_path(path)
        return any(
            normalized == prefix.rstrip("/") or normalized.startswith(prefix)
            for prefix in self.therapy_history_prefixes
        )

    def is_allowed_write_path(self, path: str | Path) -> bool:
        normalized = self.normalize_path(path)
        return normalized.startswith(self.allowed_write_prefixes)

    def validate_changed_paths(self, paths: Iterable[str | Path], workflow: str) -> list[ValidationError]:
        errors: list[ValidationError] = []
        for path in paths:
            normalized = self.normalize_path(path)
            if self.is_hidden_or_protected(normalized):
                errors.append(
                    ValidationError(
                        code="protected_path",
                        path=normalized,
                        message="Hidden, plugin, trash, and agent-internal paths are not writable.",
                    )
                )
                continue
            if self.is_secret_like(normalized):
                errors.append(
                    ValidationError(
                        code="secret_like_path",
                        path=normalized,
                        message="Secret-like files must not be written or committed by vault-inbox.",
                    )
                )
                continue
            if workflow in {"capture", "audit", "cleanup"} and self.is_therapy_history(normalized):
                errors.append(
                    ValidationError(
                        code="protected_therapy_history",
                        path=normalized,
                        message="Old Therapy transcripts, summaries, and archive notes are protected.",
                    )
                )
                continue
            if not self.is_allowed_write_path(normalized):
                errors.append(
                    ValidationError(
                        code="write_root_not_allowed",
                        path=normalized,
                        message="Changed path is outside allowed vault write roots.",
                    )
                )
        return errors

    def validate_markdown_file(self, path: Path) -> list[ValidationError]:
        normalized = self.normalize_path(path)
        errors = self.validate_changed_paths([normalized], workflow="capture")
        if path.suffix != ".md" or not path.exists():
            return errors
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            errors.append(
                ValidationError(
                    code="missing_frontmatter",
                    path=normalized,
                    message="Markdown note must start with YAML frontmatter.",
                )
            )
            return errors
        try:
            note = frontmatter.loads(text)
        except Exception as exc:
            errors.append(
                ValidationError(
                    code="invalid_frontmatter",
                    path=normalized,
                    message=f"Frontmatter could not be parsed: {exc}",
                )
            )
            return errors
        if "note_type" not in note.metadata:
            errors.append(
                ValidationError(
                    code="missing_note_type",
                    path=normalized,
                    message="Frontmatter must include note_type.",
                )
            )
        if "# " not in note.content:
            errors.append(
                ValidationError(
                    code="missing_h1",
                    path=normalized,
                    message="Markdown note must include a top-level heading.",
                )
            )
        return errors
