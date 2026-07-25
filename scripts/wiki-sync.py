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
STATUS_VERIFIED_DATE = os.environ.get("HOMELAB_STATUS_VERIFIED_DATE", "2026-07-04")
INCLUDE_LIVE_STATUS = os.environ.get("WIKI_SYNC_INCLUDE_LIVE_STATUS") == "1"
ADJACENT_PROJECT_NAMES = [
    name.strip()
    for name in os.environ.get("WIKI_SYNC_ADJACENT_PROJECTS", "").split(",")
    if name.strip()
]
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


@dataclasses.dataclass(frozen=True)
class ProjectStatus:
    name: str
    kind: str
    path: str
    runtime: str
    project_status: str
    remaining_tasks: list[str]
    evidence: list[str]


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


def status_label(text: str) -> str:
    return text.replace("|", "\\|")


def compose_ps(root: Path, compose: Path | None) -> tuple[str, list[str]]:
    if compose is None:
        return "unknown", ["No Compose file found."]
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose), "ps", "--format", "{{.Service}}\t{{.State}}\t{{.Health}}"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
        result.check_returncode()
    except subprocess.CalledProcessError:
        return "unknown", ["`docker compose ps` could not read this stack."]
    except subprocess.TimeoutExpired:
        return "unknown", ["`docker compose ps` timed out while reading this stack."]
    rows = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not rows:
        return "stopped", ["No services are currently listed by `docker compose ps`."]

    service_states: list[tuple[str, str, str]] = []
    for row in rows:
        parts = row.split("\t")
        service = parts[0] if len(parts) > 0 else "unknown"
        state = parts[1] if len(parts) > 1 else "unknown"
        health = parts[2] if len(parts) > 2 else ""
        service_states.append((service, state, health))

    non_running = [state for _, state, _ in service_states if state != "running"]
    unhealthy = [health for _, _, health in service_states if health == "unhealthy"]
    stopped_states = {"created", "dead", "exited", "removing"}
    observed_states = {state for _, state, _ in service_states}
    if not non_running and not unhealthy:
        runtime = "running"
    elif observed_states and observed_states <= stopped_states:
        runtime = "stopped"
    else:
        runtime = "partial"
    evidence = [f"`{service}`: {state}{f' ({health})' if health else ''}" for service, state, health in service_states]
    return runtime, evidence


def stack_git_status(root: Path, stack: Path) -> str:
    status = run_git(root, ["status", "--short", "--", stack.name]).rstrip()
    if not status:
        return "clean"
    states: set[str] = set()
    worktree_states = {"M": "modified", "D": "deleted", "A": "added", "R": "renamed", "C": "copied", "U": "unmerged"}
    for line in status.splitlines():
        code = line[:2]
        if code == "??":
            states.add("untracked")
            continue
        if len(code) == 2 and code[1] in worktree_states:
            states.add(worktree_states[code[1]])
    return ", ".join(sorted(states)) if states else "clean"


def known_stack_tasks(stack: str) -> list[str]:
    tasks: dict[str, list[str]] = {
        "traefik": [
            "Complete Cloudflare cutover from NPM to Traefik after route parity is verified.",
            "Keep NPM available as rollback until public ingress has been proven off-LAN.",
        ],
        "nginx-proxy-manager": [
            "Keep as rollback during Traefik migration.",
            "Reconcile generated proxy configs with the live SQLite database before disabling stale rows.",
        ],
        "spotify-stats": [
            "Finish hardening large Your Spotify imports beyond the current cache and `/tmp/imports` fixes.",
            "Decide whether the upstream checkout changes should become a local patch, fork, or discardable hotfix.",
        ],
        "obsidian-livesync": [
            "Resolve the stale duplicate NPM row for `obsidian.ethan-herring.com` if it still exists.",
            "Keep LiveSync replication separate from the always-on Obsidian API/MCP service.",
        ],
        "timemachine": [
            "If remote Macs cannot route to `192.168.1.230`, advertise and approve a Tailscale route for `192.168.1.230/32`.",
        ],
        "home-assistant": [
            "Keep backup, validation, deploy, restart, logs, and rollback helper docs aligned with the live scripts.",
            "Maintain separate handling for the primary Home Assistant instance and `HomeAssistant2`.",
        ],
        "ebooks": [
            "Finish first-run application configuration in Calibre-Web Automated and LazyLibrarian.",
            "Verify StoryGraph watcher behavior after adding a real export CSV.",
        ],
        "arr-suite": [
            "Keep dry-run-first acquisition workflows and approval artifacts for bulk Radarr changes.",
            "Continue live queue verification before any Jellyfin collection or cleanup work.",
        ],
        "pingvin-share": [
            "Review whether Pingvin settings should stay UI-managed or gain tracked documentation for each production setting.",
        ],
        "stash": [
            "Add a stack README covering media roots, backups, scan behavior, and qBittorrent seeding constraints.",
        ],
        "linkstack": [
            "Normalize the stack into the broader IaC model and document public hardening settings.",
        ],
    }
    return tasks.get(stack, [])


