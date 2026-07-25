from pathlib import Path

from vault_inbox.policy import PolicyEngine, ValidationError


def test_policy_blocks_hidden_plugin_and_secret_paths(tmp_path: Path) -> None:
    policy = PolicyEngine.default(vault_root=tmp_path)

    errors = policy.validate_changed_paths(
        [
            ".obsidian/plugins/quickadd/data.json",
            "Personal/secret.key",
            "Therapy/Transcripts/Raw/2026-06-08.md",
        ],
        workflow="capture",
    )

    assert [error.code for error in errors] == [
        "protected_path",
        "secret_like_path",
        "protected_therapy_history",
    ]


def test_policy_allows_vault_admin_inbox_and_current_therapy_intake(tmp_path: Path) -> None:
    policy = PolicyEngine.default(vault_root=tmp_path)

    errors = policy.validate_changed_paths(
        [
            "Vault Admin/Inbox/2026-07-04.md",
            "Therapy/Intake/Current.md",
            "Personal/Resources/Topics/Second Brain.md",
        ],
        workflow="capture",
    )

    assert errors == []


def test_markdown_validation_requires_frontmatter_and_expected_heading(tmp_path: Path) -> None:
    note = tmp_path / "Personal" / "Resources" / "Topics" / "Second Brain.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Second Brain\n\nNo frontmatter.\n", encoding="utf-8")
    policy = PolicyEngine.default(vault_root=tmp_path)

    errors = policy.validate_markdown_file(note)

    assert ValidationError(
        code="missing_frontmatter",
        path="Personal/Resources/Topics/Second Brain.md",
        message="Markdown note must start with YAML frontmatter.",
    ) in errors
