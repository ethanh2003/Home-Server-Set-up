#!/usr/bin/env python3
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

INLINE_PATTERNS = [
    re.compile(r"(?i)(PASSWORD|PASS|TOKEN|SECRET|PRIVATE_KEY|GSP_GTN_API_KEY)=([^$][^\s]*)"),
    re.compile(r"tunnel\s+--no-autoupdate\s+run\s+--token\s+([^\s$][^\s]*)"),
]
WIKI_CONTENT_PATTERNS = [
    re.compile(r"(?i)\b[A-Z0-9_-]*(?:PASSWORD|PASS|TOKEN|SECRET|API[_-]?KEY|PRIVATE[_-]?KEY)[A-Z0-9_-]*\b\s*[:=]\s*(?!\[REDACTED\]|\.\.\.|<Wiki\.js|SET_AFTER_FIRST_LOGIN)[^\s`]+"),
    re.compile(r"-----BEGIN .*PRIVATE KEY-----"),
]

ALLOWLIST = {
    "github-runner/docker-compose.yml": {
        "GITHUB_RUNNER_TOKEN: ${GITHUB_RUNNER_TOKEN}",
    },
}


def main() -> int:
    failures: list[str] = []
    for compose in sorted(REPO_ROOT.glob("*/docker-compose.yml")):
        rel = compose.relative_to(REPO_ROOT).as_posix()
        allowed = ALLOWLIST.get(rel, set())
        for lineno, line in enumerate(compose.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip() in allowed:
                continue
            for pattern in INLINE_PATTERNS:
                if pattern.search(line):
                    failures.append(f"{rel}:{lineno}: inline secret-like value")

    wiki_content = REPO_ROOT / "wiki" / "content"
    if wiki_content.exists():
        for page in sorted(wiki_content.rglob("*.md")):
            text = page.read_text(encoding="utf-8", errors="replace")
            for pattern in WIKI_CONTENT_PATTERNS:
                if pattern.search(text):
                    failures.append(f"{page.relative_to(REPO_ROOT).as_posix()}: unredacted secret-like wiki content")
                    break

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("PASS: secret hygiene")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