def stack_project_status(root: Path, stack_dir: Path) -> ProjectStatus:
    stack = stack_dir.name
    compose = compose_file(stack_dir)
    compose_rel = compose.relative_to(root).as_posix() if compose else "missing"
    compose_text = compose.read_text(encoding="utf-8", errors="replace") if compose else ""
    readme = stack_dir / "README.md"
    sops = (stack_dir / ".env.sops").exists() or any(stack_dir.glob("*.sops.env"))
    tracked = is_tracked(root, compose.relative_to(root)) if compose else False
    if INCLUDE_LIVE_STATUS:
        runtime, runtime_evidence = compose_ps(root, compose)
        git_state = stack_git_status(root, stack_dir)
    else:
        runtime = "not checked"
        runtime_evidence = ["Live runtime state is monitored in Prometheus and omitted from deterministic wiki output."]
        git_state = "omitted"

    remaining = known_stack_tasks(stack)
    if not tracked:
        remaining.append("Review and either commit the stack into IaC or intentionally ignore it.")
    if not readme.exists():
        remaining.append("Add a stack README/runbook with purpose, endpoints, backup/restore notes, and common commands.")
    has_env_shape = (stack_dir / ".env").exists() or (stack_dir / ".env.example").exists() or "${" in compose_text
    if has_env_shape and not sops:
        remaining.append("Review whether runtime secrets need SOPS; if not, document why SOPS is unnecessary.")
    if runtime in {"partial", "stopped"}:
        remaining.append("Inspect `docker compose ps` and service logs before marking the runtime operational.")
    if not remaining:
        remaining.append("Keep routine image updates, backups, and documentation current.")

    if runtime in {"partial", "stopped"}:
        project_status = "in progress"
    elif not tracked:
        project_status = "needs IaC cleanup"
    elif not readme.exists():
        project_status = "needs docs"
    else:
        project_status = "operational"
    if stack in {"traefik", "spotify-stats", "ebooks"}:
        project_status = "in progress"
    if stack in {"nginx-proxy-manager", "linkstack", "stash", "obsidian-livesync"} and project_status == "operational":
        project_status = "needs IaC cleanup"

    evidence = [
        f"Compose file: `{compose_rel}`",
        f"Compose tracked in Git: {'yes' if tracked else 'no'}",
        f"README: {'yes' if readme.exists() else 'no'}",
        f"SOPS env: {'yes' if sops else 'no'}",
        f"Git status for stack path: {git_state}",
        *runtime_evidence,
    ]
    return ProjectStatus(
        name=stack,
        kind="stack",
        path=f"/home/ethan/docker/{stack}",
        runtime=runtime,
        project_status=project_status,
        remaining_tasks=remaining,
        evidence=evidence,
    )


