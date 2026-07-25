from __future__ import annotations

from pathlib import Path

from .git_ops import GitOps
from .dashboard import write_dashboards
from .ollama import check_ollama as check_ollama_live
from .policy import PolicyEngine
from .policy_sync import sync_policies_to_vault
from .search import search_notes
from .store import Store


MANAGED_VALIDATION_PREFIXES = (
    "Vault Admin/Inbox/",
    "Vault Admin/Policies/",
    "Vault Admin/Dashboards/",
)

IGNORED_VALIDATION_PATHS = {
    "AGENTS.md",
}

COMMANDS = [
    {"id": "validate-vault", "label": "Validate vault", "description": "Run policy checks over managed Markdown notes."},
    {"id": "sync-policies", "label": "Sync policies", "description": "Render canonical policy YAML into Vault Admin."},
    {"id": "init-git", "label": "Initialize Git", "description": "Create local-only vault Git repo and protected .gitignore."},
    {"id": "process-next", "label": "Process next job", "description": "Run one queued capture job."},
    {"id": "queue-reruns", "label": "Queue reruns", "description": "Queue action-needed jobs for Codex processing."},
    {"id": "reindex-notes", "label": "Reindex notes", "description": "Refresh lexical note index."},
    {"id": "test-smtp", "label": "Test SMTP", "description": "Send or simulate the fallback alert path."},
    {"id": "check-ollama", "label": "Check Ollama", "description": "Check local embedding service reachability."},
    {"id": "write-dashboards", "label": "Write dashboards", "description": "Generate Obsidian-native Vault Admin dashboards."},
]


def validate_vault(vault_root: Path) -> dict[str, object]:
    policy = PolicyEngine.default(vault_root=vault_root)
    failures = []
    legacy_backlog = []
    ignored = []
    for path in sorted(vault_root.rglob("*.md")):
        rel = policy.normalize_path(path)
        if rel in IGNORED_VALIDATION_PATHS or policy.is_hidden_or_protected(rel) or policy.is_therapy_history(rel):
            ignored.append(rel)
            continue
        errors = policy.validate_markdown_file(path)
        if rel.startswith(MANAGED_VALIDATION_PREFIXES):
            failures.extend(errors)
        elif errors:
            legacy_backlog.append({"path": rel, "issues": [error.__dict__ for error in errors]})
    return {
        "ok": not failures,
        "failure_count": len(failures),
        "failures": [failure.__dict__ for failure in failures[:100]],
        "legacy_backlog_count": len(legacy_backlog),
        "legacy_backlog": legacy_backlog[:100],
        "ignored_count": len(ignored),
        "ignored": ignored[:100],
    }


def init_git(vault_root: Path) -> dict[str, object]:
    return GitOps(vault_root).ensure_repo()


def sync_policies(app_repo_root: Path, vault_root: Path) -> dict[str, object]:
    return {"ok": True, "written": sync_policies_to_vault(app_repo_root=app_repo_root, vault_root=vault_root)}


def reindex_notes(vault_root: Path) -> dict[str, object]:
    results = search_notes(vault_root, "", limit=5000)
    return {"ok": True, "indexed": len(results)}


def queue_reruns(store: Store) -> dict[str, object]:
    queued = store.queue_action_needed_jobs()
    return {"ok": True, "queued": len(queued), "jobs": queued}


def write_vault_dashboards(vault_root: Path) -> dict[str, object]:
    return {"ok": True, "written": write_dashboards(vault_root)}


def check_ollama(base_url: str, model: str) -> dict[str, object]:
    return check_ollama_live(base_url, model)
