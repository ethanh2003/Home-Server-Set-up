# docs/github-runner.md

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

# GitHub Runner

The `github-runner/` stack runs a containerized self-hosted GitHub Actions runner with Docker socket access. Treat it as privileged: any workflow allowed to use labels `self-hosted`, `linux`, `homelab`, and `docker` can control Docker on this host.

## Setup

1. In GitHub, open the repository settings and create a Linux x64 self-hosted runner registration token.
2. Copy `github-runner/.env.example` to `github-runner/.env`.
3. Set `GITHUB_RUNNER_TOKEN` to the short-lived registration token.
4. Start the runner:

```bash
cd /home/ethan/docker/github-runner
docker compose up -d --build
```

The runner registers with labels `homelab,docker`; GitHub automatically adds `self-hosted`, `linux`, and architecture labels.

## Rotation

Registration tokens expire. If the runner is recreated after the token expires, generate a new token in GitHub and update `github-runner/.env`.
