from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from .config import Settings
from .store import Store
from .worker import Worker

logger = logging.getLogger(__name__)


def host_settings(settings: Settings) -> Settings:
    data = settings.model_dump()
    data["codex_enabled"] = True
    data["worker_enabled"] = False
    return Settings(**data)


def process_once(settings: Settings) -> dict[str, str] | None:
    effective = host_settings(settings)
    store = Store(effective.database_path)
    return Worker(settings=effective, store=store).process_next()


def run_forever(settings: Settings, *, interval_seconds: float) -> None:
    while True:
        try:
            result = process_once(settings)
            if result:
                logger.info("processed vault-inbox job: %s", result)
        except Exception:
            logger.exception("host worker iteration failed")
        time.sleep(interval_seconds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the vault-inbox host Codex worker.")
    parser.add_argument("--once", action="store_true", help="Process one queued job and exit.")
    parser.add_argument("--interval", type=float, default=None, help="Polling interval in seconds.")
    parser.add_argument("--database-path", type=Path, default=None)
    parser.add_argument("--vault-root", type=Path, default=None)
    parser.add_argument("--app-repo-root", type=Path, default=None)
    parser.add_argument("--codex-binary", default=None)
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    overrides = {
        key: value
        for key, value in {
            "database_path": args.database_path,
            "vault_root": args.vault_root,
            "app_repo_root": args.app_repo_root,
            "codex_binary": args.codex_binary,
        }.items()
        if value is not None
    }
    settings = Settings(**overrides)
    if args.once:
        result = process_once(settings)
        logger.info("process_once result: %s", result)
        return 0
    run_forever(settings, interval_seconds=args.interval or settings.worker_interval_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
