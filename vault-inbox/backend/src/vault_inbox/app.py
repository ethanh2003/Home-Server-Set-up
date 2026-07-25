from __future__ import annotations

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import Settings
from .commands import (
    COMMANDS,
    check_ollama,
    init_git,
    queue_reruns,
    reindex_notes,
    sync_policies,
    validate_vault,
    write_vault_dashboards,
)
from .smtp import send_alert
from .url_ingest import fetch_url_summary
from .search import search_notes
from .store import Store
from .worker import Worker


class CaptureRequest(BaseModel):
    content: str = Field(min_length=1)
    hint: str | None = None
    content_type: str = "text"
    source_url: str | None = None


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    store = Store(settings.database_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        worker = BackgroundWorker(settings=settings, store=store)
        app.state.background_worker = worker
        await worker.start()
        try:
            yield
        finally:
            await worker.stop()

    app = FastAPI(
        title="vault-inbox",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.settings = settings
    app.state.store = store

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins(),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, object]:
        body: dict[str, object] = {
            "app": {"ok": True, "name": "vault-inbox"},
            "vault": {"ok": settings.vault_root.exists()},
            "codex": {"enabled": settings.codex_enabled},
            "ollama": {"model": settings.ollama_embedding_model},
            "smtp": {"enabled": settings.smtp_enabled},
        }
        if settings.health_details_enabled:
            body["vault"]["path"] = str(settings.vault_root)  # type: ignore[index]
            body["codex"]["binary"] = settings.codex_binary  # type: ignore[index]
            body["ollama"]["base_url"] = settings.ollama_base_url  # type: ignore[index]
            body["smtp"]["host"] = settings.smtp_host  # type: ignore[index]
            body["smtp"]["to"] = settings.smtp_to  # type: ignore[index]
        return body

    def run_command(action):
        try:
            return action()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/captures", status_code=201)
    def create_capture(request: CaptureRequest) -> dict[str, object]:
        content = request.content
        source_url = request.source_url
        if request.content_type == "url" and request.source_url:
            try:
                fetched = fetch_url_summary(
                    request.source_url,
                    allow_private_networks=settings.url_ingest_allow_private_networks,
                )
                source_url = fetched["url"]
                content = f"# {fetched['title']}\n\n{request.content}\n\nFetched page text:\n{fetched['content']}"
            except Exception as exc:
                content = f"{request.content}\n\nURL fetch failed: {exc}"
        capture = store.create_capture(
            content=content,
            hint=request.hint,
            content_type=request.content_type,
            source_url=source_url,
        )
        job = store.create_job(capture_id=capture["id"], job_type="capture")
        return {"capture": capture, "job": job}

    @app.get("/api/jobs")
    def list_jobs() -> dict[str, object]:
        return {"jobs": store.list_jobs()}

    @app.post("/api/jobs/{job_id}/rerun")
    def rerun_job(job_id: str) -> dict[str, object]:
        job = store.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        new_job = store.create_job(capture_id=job["capture_id"], job_type=job["job_type"])
        return {"job": new_job}

    @app.post("/api/worker/process-next")
    def process_next() -> dict[str, object]:
        result = Worker(settings=settings, store=store).process_next()
        return {"result": result}

    @app.get("/api/commands")
    def commands() -> dict[str, object]:
        return {"actions": COMMANDS}

    @app.post("/api/commands/validate-vault")
    def command_validate_vault() -> dict[str, object]:
        return run_command(lambda: validate_vault(settings.vault_root))

    @app.post("/api/commands/sync-policies")
    def command_sync_policies() -> dict[str, object]:
        return run_command(lambda: sync_policies(settings.app_repo_root, settings.vault_root))

    @app.post("/api/commands/init-git")
    def command_init_git() -> dict[str, object]:
        return run_command(lambda: init_git(settings.vault_root))

    @app.post("/api/commands/process-next")
    def command_process_next() -> dict[str, object]:
        return run_command(lambda: {"ok": True, "result": Worker(settings=settings, store=store).process_next()})

    @app.post("/api/commands/queue-reruns")
    def command_queue_reruns() -> dict[str, object]:
        return run_command(lambda: queue_reruns(store))

    @app.post("/api/commands/reindex-notes")
    def command_reindex_notes() -> dict[str, object]:
        return run_command(lambda: reindex_notes(settings.vault_root))

    @app.post("/api/commands/test-smtp")
    def command_test_smtp() -> dict[str, object]:
        if not settings.smtp_enabled:
            return {"ok": True, "enabled": False, "message": "SMTP disabled"}
        return run_command(
            lambda: send_alert(
                settings,
                subject="vault-inbox SMTP test",
                body="This is a vault-inbox SMTP test from the PWA command center.",
            )
        )

    @app.post("/api/commands/check-ollama")
    def command_check_ollama() -> dict[str, object]:
        return run_command(lambda: check_ollama(settings.ollama_base_url, settings.ollama_embedding_model))

    @app.post("/api/commands/write-dashboards")
    def command_write_dashboards() -> dict[str, object]:
        return run_command(lambda: write_vault_dashboards(settings.vault_root))

    @app.get("/api/search")
    def search(q: str, limit: int = 25) -> dict[str, object]:
        return {"results": search_notes(settings.vault_root, q, limit=limit)}

    static_dir = settings.app_repo_root / "frontend" / "dist"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

    return app


app = create_app()
from .background import BackgroundWorker
