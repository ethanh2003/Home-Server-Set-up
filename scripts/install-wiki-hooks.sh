#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
hook_dir="$repo_root/.git/hooks"
hook="$hook_dir/pre-push"

mkdir -p "$hook_dir"
cat >"$hook" <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
"$repo_root/scripts/wiki-sync.sh" --check
HOOK
chmod +x "$hook"
printf 'Installed wiki pre-push hook at %s\n' "$hook"
