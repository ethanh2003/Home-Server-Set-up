#!/usr/bin/env python3
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "wiki-sync.py"


def load_module():
    spec = importlib.util.spec_from_file_location("wiki_sync", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["wiki_sync"] = module
    spec.loader.exec_module(module)
    return module


def make_repo() -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="wiki-sync-test-"))
    repo = tmpdir / "repo"
    repo.mkdir()
    (repo / "docs").mkdir()
    (repo / "docs" / "iac-runbook.md").write_text("# IaC Runbook\n\nValidate with scripts.\n", encoding="utf-8")
    (repo / "STACKS_README.md").write_text("# Docker Stacks\n\nStack summary.\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".env\n*.env\n", encoding="utf-8")
    (repo / ".sops.yaml").write_text("creation_rules: []\n", encoding="utf-8")
    (repo / "renovate.json5").write_text('{"minimumReleaseAge":"7 days"}\n', encoding="utf-8")

    stack = repo / "alpha-stack"
    stack.mkdir()
    (stack / "docker-compose.yml").write_text(
        """services:
  alpha:
    image: example/alpha:1.0
    environment:
      API_TOKEN: ${API_TOKEN}
    networks:
      - proxy_net
networks:
  proxy_net:
    external: true
""",
        encoding="utf-8",
    )
    (stack / ".env.sops").write_text("API_TOKEN=ENC[AES256_GCM,data:redacted]\n", encoding="utf-8")
    (stack / "README.md").write_text("# Alpha Stack\n\nUses TOKEN=super-secret-value.\n", encoding="utf-8")

    history = repo / ".codex-memory" / "rollout_summaries"
    history.mkdir(parents=True)
    (history / "2026-06-01T00-00-00-alpha.md").write_text(
        "session_meta payload id 019example\n"
        "Fixed alpha stack with PASSWORD=bad-secret and verified HTTP 200.\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Wiki Sync Test"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial alpha stack"], cwd=repo, check=True)
    return repo


class WikiSyncTests(unittest.TestCase):
    def test_generate_all_creates_expected_pages_and_redacts_sensitive_values(self):
        module = load_module()
        repo = make_repo()
        try:
            result = module.generate(repo, stack=None, include_backfill=True)
            paths = {page.relative_path.as_posix() for page in result.pages}

            self.assertIn("homelab/index.md", paths)
            self.assertIn("homelab/stacks/alpha-stack.md", paths)
            self.assertIn("homelab/runbooks/iac-runbook.md", paths)
            self.assertIn("homelab/history/2026-06-01-alpha.md", paths)
            self.assertIn("homelab/migration-gaps.md", paths)

            combined = "\n".join(page.content for page in result.pages)
            self.assertNotIn("super-secret-value", combined)
            self.assertNotIn("bad-secret", combined)
            self.assertIn("[REDACTED]", combined)
            self.assertIn("alpha-stack", combined)
            self.assertIn("Has SOPS env: yes", combined)
        finally:
            shutil.rmtree(repo.parent)

    def test_stack_mode_limits_stack_focus_but_keeps_index_and_gaps(self):
        module = load_module()
        repo = make_repo()
        try:
            result = module.generate(repo, stack="alpha-stack", include_backfill=False)
            paths = {page.relative_path.as_posix() for page in result.pages}

            self.assertIn("homelab/index.md", paths)
            self.assertIn("homelab/stacks/alpha-stack.md", paths)
            self.assertIn("homelab/migration-gaps.md", paths)
            self.assertFalse(any(path.startswith("homelab/history/") for path in paths))
        finally:
            shutil.rmtree(repo.parent)

    def test_check_mode_fails_when_content_is_stale_and_passes_after_write(self):
        repo = make_repo()
        try:
            env = os.environ | {"IAC_REPO_ROOT": str(repo)}
            stale = subprocess.run(
                [sys.executable, str(SCRIPT), "--check"],
                cwd=repo,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(stale.returncode, 1)
            self.assertIn("wiki content is stale", stale.stderr)

            written = subprocess.run(
                [sys.executable, str(SCRIPT), "--backfill"],
                cwd=repo,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(written.returncode, 0, written.stderr)

            fresh = subprocess.run(
                [sys.executable, str(SCRIPT), "--check"],
                cwd=repo,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(fresh.returncode, 0, fresh.stderr)
            self.assertIn("wiki content is current", fresh.stdout)
        finally:
            shutil.rmtree(repo.parent)


if __name__ == "__main__":
    unittest.main()
