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

mapfile -t stacks < <("$script_dir/iac-changed-stacks.sh" "$base" "$head")

if [[ "${#stacks[@]}" -eq 0 ]]; then
  printf 'No changed Docker Compose stacks to deploy.\n'
  exit 0
fi

iac_ensure_proxy_net

for stack in "${stacks[@]}"; do
  stack_dir="$root/$stack"
  printf 'Deploying %s\n' "$stack"

  "$script_dir/secrets-decrypt.sh" --stack "$stack"

  mapfile -t env_args < <(iac_compose_env_args "$stack_dir")
  (
    cd "$stack_dir"
    docker compose "${env_args[@]}" config >/dev/null
    docker compose "${env_args[@]}" pull
    docker compose "${env_args[@]}" up -d --remove-orphans
    docker compose "${env_args[@]}" ps
  )
done
