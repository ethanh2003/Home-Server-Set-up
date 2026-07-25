#!/usr/bin/env python3
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "ebooks" / "scripts" / "storygraph_watch.py"


def load_module():
    spec = importlib.util.spec_from_file_location("storygraph_watch", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["storygraph_watch"] = module
    spec.loader.exec_module(module)
    return module


class StoryGraphWatchTests(unittest.TestCase):
    def test_process_once_runs_importer_for_newest_csv_and_records_state(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            import_dir = tmp_path / "imports"
            import_dir.mkdir()
            source = import_dir / "storygraph.csv"
            source.write_text("Title,Authors,Read Status\nDune,Frank Herbert,to-read\n", encoding="utf-8")
            state = tmp_path / "state.txt"
            calls = []

            def fake_run(cmd, check):
                calls.append(cmd)
                return subprocess.CompletedProcess(cmd, 0)

            module.subprocess.run = fake_run

            processed = module.process_once(
                importer=Path("/scripts/storygraph_wishlist_import.py"),
                import_dir=import_dir,
                state_file=state,
                calibre_db=Path("/calibre-library/metadata.db"),
                output=Path("/imports/lazylibrarian-wishlist.csv"),
                report=Path("/reports/storygraph-wishlist-report.md"),
                lazylibrarian_import_dir=Path("/storygraph-imports"),
                import_lazylibrarian=False,
                search=False,
            )

            self.assertTrue(processed)
            self.assertEqual(len(calls), 1)
            self.assertIn("--source", calls[0])
            self.assertIn(str(source), calls[0])
            self.assertEqual(state.read_text(encoding="utf-8").strip(), module.file_fingerprint(source))

    def test_process_once_skips_when_newest_csv_is_unchanged(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            import_dir = tmp_path / "imports"
            import_dir.mkdir()
            source = import_dir / "storygraph.csv"
            source.write_text("Title,Authors,Read Status\nDune,Frank Herbert,to-read\n", encoding="utf-8")
            state = tmp_path / "state.txt"
            state.write_text(module.file_fingerprint(source), encoding="utf-8")
            calls = []
            module.subprocess.run = lambda cmd, check: calls.append(cmd)

            processed = module.process_once(
                importer=Path("/scripts/storygraph_wishlist_import.py"),
                import_dir=import_dir,
                state_file=state,
                calibre_db=Path("/calibre-library/metadata.db"),
                output=Path("/imports/lazylibrarian-wishlist.csv"),
                report=Path("/reports/storygraph-wishlist-report.md"),
                lazylibrarian_import_dir=Path("/storygraph-imports"),
                import_lazylibrarian=True,
                search=True,
            )

            self.assertFalse(processed)
            self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
