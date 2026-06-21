#!/usr/bin/env bash
set -euo pipefail

cd /home/runner

: "${GITHUB_REPOSITORY_URL:?Set GITHUB_REPOSITORY_URL to the repository URL.}"
: "${GITHUB_RUNNER_TOKEN:?Set GITHUB_RUNNER_TOKEN to a short-lived GitHub runner registration token.}"

runner_name="${GITHUB_RUNNER_NAME:-homelab-$(hostname)}"
runner_labels="${GITHUB_RUNNER_LABELS:-homelab,docker}"
runner_work="${GITHUB_RUNNER_WORKDIR:-_work}"

cleanup() {
  if [[ -f .runner ]]; then
    ./config.sh remove --unattended --token "$GITHUB_RUNNER_TOKEN" || true
  fi
}

trap cleanup EXIT INT TERM

if [[ ! -f .runner ]]; then
  ./config.sh \
    --unattended \
    --url "$GITHUB_REPOSITORY_URL" \
    --token "$GITHUB_RUNNER_TOKEN" \
    --name "$runner_name" \
    --labels "$runner_labels" \
    --work "$runner_work" \
    --replace
fi

exec ./run.sh
