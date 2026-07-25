from __future__ import annotations

from datetime import date

from .config import Settings
from .codex_runner import CodexRunner
from .git_ops import GitOps
from .search import search_notes
from .smtp import send_alert
from .store import Store


class Worker:
    def __init__(self, *, settings: Settings, store: Store) -> None:
        self.settings = settings
        self.store = store

    def process_next(self) -> dict[str, str] | None:
        self.store.requeue_stale_running_jobs(
            older_than_seconds=self.settings.worker_stale_running_seconds,
        )
        job = self.store.claim_next_queued_job()
        if job is None:
            return None
        capture = self.store.get_capture(job["capture_id"])
        if capture is None:
            self.store.update_job(job["id"], status="failed", last_error="Capture missing")
            return {"job_id": job["id"], "status": "failed"}

        if not self.settings.codex_enabled:
            written_path = self._write_capture_only(job_id=job["id"], capture=capture)
            commit_sha = GitOps(self.settings.vault_root).commit_paths(
                [written_path],
                f"vault-inbox capture-only fallback {job['id'][:8]}",
            )
            self.store.update_job(
                job["id"],
                status="needs_rerun",
                last_error="Codex processing disabled; capture-only fallback written.",
                commit_sha=commit_sha,
            )
            self.store.add_audit_event(
                job_id=job["id"],
                event_type="capture_only",
                message="Capture preserved in Vault Admin inbox; AI organization needs rerun.",
            )
            self._send_fallback_alert(job=job, capture=capture)
            return {"job_id": job["id"], "status": "capture_only"}

        git = GitOps(self.settings.vault_root)
        git.ensure_repo()
        dirty_before = git.changed_paths(include_ignored=False)
        if dirty_before:
            written_path = self._write_capture_only(job_id=job["id"], capture=capture)
            commit_sha = git.commit_paths([written_path], f"vault-inbox capture-only fallback {job['id'][:8]}")
            self.store.update_job(
                job["id"],
                status="needs_review",
                last_error="Vault has uncommitted changes; Codex processing skipped.",
                commit_sha=commit_sha,
            )
            self.store.add_audit_event(
                job_id=job["id"],
                event_type="codex_skipped_dirty_vault",
                message="Codex processing skipped because the vault was dirty before processing.",
            )
            return {"job_id": job["id"], "status": "needs_review"}

        written_path = self._write_capture_only(job_id=job["id"], capture=capture)
        related = search_notes(self.settings.vault_root, capture["content"][:80], limit=10)
        result = CodexRunner(self.settings).run_and_validate(
            capture=capture,
            related_notes=related,
            job_id=job["id"],
            commit_message=f"vault-inbox codex job {job['id'][:8]}",
        )
        if not result["ok"]:
            commit_sha = GitOps(self.settings.vault_root).commit_paths(
                [written_path],
                f"vault-inbox capture-only fallback {job['id'][:8]}",
            )
            self.store.update_job(
                job["id"],
                status="needs_rerun",
                last_error=str(result.get("stderr") or "Codex failed"),
                commit_sha=commit_sha,
            )
            self.store.add_audit_event(
                job_id=job["id"],
                event_type="codex_failed_validation" if result.get("validation_errors") else "codex_failed",
                message=str(result.get("validation_errors") or result.get("stderr") or "Codex failed"),
            )
            self._send_fallback_alert(job=job, capture=capture)
            return {"job_id": job["id"], "status": "capture_only"}
        self.store.update_job(job["id"], status="completed", commit_sha=str(result.get("commit_sha") or ""))
        self.store.add_audit_event(job_id=job["id"], event_type="completed", message="Codex processing completed.")
        return {"job_id": job["id"], "status": "completed"}

    def _write_capture_only(self, *, job_id: str, capture: dict[str, str]) -> str:
        inbox_dir = self.settings.vault_root / "Vault Admin" / "Inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        note_path = inbox_dir / f"{date.today().isoformat()}.md"
        if not note_path.exists():
            note_path.write_text(
                "---\nnote_type: vault_inbox_daily\nstatus: active\ntags:\n  - vault-admin\n  - vault-inbox\n---\n"
                f"# Vault Inbox {date.today().isoformat()}\n\n",
                encoding="utf-8",
            )
        elif capture["id"] in note_path.read_text(encoding="utf-8"):
            return note_path.relative_to(self.settings.vault_root).as_posix()
        hint = f"\n- Hint: {capture['hint']}" if capture.get("hint") else ""
        source = f"\n- Source: {capture['source_url']}" if capture.get("source_url") else ""
        with note_path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"## Capture {capture['created_at']}\n\n"
                f"- Capture ID: `{capture['id']}`\n"
                f"- Job ID: `{job_id}`"
                f"{hint}{source}\n\n"
                f"{capture['content']}\n\n"
            )
        return note_path.relative_to(self.settings.vault_root).as_posix()

    def _send_fallback_alert(self, *, job: dict[str, str], capture: dict[str, str]) -> None:
        if not self.settings.smtp_enabled:
            return
        try:
            send_alert(
                self.settings,
                subject="vault-inbox capture needs AI rerun",
                body=(
                    "vault-inbox preserved a capture but did not complete AI organization.\n\n"
                    f"Job: {job['id']}\n"
                    f"Capture: {capture['id']}\n"
                    "Open the PWA command center to rerun it."
                ),
            )
        except Exception as exc:
            self.store.add_audit_event(
                job_id=job["id"],
                event_type="smtp_failed",
                message=f"Failed to send fallback alert: {exc}",
            )