def adjacent_project_status(root: Path, name: str) -> ProjectStatus | None:
    path = root.parent / name
    if not path.exists():
        return None
    git_status = subprocess.run(
        ["git", "-C", str(path), "status", "--short", "--branch"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if git_status.returncode == 0:
        git_summary = " ".join(line.strip() for line in git_status.stdout.splitlines()[:3]) or "clean"
    else:
        git_summary = "not a git repository"

    config_files = [
        rel
        for rel in ("docker-compose.yml", "compose.yml", "package.json", "pyproject.toml", "AGENTS.md")
        if (path / rel).exists()
    ]
    evidence = [f"Path: `{path}`", f"Git status: {git_summary}"]
    if config_files:
        evidence.append("Project files: " + ", ".join(f"`{rel}`" for rel in config_files))

    if name == "obsidian-api-mcp":
        return ProjectStatus(
            name=name,
            kind="adjacent repo",
            path=str(path),
            runtime="non-runtime",
            project_status="operational",
            remaining_tasks=[
                "Keep the user systemd service and bearer-token setup documented with the Obsidian vault notes.",
                "Do not treat this service as the LiveSync replication engine.",
            ],
            evidence=evidence,
        )
    if name == "arr-multi-user":
        return ProjectStatus(
            name=name,
            kind="adjacent repo",
            path=str(path),
            runtime="non-runtime",
            project_status="in progress",
            remaining_tasks=[
                "Create the initial repository commit once the current scaffold and submodule state are reviewed.",
                "Finish the companion-app plan set and re-run the repository contract tests.",
            ],
            evidence=evidence,
        )
    if name == "chicago-dashboard":
        return ProjectStatus(
            name=name,
            kind="adjacent repo",
            path=str(path),
            runtime="non-runtime",
            project_status="in progress",
            remaining_tasks=[
                "Implement the remaining CTA, weather, calendar, ETA, preferences, and cross-plan consistency plans.",
                "Review the local server/package changes and decide what belongs in Git.",
            ],
            evidence=evidence,
        )
    if name == "dymo-label":
        return ProjectStatus(
            name=name,
            kind="adjacent app",
            path=str(path),
            runtime="unknown",
            project_status="blocked",
            remaining_tasks=[
                "Initialize source control or explicitly document why the app remains outside Git.",
                "Restore or recreate `frontend/src/stores/appStore`, `frontend/src/components/Login`, and `frontend/src/components/Editor` so the frontend build can compile.",
            ],
            evidence=evidence,
        )
    return None


def collect_project_statuses(root: Path, stacks: list[Path]) -> list[ProjectStatus]:
    statuses = [stack_project_status(root, stack) for stack in stacks]
    statuses.extend(
        status
        for name in ADJACENT_PROJECT_NAMES
        if (status := adjacent_project_status(root, name)) is not None
    )
    return sorted(statuses, key=lambda status: (status.kind != "stack", status.name.lower()))


def page_header(title: str) -> str:
    return f"# {title}\n\n> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.\n\n"


def generate_homepage(stacks: list[Path]) -> Page:
    lines = [
        page_header("Homelab Documentation"),
        f"Last verified: {STATUS_VERIFIED_DATE}",
        "",
        "This Wiki.js site is the operational documentation entrypoint for the homelab.",
        "",
        "## Start Here",
        "",
        "- [Homelab Wiki](/homelab/index)",
        "- [Project Status](/homelab/projects)",
        "- [Migration Gaps](/homelab/migration-gaps)",
        "- [Traefik Migration](/homelab/runbooks/traefik-migration)",
        "- [IaC Runbook](/homelab/runbooks/iac-runbook)",
        "",
        "## Active Stacks",
        "",
    ]
    lines.extend(f"- [{stack.name}](/homelab/stacks/{stack.name})" for stack in stacks)
    lines.extend(
        [
            "",
            "## Source Of Truth",
            "",
            "- Git repo: `/home/ethan/docker`",
            "- Generated wiki source: `/home/ethan/docker/wiki/content`",
            "- Publish command: `./scripts/wiki-sync.sh --backfill --publish`",
            "",
        ]
    )
    return Page(Path("home.md"), "Homelab Documentation", redact("\n".join(lines)))


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
        "## Project Status",
        "",
        "- [Project Status](/homelab/projects)",
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


def project_status_markdown(status: ProjectStatus) -> list[str]:
    lines = [
        "## Project Status",
        "",
        f"- Runtime: {status.runtime}",
        f"- Project status: {status.project_status}",
        f"- Last verified: {STATUS_VERIFIED_DATE}",
        "",
        "## Remaining Tasks",
        "",
    ]
    lines.extend(f"- {task}" for task in status.remaining_tasks)
    lines.extend(["", "## Evidence", ""])
    lines.extend(f"- {item}" for item in status.evidence)
    return lines


def generate_projects_page(root: Path, statuses: list[ProjectStatus]) -> Page:
    lines = [
        page_header("Homelab Project Status"),
        f"Last verified: {STATUS_VERIFIED_DATE}",
        "",
        "## Status Model",
        "",
        "- Runtime: `not checked` in deterministic output; opt-in snapshots may report `running`, `partial`, `stopped`, `unknown`, or `non-runtime`.",
        "- Project status: `operational`, `in progress`, `needs IaC cleanup`, `needs docs`, `blocked`, or `archived`.",
        "- Remaining tasks are concrete next actions, not placeholders.",
        "",
        "## Projects",
        "",
        "| Project | Kind | Runtime | Project status | Path |",
        "| --- | --- | --- | --- | --- |",
    ]
    for status in statuses:
        wiki_path = f"/homelab/stacks/{status.name}" if status.kind == "stack" else ""
        label = f"[{status.name}]({wiki_path})" if wiki_path else status.name
        lines.append(
            "| "
            + " | ".join(
                [
                    label,
                    status_label(status.kind),
                    status_label(status.runtime),
                    status_label(status.project_status),
                    f"`{status_label(status.path)}`",
                ]
            )
            + " |"
        )

    lines.extend(["", "## Remaining Task Index", ""])
    for status in statuses:
        lines.append(f"### {status.name}")
        lines.append("")
        lines.append(f"- Runtime: {status.runtime}")
        lines.append(f"- Project status: {status.project_status}")
        lines.extend(f"- {task}" for task in status.remaining_tasks)
        lines.append("")
    return Page(Path("homelab/projects.md"), "Homelab Project Status", redact("\n".join(lines)))


def generate_stack_page(root: Path, stack_dir: Path) -> Page:
    stack = stack_dir.name
    status = stack_project_status(root, stack_dir)
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
        *project_status_markdown(status),
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
    log_ref = "HEAD"
    content_commit = run_git(root, ["log", "--pretty=format:%H", "-1", "--", "wiki/content"]).strip()
    if content_commit:
        cutoff = content_commit
        while True:
            parent = run_git(root, ["rev-parse", "--verify", f"{cutoff}^"]).strip()
            if not parent:
                break
            parent_changed = run_git(root, ["diff-tree", "--no-commit-id", "--name-only", "-r", parent]).splitlines()
            if not any(path.startswith("wiki/content/") for path in parent_changed):
                break
            cutoff = parent
        parent = run_git(root, ["rev-parse", "--verify", f"{cutoff}^"]).strip()
        if parent:
            log_ref = parent

    log_lines: list[str] = []
    for commit in run_git(root, ["log", log_ref, "--pretty=format:%H", "--max-count=160"]).splitlines():
        changed = run_git(root, ["diff-tree", "--no-commit-id", "--name-only", "-r", commit]).splitlines()
        if any(path.startswith("wiki/content/") for path in changed):
            continue
        line = run_git(root, ["show", "-s", "--date=short", "--pretty=format:%ad %h %s", commit]).strip()
        if line:
            log_lines.append(line)
        if len(log_lines) >= 80:
            break
    log = "\n".join(log_lines)
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
            "Committed wiki content omits raw dirty-status output so `wiki-sync --check` is reproducible.",
            "Check live drift from the IaC root with:",
            "",
            "```bash",
            "git status --short -- . ':(exclude)wiki/content'",
            "```",
            "",
            "Current generated-live status:",
            "",
            "```text",
            redact(run_git(root, ["status", "--short", "--", ".", ":(exclude)wiki/content"]).strip() or "clean")
            if os.environ.get("WIKI_SYNC_INCLUDE_DIRTY") == "1"
            else "omitted; set WIKI_SYNC_INCLUDE_DIRTY=1 for an ad hoc live snapshot",
            "```",
            "",
        ]
    )
    return Page(Path("homelab/migration-gaps.md"), "Migration Gaps", redact("\n".join(lines)))


