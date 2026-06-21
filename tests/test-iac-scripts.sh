#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_file() {
  [[ -f "$1" ]] || fail "missing file: $1"
}

assert_executable() {
  [[ -x "$1" ]] || fail "not executable: $1"
}

for script in \
  "$repo_root/scripts/iac-validate.sh" \
  "$repo_root/scripts/iac-changed-stacks.sh" \
  "$repo_root/scripts/iac-deploy-changed.sh" \
  "$repo_root/scripts/secrets-decrypt.sh"; do
  assert_file "$script"
  assert_executable "$script"
  bash -n "$script"
done

for script in \
  "$repo_root/scripts/npm-export.py" \
  "$repo_root/scripts/traefik-generate-dynamic.py"; do
  assert_file "$script"
  assert_executable "$script"
  python3 -m py_compile "$script"
done

mkdir -p "$tmpdir/repo/stack-a" "$tmpdir/repo/docs"
cat >"$tmpdir/repo/stack-a/docker-compose.yml" <<'YAML'
services:
  hello:
    image: hello-world:linux
YAML
cat >"$tmpdir/repo/docs/readme.md" <<'EOF'
fixture docs
EOF

git -C "$tmpdir/repo" init -q
git -C "$tmpdir/repo" config user.email test@example.invalid
git -C "$tmpdir/repo" config user.name 'IaC Test'
git -C "$tmpdir/repo" add .
git -C "$tmpdir/repo" commit -q -m initial
base="$(git -C "$tmpdir/repo" rev-parse HEAD)"

printf '# changed\n' >>"$tmpdir/repo/stack-a/docker-compose.yml"
git -C "$tmpdir/repo" add stack-a/docker-compose.yml
git -C "$tmpdir/repo" commit -q -m 'change stack'
head="$(git -C "$tmpdir/repo" rev-parse HEAD)"

changed="$(IAC_REPO_ROOT="$tmpdir/repo" "$repo_root/scripts/iac-changed-stacks.sh" "$base" "$head")"
[[ "$changed" == "stack-a" ]] || fail "expected stack-a, got: $changed"

IAC_REPO_ROOT="$tmpdir/repo" "$repo_root/scripts/iac-validate.sh"
IAC_REPO_ROOT="$tmpdir/repo" "$repo_root/scripts/secrets-decrypt.sh"

python3 "$repo_root/tests/test-traefik-migration.py" "$tmpdir"
python3 "$repo_root/tests/test-secret-hygiene.py"

git -C "$tmpdir/repo" checkout -q "$base"
printf '# changed\n' >>"$tmpdir/repo/docs/readme.md"
git -C "$tmpdir/repo" add docs/readme.md
git -C "$tmpdir/repo" commit -q -m 'docs only'
docs_head="$(git -C "$tmpdir/repo" rev-parse HEAD)"

docs_changed="$(IAC_REPO_ROOT="$tmpdir/repo" "$repo_root/scripts/iac-changed-stacks.sh" "$base" "$docs_head")"
[[ -z "$docs_changed" ]] || fail "expected no stack changes, got: $docs_changed"

printf 'PASS: iac scripts\n'
