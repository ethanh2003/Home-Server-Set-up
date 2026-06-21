#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/iac-common.sh
source "$script_dir/lib/iac-common.sh"

root="$(iac_repo_root)"
status=0

if ! command -v docker >/dev/null 2>&1; then
  printf 'docker is required for Compose validation.\n' >&2
  exit 1
fi

while IFS= read -r stack_dir; do
  stack_name="$(iac_stack_name "$root" "$stack_dir")"
  printf 'Validating %s\n' "$stack_name"

  mapfile -t env_args < <(iac_compose_env_args "$stack_dir")
  if ! (cd "$stack_dir" && docker compose "${env_args[@]}" config >/dev/null); then
    printf 'Compose validation failed for %s\n' "$stack_name" >&2
    status=1
  fi
done < <(iac_stack_dirs "$root")

exit "$status"
