#!/usr/bin/env python3
import csv
import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "ebooks" / "scripts" / "storygraph_wishlist_import.py"


def load_module():
    spec = importlib.util.spec_from_file_location("storygraph_wishlist_import", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["storygraph_wishlist_import"] = module
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_calibre_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("create table books (id integer primary key, title text not null)")
        conn.execute("create table authors (id integer primary key, name text not null)")
        conn.execute("create table books_authors_link (book integer not null, author integer not null)")
        conn.execute("insert into books (id, title) values (1, 'Existing Book')")
        conn.execute("insert into authors (id, name) values (1, 'Known Author')")
        conn.execute("insert into books_authors_link (book, author) values (1, 1)")
        conn.commit()
    finally:
        conn.close()


class StoryGraphWishlistImportTests(unittest.TestCase):
    def test_normalizes_storygraph_export_to_lazylibrarian_wishlist(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "storygraph.csv"
            output = tmp_path / "wishlist.csv"
            report = tmp_path / "report.md"
            make_calibre_db(tmp_path / "metadata.db")
            write_csv(
                source,
                [
                    {
                        "Title": "Wanted Book",
                        "Authors": "Ada Writer",
                        "ISBN": "9781234567890",
                        "Read Status": "to-read",
                    },
                    {
                        "Title": "Finished Book",
                        "Authors": "Bea Writer",
                        "ISBN": "9780000000002",
                        "Read Status": "read",
                    },
                ],
            )

            exit_code = module.main(
                [
                    "--source",
                    str(source),
                    "--calibre-db",
                    str(tmp_path / "metadata.db"),
                    "--output",
                    str(output),
                    "--report",
                    str(report),
                ]
            )

            self.assertEqual(exit_code, 0)
            with output.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows, [{"Title": "Wanted Book", "Author": "Ada Writer", "ISBN13": "9781234567890"}])
            self.assertIn("Finished Book", report.read_text(encoding="utf-8"))
            self.assertIn("status_not_wanted", report.read_text(encoding="utf-8"))

    def test_writes_lazylibrarian_compatible_isbn13_header(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "storygraph.csv"
            output = tmp_path / "wishlist.csv"
            report = tmp_path / "report.md"
            write_csv(
                source,
                [{"Title": "ISBN Book", "Authors": "Ada Writer", "ISBN": "978-1-234-56789-0", "Read Status": "to-read"}],
            )

            self.assertEqual(module.main(["--source", str(source), "--output", str(output), "--report", str(report)]), 0)

            with output.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, ["Title", "Author", "ISBN13"])
                self.assertEqual(list(reader), [{"Title": "ISBN Book", "Author": "Ada Writer", "ISBN13": "9781234567890"}])

    def test_skips_books_already_in_calibre_library(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "storygraph.csv"
            output = tmp_path / "wishlist.csv"
            report = tmp_path / "report.md"
            make_calibre_db(tmp_path / "metadata.db")
            write_csv(
                source,
                [
                    {
                        "Book Title": "Existing Book",
                        "Book Author": "Known Author",
                        "ISBN13": "9781234567890",
                        "Exclusive Shelf": "to-read",
                    },
                    {
                        "Book Title": "New Book",
                        "Book Author": "Known Author",
                        "ISBN13": "9781234567891",
                        "Exclusive Shelf": "to-read",
                    },
                ],
            )

            self.assertEqual(
                module.main(
                    [
                        "--source",
                        str(source),
                        "--calibre-db",
                        str(tmp_path / "metadata.db"),
                        "--output",
                        str(output),
                        "--report",
                        str(report),
                    ]
                ),
                0,
            )

            with output.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["Title"] for row in rows], ["New Book"])
            self.assertIn("already_in_calibre", report.read_text(encoding="utf-8"))

    def test_reports_rows_missing_title_or_author_without_partial_failure(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "storygraph.csv"
            output = tmp_path / "wishlist.csv"
            report = tmp_path / "report.md"
            write_csv(
                source,
                [
                    {"Title": "", "Authors": "Ada Writer", "Read Status": "to-read"},
                    {"Title": "Good Book", "Authors": "Ada Writer", "Read Status": "to-read"},
                    {"Title": "No Author", "Authors": "", "Read Status": "to-read"},
                ],
            )

            self.assertEqual(
                module.main(["--source", str(source), "--output", str(output), "--report", str(report)]),
                2,
            )

            with output.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["Title"] for row in rows], ["Good Book"])
            report_text = report.read_text(encoding="utf-8")
            self.assertIn("missing_title", report_text)
            self.assertIn("missing_author", report_text)

    def test_import_lazylibrarian_can_read_untracked_env_file(self):
        module = load_module()
        calls = []
        module.call_lazylibrarian = lambda api_url, api_key, command, directory=None, wait=False, timeout=30, extra_params=None: calls.append(
            (api_url, api_key, command, directory, wait, timeout, extra_params)
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "storygraph.csv"
            output = tmp_path / "wishlist.csv"
            report = tmp_path / "report.md"
            env_file = tmp_path / ".env"
            env_file.write_text(
                "LAZYLIBRARIAN_URL=http://lazylibrarian.local:5299\n"
                "LAZYLIBRARIAN_API_KEY=test-key\n",
                encoding="utf-8",
            )
            write_csv(
                source,
                [{"Title": "Good Book", "Authors": "Ada Writer", "Read Status": "to-read"}],
            )

            self.assertEqual(
                module.main(
                    [
                        "--source",
                        str(source),
                        "--output",
                        str(output),
                        "--report",
                        str(report),
                        "--env-file",
                        str(env_file),
                        "--import-lazylibrarian",
                        "--lazylibrarian-import-mode",
                        "csv",
                        "--search",
                    ]
                ),
                0,
            )

            self.assertEqual(
                calls,
                [
                    ("http://lazylibrarian.local:5299", "test-key", "importCSVwishlist", output.parent, True, 600, None),
                    ("http://lazylibrarian.local:5299", "test-key", "forceBookSearch", None, False, 600, {"type": "eBook"}),
                ],
            )

    def test_import_lazylibrarian_defaults_to_title_search_and_queue(self):
        module = load_module()
        calls = []

        def fake_call(api_url, api_key, command, directory=None, wait=False, timeout=30, extra_params=None):
            calls.append((command, directory, wait, timeout, extra_params))
            if command == "findBook":
                return json.dumps(
                    [
                        {
                            "bookid": "OL123W",
                            "bookname": "Good Book",
                            "authorname": "Ada Writer",
                            "author_fuzz": 100,
                            "book_fuzz": 98,
                            "highest_fuzz": 99,
                        }
                    ]
                )
            return "OK"

        module.call_lazylibrarian = fake_call
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "storygraph.csv"
            output = tmp_path / "wishlist.csv"
            report = tmp_path / "report.md"
            write_csv(
                source,
                [{"Title": "Good Book", "Authors": "Ada Writer", "Read Status": "to-read"}],
            )

            self.assertEqual(
                module.main(
                    [
                        "--source",
                        str(source),
                        "--output",
                        str(output),
                        "--report",
                        str(report),
                        "--lazylibrarian-api-key",
                        "test-key",
                        "--import-lazylibrarian",
                    ]
                ),
                0,
            )

            self.assertEqual(
                calls,
                [
                    ("findBook", None, False, 600, {"name": "Good Book Ada Writer"}),
                    ("addBook", None, True, 600, {"id": "OL123W"}),
                    ("queueBook", None, False, 600, {"id": "OL123W"}),
                ],
            )

    def test_import_lazylibrarian_can_use_container_visible_import_dir(self):
        module = load_module()
        calls = []
        module.call_lazylibrarian = lambda api_url, api_key, command, directory=None, wait=False, timeout=30, extra_params=None: calls.append(
            (api_url, api_key, command, directory, wait, timeout, extra_params)
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "storygraph.csv"
            output = tmp_path / "wishlist.csv"
            report = tmp_path / "report.md"
            write_csv(
                source,
                [{"Title": "Good Book", "Authors": "Ada Writer", "Read Status": "to-read"}],
            )

            self.assertEqual(
                module.main(
                    [
                        "--source",
                        str(source),
                        "--output",
                        str(output),
                        "--report",
                        str(report),
                        "--lazylibrarian-api-key",
                        "test-key",
                        "--import-lazylibrarian",
                        "--lazylibrarian-import-mode",
                        "csv",
                        "--lazylibrarian-import-dir",
                        "/storygraph-imports",
                    ]
                ),
                0,
            )

            self.assertEqual(
                calls,
                [("http://127.0.0.1:5299", "test-key", "importCSVwishlist", Path("/storygraph-imports"), True, 600, None)],
            )


if __name__ == "__main__":
    unittest.main()
