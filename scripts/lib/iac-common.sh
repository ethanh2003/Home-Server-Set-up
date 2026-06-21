#!/usr/bin/env bash

iac_repo_root() {
  if [[ -n "${IAC_REPO_ROOT:-}" ]]; then
    printf '%s\n' "$IAC_REPO_ROOT"
    return 0
  fi

  git rev-parse --show-toplevel 2>/dev/null
}

iac_stack_dirs() {
  local root="$1"

  find "$root" -mindepth 2 -maxdepth 2 -type f -name docker-compose.yml \
    ! -path "$root/.git/*" \
    ! -path "$root/.github/*" \
    -printf '%h\n' | sort
}

iac_stack_name() {
  local root="$1"
  local stack_dir="$2"

  realpath --relative-to="$root" "$stack_dir"
}

iac_compose_env_args() {
  local stack_dir="$1"

  if [[ -f "$stack_dir/.env" ]]; then
    printf '%s\n' "--env-file"
    printf '%s\n' "$stack_dir/.env"
  elif [[ -f "$stack_dir/.env.example" ]]; then
    printf '%s\n' "--env-file"
    printf '%s\n' "$stack_dir/.env.example"
  fi
}

iac_ensure_proxy_net() {
  if docker network inspect proxy_net >/dev/null 2>&1; then
    printf 'Network proxy_net exists.\n'
    return 0
  fi

  printf 'Creating Docker network proxy_net.\n'
  docker network create proxy_net >/dev/null
}

iac_require_clean_ref() {
  local ref="$1"

  if [[ -z "$ref" ]]; then
    printf 'Missing required git ref.\n' >&2
    return 1
  fi
}
