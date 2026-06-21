#!/usr/bin/env python3
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

INLINE_PATTERNS = [
    re.compile(r"(?i)(PASSWORD|PASS|TOKEN|SECRET|PRIVATE_KEY|GSP_GTN_API_KEY)=([^$][^\s]*)"),
    re.compile(r"tunnel\s+--no-autoupdate\s+run\s+--token\s+([^\s$][^\s]*)"),
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

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("PASS: secret hygiene")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
