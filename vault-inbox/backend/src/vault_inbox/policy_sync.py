from __future__ import annotations

from pathlib import Path

import yaml


def sync_policies_to_vault(*, app_repo_root: Path, vault_root: Path) -> list[str]:
    policy_dir = app_repo_root / "policies"
    output_dir = vault_root / "Vault Admin" / "Policies"
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for policy_path in sorted(policy_dir.glob("*.yml")):
        data = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
        policy_id = str(data.get("id") or policy_path.stem)
        target = output_dir / f"{policy_path.stem}.md"
        body = (
            "---\n"
            "note_type: vault_inbox_policy\n"
            f"policy_id: {policy_id}\n"
            f"version: {data.get('version', 1)}\n"
            "tags:\n"
            "  - vault-admin\n"
            "  - vault-inbox/policy\n"
            "---\n"
            f"# Policy: {policy_id}\n\n"
            "```yaml\n"
            f"{policy_path.read_text(encoding='utf-8').strip()}\n"
            "```\n"
        )
        target.write_text(body, encoding="utf-8")
        written.append(target.relative_to(vault_root).as_posix())
    return written