def generate(root: Path, stack: str | None, include_backfill: bool) -> GenerateResult:
    stacks = discover_stacks(root)
    statuses = collect_project_statuses(root, stacks)
    pages = [generate_homepage(stacks), generate_index(root, stacks), generate_projects_page(root, statuses), generate_migration_gaps(root, stacks)]
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


PAGE_LOOKUP_QUERY = """
query($path: String!, $locale: String!) {
  pages {
    singleByPath(path: $path, locale: $locale) {
      id
    }
  }
}
"""

PAGE_CREATE_MUTATION = """
mutation($content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
  pages {
    create(content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
      responseResult { succeeded message }
      page { id }
    }
  }
}
"""

PAGE_UPDATE_MUTATION = """
mutation($id: Int!, $content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
  pages {
    update(id: $id, content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
      responseResult { succeeded message }
      page { id }
    }
  }
}
"""


def publish_page(base_url: str, token: str, page: Page) -> None:
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
    lookup = graphql_request(base_url, token, PAGE_LOOKUP_QUERY, {"path": path, "locale": "en"})
    page_id = (((lookup.get("data") or {}).get("pages") or {}).get("singleByPath") or {}).get("id")
    if page_id:
        response = graphql_request(base_url, token, PAGE_UPDATE_MUTATION, common | {"id": int(page_id)})
        result = ((response.get("data") or {}).get("pages") or {}).get("update", {}).get("responseResult", {})
    else:
        response = graphql_request(base_url, token, PAGE_CREATE_MUTATION, common)
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
