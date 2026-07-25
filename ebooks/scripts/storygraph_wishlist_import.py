#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_IMPORT_DIR = Path(__file__).resolve().parents[1] / "imports" / "storygraph"
DEFAULT_REPORT = Path(__file__).resolve().parents[1] / "reports" / "storygraph-wishlist-report.md"
DEFAULT_OUTPUT = DEFAULT_IMPORT_DIR / "lazylibrarian-eBook-wishlist.csv"
DEFAULT_CALIBRE_DB = Path("/mnt/data_14tb/media/books/metadata.db")
DEFAULT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
DEFAULT_WANTED_STATUSES = {"to-read", "to read", "tbr", "currently-reading", "currently reading"}
ERROR_REASONS = {"missing_title", "missing_author"}

TITLE_COLUMNS = ("title", "book title", "book")
AUTHOR_COLUMNS = ("authors", "author", "book author")
ISBN_COLUMNS = ("isbn", "isbn13", "isbn/uid", "isbn uid", "isbn-13")
STATUS_COLUMNS = ("read status", "exclusive shelf", "shelf", "status", "owned")


@dataclass(frozen=True)
class WishlistRow:
    title: str
    author: str
    isbn: str


@dataclass(frozen=True)
class ReviewItem:
    row_number: int
    reason: str
    title: str = ""
    author: str = ""
    detail: str = ""


