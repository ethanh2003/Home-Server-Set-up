from __future__ import annotations

from datetime import date
from pathlib import Path


def write_dashboards(vault_root: Path) -> list[str]:
    dashboard_dir = vault_root / "Vault Admin" / "Dashboards"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    dashboard = dashboard_dir / "Vault Inbox Dashboard.md"
    dashboard.write_text(
        "---\n"
        "note_type: vault_inbox_dashboard\n"
        "status: active\n"
        f"last_updated: {date.today().isoformat()}\n"
        "tags:\n"
        "  - vault-admin\n"
        "  - vault-inbox/dashboard\n"
        "---\n"
        "# Vault Inbox Dashboard\n\n"
        "## Current Workflow\n\n"
        "- Capture from the PWA at `inbox.ethan-herring.com`.\n"
        "- Review recent capture-only fallbacks in `Vault Admin/Inbox/`.\n"
        "- Use the PWA command center for validation, policy sync, reindexing, and cleanup dry runs.\n\n"
        "## Important Areas\n\n"
        "- [[Vault Admin/Policies/capture]]\n"
        "- [[Vault Admin/Policies/audit]]\n"
        "- [[Vault Admin/Review Queue/Vault Sync Review Queue]]\n\n"
        "## Guardrails\n\n"
        "- Hidden folders, plugin configs, secrets, old Therapy transcripts, old Therapy summaries, and Therapy archive notes are protected.\n"
        "- New/current Therapy captures may update active intake only.\n"
        "- Plugin changes require explicit approval.\n",
        encoding="utf-8",
    )
    return [dashboard.relative_to(vault_root).as_posix()]
