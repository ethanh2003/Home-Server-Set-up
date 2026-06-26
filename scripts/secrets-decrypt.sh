#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/iac-common.sh
source "$script_dir/lib/iac-common.sh"

root="$(iac_repo_root)"
target_stack=""
repo_owner="$(stat -c '%u:%g' "$root")"

if [[ "${1:-}" == "--stack" ]]; then
  target_stack="${2:-}"
  [[ -n "$target_stack" ]] || {
    printf 'Usage: %s [--stack STACK]\n' "$0" >&2
    exit 1
  }
elif [[ $# -gt 0 ]]; then
  printf 'Usage: %s [--stack STACK]\n' "$0" >&2
  exit 1
fi

if [[ -n "${SOPS_AGE_KEY:-}" && -z "${SOPS_AGE_KEY_FILE:-}" ]]; then
  key_file="$(mktemp)"
  trap 'rm -f "$key_file"' EXIT
  chmod 600 "$key_file"
  printf '%s\n' "$SOPS_AGE_KEY" >"$key_file"
  export SOPS_AGE_KEY_FILE="$key_file"
fi

mapfile -t encrypted_files < <(
  if [[ -n "$target_stack" ]]; then
    find "$root/$target_stack" -maxdepth 1 -type f \( -name '*.sops.env' -o -name '.env.sops' -o -name '.env.sops.yaml' -o -name '.env.sops.yml' \) 2>/dev/null | sort
  else
    find "$root" -mindepth 2 -maxdepth 2 -type f \( -name '*.sops.env' -o -name '.env.sops' -o -name '.env.sops.yaml' -o -name '.env.sops.yml' \) \
      ! -path "$root/.git/*" \
      ! -path "$root/.github/*" \
      ! -path "$root/secrets/*" | sort
  fi
)

if [[ "${#encrypted_files[@]}" -eq 0 ]]; then
  printf 'No encrypted env files found.\n'
  exit 0
fi

if ! command -v sops >/dev/null 2>&1; then
  printf 'sops is required to decrypt encrypted env files.\n' >&2
  exit 1
fi

for encrypted in "${encrypted_files[@]}"; do
  stack_dir="$(dirname "$encrypted")"
  output="$stack_dir/.env"
  tmp_output="$(mktemp)"
  printf 'Decrypting %s -> %s\n' "$(realpath --relative-to="$root" "$encrypted")" "$(realpath --relative-to="$root" "$output")"
  if [[ "$encrypted" == *.sops.env || "$(basename "$encrypted")" == ".env.sops" ]]; then
    sops --decrypt --input-type dotenv --output-type dotenv "$encrypted" >"$tmp_output"
  else
    sops --decrypt "$encrypted" >"$tmp_output"
  fi
  install -m 0600 "$tmp_output" "$output"
  chown "$repo_owner" "$output" 2>/dev/null || true
  rm -f "$tmp_output"
done
