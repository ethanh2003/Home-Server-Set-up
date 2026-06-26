#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import difflib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


CONTENT_ROOT = Path("wiki/content")
WIKI_HOSTS = ["wiki.ethan-herring.com", "wiki.pup-percy.com", "wiki.ethanh.online"]
SECRET_PATTERNS = [
    re.compile(r"(?i)\b[A-Z0-9_-]*(?:PASSWORD|PASS|TOKEN|SECRET|API[_-]?KEY|PRIVATE[_-]?KEY)[A-Z0-9_-]*\b\s*[:=]\s*[^\s`'\"]+"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
]


@dataclasses.dataclass(frozen=True)
class Page:
    relative_path: Path
    title: str
    content: str

    @property
    def wiki_path(self) -> str:
        return self.relative_path.with_suffix("").as_posix()


@dataclasses.dataclass(frozen=True)
class GenerateResult:
    root: Path
    pages: list[Page]


def repo_root() -> Path:
    if os.environ.get("IAC_REPO_ROOT"):
        return Path(os.environ["IAC_REPO_ROOT"]).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0:
        return Path(result.stdout.strip()).resolve()
    return Path.cwd().resolve()


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        def replacement(match: re.Match[str]) -> str:
            original = match.group(0)
            if ":" in original:
                return original.split(":", 1)[0] + ": [REDACTED]"
            if "=" in original:
                return original.split("=", 1)[0] + "=[REDACTED]"
            return match.group(1) + "[REDACTED]" if match.groups() else "[REDACTED]"

        redacted = pattern.sub(replacement, redacted)
    redacted = "\n".join(line.rstrip() for line in redacted.splitlines())
    return redacted


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "page"


def run_git(root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def is_tracked(root: Path, path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", path.as_posix()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def discover_stacks(root: Path) -> list[Path]:
    stacks: set[Path] = set()
    for pattern in ("*/docker-compose.yml", "*/compose.yml"):
        for compose in root.glob(pattern):
            if ".git" not in compose.parts:
                stacks.add(compose.parent)
    return sorted(stacks, key=lambda path: path.name.lower())


def compose_file(stack_dir: Path) -> Path | None:
    for name in ("docker-compose.yml", "compose.yml"):
        candidate = stack_dir / name
        if candidate.exists():
            return candidate
    return None


def service_names(compose_text: str) -> list[str]:
    names: list[str] = []
    in_services = False
    for line in compose_text.splitlines():
        if line.startswith("services:"):
            in_services = True
            continue
        if in_services and line and not line.startswith((" ", "\t")):
            break
        match = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", line)
        if in_services and match:
            names.append(match.group(1))
    return names


def image_names(compose_text: str) -> list[str]:
    return sorted(set(re.findall(r"^\s*image:\s*([^\s#]+)", compose_text, flags=re.M)))


def page_header(title: str) -> str:
    return f"# {title}\n\n> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.\n\n"


def generate_index(root: Path, stacks: list[Path]) -> Page:
    lines = [
        page_header("Homelab Wiki"),
        "## URLs",
        "",
        *[f"- https://{host}" for host in WIKI_HOSTS],
        "",
        "## Source of Truth",
        "",
        "- Git repo: `/home/ethan/docker`",
        "- Wiki content source: `wiki/content/`",
        "- Publish command: `./scripts/wiki-sync.sh --all --publish`",
        "- Focus stack command: `./scripts/wiki-sync.sh --stack <stack-name>`",
        "",
        "## Stacks",
        "",
    ]
    lines.extend(f"- [{stack.name}](/homelab/stacks/{stack.name})" for stack in stacks)
    lines.extend(
        [
            "",
            "## Core Runbooks",
            "",
            "- [IaC Runbook](/homelab/runbooks/iac-runbook)",
            "- [GitHub Runner](/homelab/runbooks/github-runner)",
            "- [Traefik Migration](/homelab/runbooks/traefik-migration)",
            "- [Migration Gaps](/homelab/migration-gaps)",
            "",
        ]
    )
    return Page(Path("homelab/index.md"), "Homelab Wiki", redact("\n".join(lines)))


def generate_stack_page(root: Path, stack_dir: Path) -> Page:
    stack = stack_dir.name
    compose = compose_file(stack_dir)
    compose_rel = compose.relative_to(root).as_posix() if compose else "missing"
    compose_text = compose.read_text(encoding="utf-8", errors="replace") if compose else ""
    readme = stack_dir / "README.md"
    sops_files = sorted(
        file.name
        for file in stack_dir.iterdir()
        if file.is_file() and (file.name == ".env.sops" or file.name.endswith(".sops.env"))
    )
    tracked = is_tracked(root, compose.relative_to(root)) if compose else False
    services = service_names(compose_text)
    images = image_names(compose_text)

    lines = [
        page_header(f"Stack: {stack}"),
        "## IaC Status",
        "",
        f"- Compose file: `{compose_rel}`",
        f"- Compose tracked in Git: {'yes' if tracked else 'no'}",
        f"- Has SOPS env: {'yes' if sops_files else 'no'}",
        f"- README: {'yes' if readme.exists() else 'no'}",
        "",
        "## Services",
        "",
    ]
    lines.extend(f"- `{name}`" for name in services) if services else lines.append("- No services parsed.")
    lines.extend(["", "## Images", ""])
    lines.extend(f"- `{image}`" for image in images) if images else lines.append("- No images parsed.")
    lines.extend(
        [
            "",
            "## Operations",
            "",
            f"```bash\ncd /home/ethan/docker/{stack}\ndocker compose config\ndocker compose ps\n```",
            "",
            "## Notes",
            "",
        ]
    )
    if readme.exists():
        lines.append(redact(readme.read_text(encoding="utf-8", errors="replace")))
    else:
        lines.append("No stack README exists yet.")
    return Page(Path(f"homelab/stacks/{stack}.md"), f"Stack: {stack}", redact("\n".join(lines)))


def runbook_sources(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for name in ("STACKS_README.md", "GEMINI.md", "STACKS_GEMINI.md"):
        path = root / name
        if path.exists():
            candidates.append(path)
    candidates.extend(sorted((root / "docs").glob("*.md")) if (root / "docs").exists() else [])
    for readme in sorted(root.glob("*/README.md")):
        if readme.parts[-3:] and "upstream-your_spotify" in readme.parts:
            continue
        candidates.append(readme)
    return candidates


def generate_runbook_pages(root: Path) -> list[Page]:
    pages: list[Page] = []
    seen: set[str] = set()
    for source in runbook_sources(root):
        rel = source.relative_to(root).as_posix()
        slug = slugify(rel.removesuffix(".md").replace("/", "-"))
        if source.name in {"iac-runbook.md", "github-runner.md", "traefik-migration.md"}:
            slug = source.stem
        if slug in seen:
            continue
        seen.add(slug)
        title = rel
        content = page_header(title) + redact(source.read_text(encoding="utf-8", errors="replace"))
        pages.append(Page(Path(f"homelab/runbooks/{slug}.md"), title, content))
    return pages


def history_slug(path: Path) -> str:
    name = path.stem
    match = re.match(r"(\d{4}-\d{2}-\d{2})T\d{2}-\d{2}-\d{2}-(?:[^-]+-)?(.+)", name)
    if match:
        return f"{match.group(1)}-{slugify(match.group(2))}"
    return slugify(name)


def generate_history_pages(root: Path) -> list[Page]:
    pages: list[Page] = []
    log = run_git(root, ["log", "--date=short", "--pretty=format:%ad %h %s", "--max-count=80"])
    if log:
        content = page_header("Git History") + "```text\n" + redact(log) + "\n```\n"
        pages.append(Page(Path("homelab/history/git-history.md"), "Git History", content))

    npm_inventory = root / "nginx-proxy-manager" / "npm-migration-inventory.yml"
    if npm_inventory.exists():
        content = page_header("NPM Migration Inventory") + "```yaml\n" + redact(npm_inventory.read_text(encoding="utf-8", errors="replace")) + "\n```\n"
        pages.append(Page(Path("homelab/history/npm-migration-inventory.md"), "NPM Migration Inventory", content))

    global_memory = Path("/home/ethan/.codex/memories/rollout_summaries")
    memory_dirs = [root / ".codex-memory" / "rollout_summaries", global_memory]
    for memory_dir in memory_dirs:
        if not memory_dir.exists():
            continue
        for summary in sorted(memory_dir.glob("*.md")):
            text = summary.read_text(encoding="utf-8", errors="replace")
            if memory_dir == global_memory and "/home/ethan/docker" not in text and "homelab" not in text.lower():
                continue
            snippet = "\n".join(text.splitlines()[:120])
            slug = history_slug(summary)
            title = summary.stem
            content = page_header(title) + redact(snippet) + "\n"
            pages.append(Page(Path(f"homelab/history/{slug}.md"), title, content))
    return pages


def generate_migration_gaps(root: Path, stacks: list[Path]) -> Page:
    status = run_git(root, ["status", "--short", "--", ".", ":(exclude)wiki/content"])
    lines = [
        page_header("Migration Gaps"),
        "## Stack IaC Coverage",
        "",
        "| Stack | Compose | Compose tracked | SOPS env | README |",
        "| --- | --- | --- | --- | --- |",
    ]
    for stack in stacks:
        compose = compose_file(stack)
        compose_rel = compose.relative_to(root) if compose else Path("missing")
        tracked = is_tracked(root, compose_rel) if compose else False
        sops = (stack / ".env.sops").exists() or any(stack.glob("*.sops.env"))
        readme = (stack / "README.md").exists()
        lines.append(f"| {stack.name} | `{compose_rel.as_posix()}` | {'yes' if tracked else 'no'} | {'yes' if sops else 'no'} | {'yes' if readme else 'no'} |")
    lines.extend(
        [
            "",
            "## Reverse Proxy State",
            "",
            "- Target state: Traefik owns IaC routing.",
            "- Transition state may still have NPM live on ports `80/443` until Cloudflared cutover is verified.",
            "- Wiki routes are defined for all three wiki hostnames.",
            "",
            "## Dirty Worktree Snapshot",
            "",
            "```text",
            redact(status.strip() or "clean"),
            "```",
            "",
        ]
    )
    return Page(Path("homelab/migration-gaps.md"), "Migration Gaps", redact("\n".join(lines)))


def generate(root: Path, stack: str | None, include_backfill: bool) -> GenerateResult:
    stacks = discover_stacks(root)
    pages = [generate_index(root, stacks), generate_migration_gaps(root, stacks)]
    selected = [path for path in stacks if stack is None or path.name == stack]
    if stack and not selected:
        raise SystemExit(f"Unknown stack: {stack}")
    pages.extend(generate_stack_page(root, stack_dir) for stack_dir in selected)
    if stack is None:
        pages.extend(generate_runbook_pages(root))
    if include_backfill:
        pages.extend(generate_history_pages(root))
    pages = sorted(pages, key=lambda page: page.relative_path.as_posix())
    return GenerateResult(root=root, pages=pages)


def expected_files(result: GenerateResult) -> dict[Path, str]:
    return {CONTENT_ROOT / page.relative_path: page.content.rstrip() + "\n" for page in result.pages}


def write_pages(result: GenerateResult) -> None:
    output_root = result.root / CONTENT_ROOT
    for rel, content in expected_files(result).items():
        path = result.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"Wrote {len(result.pages)} wiki content pages to {output_root}")


def check_pages(result: GenerateResult) -> int:
    failures: list[str] = []
    for rel, content in expected_files(result).items():
        path = result.root / rel
        if not path.exists():
            failures.append(f"missing {rel.as_posix()}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != content:
            diff = "\n".join(difflib.unified_diff(actual.splitlines(), content.splitlines(), fromfile=str(rel), tofile=f"expected/{rel}", lineterm=""))
            failures.append(diff)
    if failures:
        print("wiki content is stale; run ./scripts/wiki-sync.sh --backfill", file=sys.stderr)
        print("\n\n".join(failures), file=sys.stderr)
        return 1
    print("wiki content is current")
    return 0


def graphql_request(url: str, token: str, query: str, variables: dict[str, object]) -> dict[str, object]:
    endpoint = url.rstrip("/") + "/graphql"
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Wiki.js GraphQL HTTP {exc.code}: {body}") from exc


def publish_page(base_url: str, token: str, page: Page) -> None:
    lookup_query = """
query($path: String!, $locale: String!) {
  pages {
    single(path: $path, locale: $locale) {
      id
    }
  }
}
"""
    create_mutation = """
mutation($content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
  pages {
    create(content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
      responseResult { succeeded message }
      page { id }
    }
  }
}
"""
    update_mutation = """
mutation($id: Int!, $content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
  pages {
    update(id: $id, content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
      responseResult { succeeded message }
      page { id }
    }
  }
}
"""
    path = page.wiki_path
    common = {
        "content": page.content,
        "description": "Generated homelab IaC documentation",
        "editor": "markdown",
        "isPublished": True,
        "isPrivate": False,
        "locale": "en",
        "path": path,
        "tags": ["homelab", "iac", "generated"],
        "title": page.title,
    }
    lookup = graphql_request(base_url, token, lookup_query, {"path": path, "locale": "en"})
    page_id = (((lookup.get("data") or {}).get("pages") or {}).get("single") or {}).get("id")
    if page_id:
        response = graphql_request(base_url, token, update_mutation, common | {"id": int(page_id)})
        result = ((response.get("data") or {}).get("pages") or {}).get("update", {}).get("responseResult", {})
    else:
        response = graphql_request(base_url, token, create_mutation, common)
        result = ((response.get("data") or {}).get("pages") or {}).get("create", {}).get("responseResult", {})
    if result and not result.get("succeeded", False):
        raise RuntimeError(f"Wiki.js publish failed for {path}: {result.get('message')}")


def publish(result: GenerateResult) -> None:
    base_url = os.environ.get("WIKIJS_URL", "https://wiki.ethan-herring.com")
    token = os.environ.get("WIKIJS_API_TOKEN", "")
    if not token or token.startswith("SET_"):
        raise SystemExit("WIKIJS_API_TOKEN is required for --publish")
    for page in result.pages:
        publish_page(base_url, token, page)
    print(f"Published {len(result.pages)} pages to {base_url}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and publish homelab Wiki.js content.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="Generate all current wiki pages.")
    mode.add_argument("--stack", help="Generate the focus page for one stack.")
    mode.add_argument("--backfill", action="store_true", help="Generate all pages including historical backfill.")
    mode.add_argument("--check", action="store_true", help="Check generated content is current.")
    parser.add_argument("--publish", action="store_true", help="Publish generated pages to Wiki.js via GraphQL.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = repo_root()
    include_backfill = args.backfill or args.check
    result = generate(root, stack=args.stack, include_backfill=include_backfill)
    if args.check:
        return check_pages(result)
    write_pages(result)
    if args.publish:
        publish(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
