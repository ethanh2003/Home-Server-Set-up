#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/iac-common.sh
source "$script_dir/lib/iac-common.sh"

base="${1:-}"
head="${2:-HEAD}"
root="$(iac_repo_root)"

iac_require_clean_ref "$base"
iac_require_clean_ref "$head"

git -C "$root" diff --name-only "$base" "$head" | while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  stack="${path%%/*}"
  [[ "$stack" != "$path" ]] || continue
  [[ -f "$root/$stack/docker-compose.yml" ]] || continue
  printf '%s\n' "$stack"
done | sort -u
