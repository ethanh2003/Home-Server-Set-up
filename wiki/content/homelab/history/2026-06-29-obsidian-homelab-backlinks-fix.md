# 2026-06-29T21-43-48-mRhR-obsidian_homelab_backlinks_fix

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f1556-a735-7c40-bab1-77dce8d6f1f7
updated_at: 2026-07-04T21:13:25+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/29/rollout-2026-06-29T21-43-48-019f1556-a735-7c40-bab1-77dce8d6f1f7.jsonl
cwd: /home/ethan

# Fixed Obsidian project links so the Homelab index and per-project notes resolve correctly inside the vault.

Rollout context: The user first asked to update Obsidian's homelab folder with project info, status, and remaining tasks. That work extended the Git-backed Wiki.js generator under `/home/ethan/docker` and also created a vault-native inventory under `/data/Obsidian/Main/Homelab`. After the initial implementation and publish, the user reported that the backlinks in Obsidian were wrong, so this follow-up focused on fixing the vault wikilinks rather than the wiki content itself.

## Task 1: Fix Obsidian backlink targets in Homelab project notes
Outcome: success

Preference signals:
- When the user said "the backlinks in obsidian aren't right" after the first pass, they were specifically asking for vault-link correctness, not a broader content rewrite -> future updates should verify Obsidian wikilinks as a first-class acceptance criterion.

Key steps:
- Inspected the current vault notes and found the generated links were relative-looking forms like `[[Projects/foo]]` from `Homelab/Projects.md` and `[[../Projects]]` in the child notes.
- Rewrote the vault-root links to explicit `Homelab/Projects/...` paths, e.g. `[[Homelab/Projects/foo]]` and `[[Homelab/Projects|Homelab Projects]]`.
- Regenerated all 29 vault notes under `/data/Obsidian/Main/Homelab/Projects/` so the status content and backlinks stayed in sync.
- Verified that no `[[Projects/...]]` or `[[../Projects...]]` links remained and that every `Homelab/Projects` wikilink resolved to an existing file.

Failures and how to do differently:
- The first Obsidian pass used links that looked reasonable in Markdown but did not resolve as intended in the vault. Future similar work should validate Obsidian wikilinks against the actual vault root path instead of assuming relative-style wiki links will behave correctly.
- The generated project notes also exposed a consistency issue where index and child notes could drift if only one surface was regenerated. Future updates should regenerate the index and per-project notes together.

Reusable knowledge:
- Obsidian notes in this vault should link with vault-root wikilinks such as `[[Homelab/Projects/foo]]`, not relative-looking `[[Projects/foo]]` or `[[../Projects]]` forms.
- The Homelab project inventory lives under `/data/Obsidian/Main/Homelab/Projects.md` plus per-project notes in `/data/Obsidian/Main/Homelab/Projects/`.
- A simple resolution check is to grep for `[[Projects/` and `[[../Projects` in the Homelab project notes, then confirm each wikilink points to an actual file.

References:
- `/data/Obsidian/Main/Homelab/Projects.md`
- `/data/Obsidian/Main/Homelab/Projects/spotify-stats.md`
- `/data/Obsidian/Main/Homelab/Projects/arr-multi-user.md`
- Verified final link forms: `[[Homelab/Projects/foo]]` in the index and `[[Homelab/Projects|Homelab Projects]]` in child notes
