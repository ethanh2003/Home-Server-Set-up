#!/bin/bash
docker compose -f arr-stack.yml down
docker compose -f jellyfin-stack.yml down
docker compose -f homeassistant-stack.yml down
docker compose -f actualbudget-stack.yml down
docker compose -f immich-stack.yml down