def normalized_key(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def normalized_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def first_value(row: dict[str, str], candidates: tuple[str, ...]) -> str:
    normalized = {normalized_key(key): value for key, value in row.items()}
    for candidate in candidates:
        value = normalized.get(normalized_key(candidate), "")
        if value and value.strip():
            return value.strip()
    return ""


def clean_isbn(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit() or ch.upper() == "X")


def newest_csv(import_dir: Path) -> Path:
    candidates = [
        path
        for path in import_dir.glob("*.csv")
        if path.name != DEFAULT_OUTPUT.name and not path.name.startswith("lazylibrarian-")
    ]
    if not candidates:
        raise FileNotFoundError(f"no StoryGraph CSV files found in {import_dir}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def calibre_books(calibre_db: Path | None) -> set[tuple[str, str]]:
    if not calibre_db or not calibre_db.exists():
        return set()
    conn = sqlite3.connect(calibre_db)
    try:
        rows = conn.execute(
            """
            select books.title, authors.name
            from books
            join books_authors_link on books.id = books_authors_link.book
            join authors on authors.id = books_authors_link.author
            """
        ).fetchall()
    finally:
        conn.close()
    return {(normalized_text(title), normalized_text(author)) for title, author in rows}


def parse_storygraph_csv(
    source: Path,
    existing_books: set[tuple[str, str]],
    wanted_statuses: set[str],
) -> tuple[list[WishlistRow], list[ReviewItem]]:
    wanted: list[WishlistRow] = []
    review: list[ReviewItem] = []
    seen: set[tuple[str, str]] = set()

    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{source} has no CSV header")

        for row_number, row in enumerate(reader, start=2):
            title = first_value(row, TITLE_COLUMNS)
            author = first_value(row, AUTHOR_COLUMNS)
            isbn = clean_isbn(first_value(row, ISBN_COLUMNS))
            status = normalized_text(first_value(row, STATUS_COLUMNS))

            if status and status not in wanted_statuses:
                review.append(ReviewItem(row_number, "status_not_wanted", title, author, status))
                continue
            if not title:
                review.append(ReviewItem(row_number, "missing_title", title, author))
                continue
            if not author:
                review.append(ReviewItem(row_number, "missing_author", title, author))
                continue

            key = (normalized_text(title), normalized_text(author))
            if key in existing_books:
                review.append(ReviewItem(row_number, "already_in_calibre", title, author))
                continue
            if key in seen:
                review.append(ReviewItem(row_number, "duplicate_in_csv", title, author))
                continue

            seen.add(key)
            wanted.append(WishlistRow(title=title, author=author, isbn=isbn))

    return wanted, review


def write_wishlist(path: Path, rows: list[WishlistRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Title", "Author", "ISBN13"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"Title": row.title, "Author": row.author, "ISBN13": row.isbn})


def write_report(path: Path, source: Path, wanted: list[WishlistRow], review: list[ReviewItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# StoryGraph Wishlist Import Report",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Source: `{source}`",
        f"- Wanted rows written: {len(wanted)}",
        f"- Review rows: {len(review)}",
        "",
        "## Review Rows",
        "",
    ]
    if not review:
        lines.append("No review rows.")
    else:
        lines.append("| Row | Reason | Title | Author | Detail |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in review:
            lines.append(
                f"| {item.row_number} | {item.reason} | {item.title or ''} | {item.author or ''} | {item.detail or ''} |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def call_lazylibrarian(
    api_url: str,
    api_key: str,
    command: str,
    directory: Path | None = None,
    wait: bool = False,
    timeout: int = 30,
    extra_params: dict[str, str] | None = None,
) -> str:
    params = {"apikey": api_key, "cmd": command}
    if extra_params:
        params.update(extra_params)
    if directory is not None:
        params["dir"] = str(directory)
    if wait:
        params["wait"] = "1"
    url = f"{api_url.rstrip('/')}/api?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def best_lazylibrarian_match(payload: str) -> str | None:
    try:
        results = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(results, list) or not results:
        return None

    def score(item: object) -> tuple[float, float, float]:
        if not isinstance(item, dict):
            return (0.0, 0.0, 0.0)
        return (
            float(item.get("highest_fuzz") or 0),
            float(item.get("book_fuzz") or 0),
            float(item.get("author_fuzz") or 0),
        )

    best = max(results, key=score)
    if not isinstance(best, dict):
        return None
    highest_fuzz, book_fuzz, author_fuzz = score(best)
    bookid = best.get("bookid")
    if isinstance(bookid, str) and bookid and highest_fuzz >= 80 and book_fuzz >= 80 and author_fuzz >= 60:
        return bookid
    return None


def import_wishlist_via_lazylibrarian_api(
    api_url: str,
    api_key: str,
    rows: list[WishlistRow],
    timeout: int,
) -> list[ReviewItem]:
    review: list[ReviewItem] = []
    for index, row in enumerate(rows, start=1):
        payload = call_lazylibrarian(
            api_url,
            api_key,
            "findBook",
            timeout=timeout,
            extra_params={"name": f"{row.title} {row.author}"},
        )
        bookid = best_lazylibrarian_match(payload)
        if not bookid:
            review.append(ReviewItem(index, "lazylibrarian_no_match", row.title, row.author))
            continue
        call_lazylibrarian(api_url, api_key, "addBook", wait=True, timeout=timeout, extra_params={"id": bookid})
        queued = call_lazylibrarian(api_url, api_key, "queueBook", timeout=timeout, extra_params={"id": bookid})
        if "OK" not in queued:
            review.append(ReviewItem(index, "lazylibrarian_queue_failed", row.title, row.author, queued))
    return review


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def read_secret_file(path: str | None) -> str:
    if not path:
        return ""
    secret_path = Path(path)
    if not secret_path.exists():
        return ""
    return secret_path.read_text(encoding="utf-8").strip()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert newest StoryGraph CSV export to a LazyLibrarian wishlist CSV.")
    parser.add_argument("--import-dir", type=Path, default=DEFAULT_IMPORT_DIR)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--calibre-db", type=Path, default=DEFAULT_CALIBRE_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--wanted-status", action="append", default=[])
    parser.add_argument("--import-lazylibrarian", action="store_true")
    parser.add_argument("--search", action="store_true")
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE)
    parser.add_argument("--lazylibrarian-url")
    parser.add_argument("--lazylibrarian-api-key")
    parser.add_argument("--lazylibrarian-import-dir", type=Path)
    parser.add_argument("--lazylibrarian-timeout", type=int, default=600)
    parser.add_argument("--lazylibrarian-import-mode", choices=("api", "csv"), default="api")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    env_file = load_env_file(args.env_file)
    lazylibrarian_url = (
        args.lazylibrarian_url
        or os.environ.get("LAZYLIBRARIAN_URL")
        or env_file.get("LAZYLIBRARIAN_URL")
        or "http://127.0.0.1:5299"
    )
    lazylibrarian_api_key = (
        args.lazylibrarian_api_key
        or os.environ.get("LAZYLIBRARIAN_API_KEY")
        or read_secret_file(os.environ.get("LAZYLIBRARIAN_API_KEY_FILE"))
        or env_file.get("LAZYLIBRARIAN_API_KEY", "")
    )
    source = args.source or newest_csv(args.import_dir)
    wanted_statuses = {normalized_text(status) for status in args.wanted_status} or DEFAULT_WANTED_STATUSES

    existing = calibre_books(args.calibre_db)
    wanted, review = parse_storygraph_csv(source, existing, wanted_statuses)
    write_wishlist(args.output, wanted)
    write_report(args.report, source, wanted, review)

    if args.import_lazylibrarian:
        if not lazylibrarian_api_key:
            raise SystemExit("LAZYLIBRARIAN_API_KEY is required for --import-lazylibrarian")
        if args.lazylibrarian_import_mode == "csv":
            call_lazylibrarian(
                lazylibrarian_url,
                lazylibrarian_api_key,
                "importCSVwishlist",
                args.lazylibrarian_import_dir or args.output.parent,
                wait=True,
                timeout=args.lazylibrarian_timeout,
            )
        else:
            review.extend(import_wishlist_via_lazylibrarian_api(lazylibrarian_url, lazylibrarian_api_key, wanted, args.lazylibrarian_timeout))
            write_report(args.report, source, wanted, review)
        if args.search:
            call_lazylibrarian(
                lazylibrarian_url,
                lazylibrarian_api_key,
                "forceBookSearch",
                timeout=args.lazylibrarian_timeout,
                extra_params={"type": "eBook"},
            )

    return 2 if any(item.reason in ERROR_REASONS for item in review) else 0


if __name__ == "__main__":
    raise SystemExit(main())
