#!/bin/bash
docker compose -f arr-stack.yml up -d --remove-orphans
docker compose -f jellyfin-stack.yml up -d --remove-orphans
docker compose -f homeassistant-stack.yml up -d --remove-orphans
docker compose -f actualbudget-stack.yml up -d --remove-orphans
docker compose -f immich-stack.yml up -d --remove-orphans
