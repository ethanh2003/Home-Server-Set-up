from __future__ import annotations

from pathlib import Path

from .policy import PolicyEngine


def title_from_markdown(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def search_notes(vault_root: Path, query: str, limit: int = 25) -> list[dict[str, str]]:
    policy = PolicyEngine.default(vault_root=vault_root)
    needle = query.casefold()
    results: list[dict[str, str]] = []
    for path in sorted(vault_root.rglob("*.md")):
        rel = policy.normalize_path(path)
        if policy.is_hidden_or_protected(rel) or policy.is_therapy_history(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if needle not in text.casefold() and needle not in rel.casefold():
            continue
        preview = " ".join(text.split())[:240]
        results.append(
            {
                "path": rel,
                "title": title_from_markdown(text, Path(rel).stem),
                "preview": preview,
            }
        )
        if len(results) >= limit:
            break
    return results
