from __future__ import annotations

import asyncio
import logging

from .config import Settings
from .store import Store
from .worker import Worker

logger = logging.getLogger(__name__)


class BackgroundWorker:
    def __init__(self, *, settings: Settings, store: Store) -> None:
        self.settings = settings
        self.store = store
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if not self.settings.worker_enabled or self._task is not None:
            return
        self._task = asyncio.create_task(self._loop(), name="vault-inbox-worker")

    async def stop(self) -> None:
        self._stop.set()
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                await self.process_once()
            except Exception:
                logger.exception("vault-inbox background worker failed")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.settings.worker_interval_seconds)
            except asyncio.TimeoutError:
                pass

    async def process_once(self) -> dict[str, str] | None:
        async with self._lock:
            return await asyncio.to_thread(Worker(settings=self.settings, store=self.store).process_next)
