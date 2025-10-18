#!/bin/bash
SCRIPT_DIR=$(dirname "$0")
docker compose \
  -f "$SCRIPT_DIR/../arr-stack.yml" \
  -f "$SCRIPT_DIR/../jellyfin-stack.yml" \
  -f "$SCRIPT_DIR/../homeassistant-stack.yml" \
  -f "$SCRIPT_DIR/../actualbudget-stack.yml" \
  -f "$SCRIPT_DIR/../dozzle-stack.yml" \
  -f "$SCRIPT_DIR/../portainer-stack.yml" \
  down --remove-orphans
