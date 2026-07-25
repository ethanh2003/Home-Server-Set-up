#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def newest_csv(import_dir: Path) -> Path | None:
    candidates = [
        path
        for path in import_dir.glob("*.csv")
        if path.name != "lazylibrarian-wishlist.csv" and not path.name.startswith("lazylibrarian-")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def file_fingerprint(path: Path) -> str:
    stat = path.stat()
    return f"{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}"


def process_once(
    *,
    importer: Path,
    import_dir: Path,
    state_file: Path,
    calibre_db: Path,
    output: Path,
    report: Path,
    lazylibrarian_import_dir: Path,
    import_lazylibrarian: bool,
    search: bool,
) -> bool:
    source = newest_csv(import_dir)
    if source is None:
        return False

    fingerprint = file_fingerprint(source)
    previous = state_file.read_text(encoding="utf-8").strip() if state_file.exists() else ""
    if previous == fingerprint:
        return False

    command = [
        sys.executable,
        str(importer),
        "--source",
        str(source),
        "--calibre-db",
        str(calibre_db),
        "--output",
        str(output),
        "--report",
        str(report),
    ]
    if import_lazylibrarian:
        command.append("--import-lazylibrarian")
        command.extend(["--lazylibrarian-import-dir", str(lazylibrarian_import_dir)])
    if search:
        command.append("--search")

    subprocess.run(command, check=True)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(fingerprint, encoding="utf-8")
    return True


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Poll StoryGraph CSV drop folder and run wishlist import on changes.")
    parser.add_argument("--importer", type=Path, default=Path("/scripts/storygraph_wishlist_import.py"))
    parser.add_argument("--import-dir", type=Path, default=Path("/imports/storygraph"))
    parser.add_argument("--state-file", type=Path, default=Path("/state/storygraph-watch.state"))
    parser.add_argument("--calibre-db", type=Path, default=Path("/calibre-library/metadata.db"))
    parser.add_argument("--output", type=Path, default=Path("/imports/storygraph/lazylibrarian-eBook-wishlist.csv"))
    parser.add_argument("--report", type=Path, default=Path("/reports/storygraph-wishlist-report.md"))
    parser.add_argument("--lazylibrarian-import-dir", type=Path, default=Path("/storygraph-imports"))
    parser.add_argument("--interval", type=int, default=int(os.environ.get("STORYGRAPH_WATCH_INTERVAL", "60")))
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--import-lazylibrarian", action="store_true", default=env_bool("STORYGRAPH_IMPORT_LAZYLIBRARIAN"))
    parser.add_argument("--search", action="store_true", default=env_bool("STORYGRAPH_SEARCH_AFTER_IMPORT"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    while True:
        try:
            process_once(
                importer=args.importer,
                import_dir=args.import_dir,
                state_file=args.state_file,
                calibre_db=args.calibre_db,
                output=args.output,
                report=args.report,
                lazylibrarian_import_dir=args.lazylibrarian_import_dir,
                import_lazylibrarian=args.import_lazylibrarian,
                search=args.search,
            )
        except Exception as exc:
            print(f"storygraph-watch: import failed: {exc}", file=sys.stderr, flush=True)

        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
