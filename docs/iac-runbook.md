# Homelab IaC Runbook

This repo treats `/home/ethan/docker` as the declarative source for Docker Compose stacks. Compose files, examples, scripts, workflows, and encrypted secret files are tracked. Plain `.env` files, config directories, databases, logs, backups, and generated runtime data stay untracked.

## Local Validation

Run:

```bash
./scripts/iac-validate.sh
```

The validator checks every `*/docker-compose.yml`. If a stack has `.env`, it uses that file. If not, it falls back to `.env.example`.

## Secret Files

Use SOPS with age for secrets. Store encrypted stack env files as one of:

- `<stack>/.env.sops`
- `<stack>/.env.sops.yaml`
- `<stack>/.env.sops.yml`
- `<stack>/*.sops.env`

Decrypt on the homelab host:

```bash
./scripts/secrets-decrypt.sh
./scripts/secrets-decrypt.sh --stack immich
```

The scripts write ignored plaintext `.env` files with restrictive permissions.

## Deploys

Main-branch deploys use:

```bash
./scripts/iac-deploy-changed.sh BASE_REF HEAD_REF
```

Only changed stack directories are deployed. The deploy path validates Compose, pulls images, runs `docker compose up -d --remove-orphans`, and prints `docker compose ps`. It never removes volumes.

## Renovate

Renovate waits seven days before proposing container updates. Patch and minor Docker Compose updates can automerge after checks pass. Major updates require review.
