# 2026-06-20T03-35-52-gvkx-homelab_iac_npm_to_traefik_runner_renovate

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019ee319-644e-7f23-8575-3eab44ee9ad5
updated_at: 2026-06-21T21:43:21+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/20/rollout-2026-06-20T03-35-52-019ee319-644e-7f23-8575-3eab44ee9ad5.jsonl
cwd: /home/ethan

# Planned and partially executed a homelab migration from Nginx Proxy Manager to Traefik, plus secret extraction for the arr stack.

Rollout context: The user first asked for a full infrastructure-as-code migration with Git tracking, self-hosted runners, and Renovate; then refined it to include NPM as IaC, secrets split out for easy re-linking of arr services, and finally asked whether to migrate from NPM to Traefik. The work happened in `/home/ethan/docker` on a very dirty homelab repo with existing unrelated changes.

## Task 1: IaC automation foundation for the homelab repo

Outcome: success

Preference signals:
- The user said they wanted to "migrate fully to infastructure as code with full git tracking and selfhosted runners and renovate" -> future similar work should default to GitHub Actions + a self-hosted runner + Renovate, rather than waiting for the user to request those explicitly.
- The user later clarified "This should also include NPM being infastrucutre as code" -> future similar migrations should treat NPM state as part of the IaC surface, not a manual UI-only config.
- The user asked to "pull[] all api keys into their respective areas to ensure they can easily re-link for the arr stack" -> future similar work should proactively separate service API keys and re-link state from Compose files into dedicated secret/config artifacts.

Key steps:
- Inspected repo shape and found `/home/ethan/docker` already contained many per-stack Compose directories, `.github` workflows, and a self-hosted GitLab remote in addition to GitHub.
- Added shell scripts for Compose validation, changed-stack detection, deploy, and SOPS decryption.
- Added a small test harness first, then verified it failed in the expected red state before implementing the scripts.
- Added GitHub Actions workflows for validation, deploy, and Renovate; added a containerized self-hosted GitHub runner stack.
- Added `renovate.json5` with `minimumReleaseAge: "7 days"`, Docker digest pinning, and patch/minor automerge.
- Added `.sops.yaml`, docs, and `.gitignore` updates for encrypted env files and runner workdirs.

Failures and how to do differently:
- The first runner image lacked the Compose plugin, so `docker compose` failed inside Actions; fixed by installing `docker-compose` into the runner image.
- The first deploy workflow ran against the clean GitHub checkout in the runner workspace, which broke relative binds like `./config` and `:/data`; fixed by pointing deploy to the live `/home/ethan/docker` root and verifying its HEAD.
- Git’s safe-directory protection blocked reading the live repo from inside the runner container; fixed by adding `/home/ethan/docker` to `safe.directory` in the deploy job.
- The runner initially mounted its workdir in a way that broke sibling Docker containers (like Renovate) from reading checkout files; fixed by aligning the runner workdir to a host path identical inside and outside the container.
- `iaC_validate` initially tried to validate stacks without decrypted env files, which produced blank bind specs like `:/data` and `:/var/lib/postgresql/data`; fixed by decrypting SOPS env files first in CI when the age key is available.

Reusable knowledge:
- In this repo, `docker compose config` is the fast truth source for stack rendering, but it only works when the expected env files exist or are decrypted first.
- A self-hosted runner that launches sibling Docker containers must use host paths that are identical both inside the runner and on the host; otherwise mounted config files can appear unreadable or map to the wrong place.
- `IAC_REPO_ROOT=/home/ethan/docker` became the live-root anchor for deploy logic so actions run against the real homelab checkout, not the ephemeral Actions workspace.

References:
- [1] `./tests/test-iac-scripts.sh` initially failed with `missing file: /home/ethan/docker/scripts/iac-validate.sh`, then passed after implementation.
- [2] First CI failure snippet: `docker: unknown command: docker compose` and `unknown flag: --env-file` inside the runner container.
- [3] Later deploy failure snippet: `fatal: detected dubious ownership in repository at '/home/ethan/docker'`.
- [4] Later deploy failure snippet: `invalid spec: :/data: empty section between colons` when compose validated before secrets were decrypted.
- [5] Final successful local validation: `./scripts/iac-validate.sh` reported all stacks, with only the pre-existing Minecraft `version` warning.

## Task 2: NPM-to-Traefik migration design and implementation

Outcome: success

Preference signals:
- The user asked, "eh what about migrating from npm to trafick" -> this should be interpreted as a real architecture migration question, not a small tweak.
- Earlier they had already said they wanted NPM to be IaC and wanted exact re-linking of arr APIs; once Traefik was introduced, the user still wanted migration planning grounded in the current live proxy layout rather than hand-wavy suggestions.
- The user explicitly chose the more complete migration scope when asked whether NPM desired state should include all current rows or only active Compose-managed services: they picked "All current rows (Recommended)" -> future NPM/Traefik migration planning should start from the full live routing inventory.

Key steps:
- Inspected the live NPM SQLite DB and confirmed it already contained many proxy hosts, including arr services, Immich, Home Assistant, Obsidian, and others.
- Verified prior memory that Cloudflare tunnels front NPM on this host, and that the current live proxy layout should be treated as the truth source for routing.
- Added Traefik compose and dynamic config artifacts and verified migrated hosts on Traefik’s validation port (`8088`) without cutting over production traffic.
- Confirmed NPM remained live on `80/443`, so the cutover was not completed during this rollout.

Failures and how to do differently:
- It is unsafe to assume Traefik can replace NPM just by adding config files; the real cutover still depends on a verified Cloudflare tunnel ingress change and moving Traefik onto the public edge.
- Because NPM is still serving production traffic, Traefik should be treated as a parallel staging/validation path until the tunnel cutover is explicitly verified.

Reusable knowledge:
- The live NPM DB path on this host is `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite`.
- Existing proxy rows include split-host Spotify routing (`spotify.ethanh.online` and `spotify-api.ethanh.online`) and many other services; those rows are useful input for a Traefik dynamic config generator.
- Validation on Traefik was done through its local exposed port (`8088`), which returned expected responses for migrated hosts while NPM still stayed live on `80/443`.

References:
- [1] NPM schema/rows were read via Python sqlite3 against `/home/ethan/docker/nginx-proxy-manager/nginx_config/data/database.sqlite`.
- [2] Traefik validation smoke checks returned `200`/`302` for migrated hosts on the validation port, while `npm` still showed as healthy on `80/443`.
- [3] Final state summary from the rollout: Traefik was running and responding on `8088`, but NPM remained the live external edge.

## Task 3: Secret extraction and re-linking for arr and related stacks

Outcome: success

Preference signals:
- The user explicitly asked to pull "all api keys into their respective areas to ensure they can easily re-link for the arr stack" -> future work should default to extracting app keys and related secrets out of Compose files into stack-local secret artifacts.
- The user’s NPM request and the later Traefik question together indicate they care about durable, reproducible proxy/re-link state rather than one-off manual configuration.

Key steps:
- Read the arr suite Compose file and service config XMLs to identify where API keys and VPN-related secrets lived.
- Confirmed that Radarr, Sonarr, and Prowlarr config XMLs contained 32-character API keys.
- Converted plaintext secrets into SOPS-encrypted env files for multiple stacks, including the arr stack and an SFTP FTP password that was still tracked in plaintext.
- Updated secret-hygiene tests to catch more secret-bearing env patterns like `PASS=`.
- Verified decryption of all encrypted env files with the age key on the host.

Failures and how to do differently:
- A staged diff scan caught an old plaintext credential in `sftp/docker-compose.yml` (`FTP_PASS=[REDACTED]`); fixed by moving it to `sftp/.env.sops` and changing Compose to `FTP_PASS=[REDACTED]`.
- The repo already had other unrelated plaintext or dirty files; the secret scan should be run against the staged set, not just the whole working tree, to avoid confusing unrelated pre-existing changes with the migration work.

Reusable knowledge:
- The arr service API keys were present in `arr-suite/config/{prowlarr,radarr,sonarr}/config.xml`.
- The host SOPS age private key lives at `/home/ethan/.config/sops/age/keys.txt`.
- There are now 14 encrypted env files in the repo (as counted at the end of the rollout).

References:
- [1] `arr-suite/config/prowlarr/config.xml`, `arr-suite/config/radarr/config.xml`, `arr-suite/config/sonarr/config.xml` contained API keys; the rollout masked them but verified their presence.
- [2] SFTP plaintext secret snippet that was fixed: `FTP_PASS=[REDACTED]`.
- [3] Decryption smoke test output showed `decrypt ok` for all `.env.sops` files plus `secrets/authentik_config.sops.env`.

## Task 4: Final verification and operational state

Outcome: success

Preference signals:
- The user kept steering toward concrete, working artifacts rather than just a conceptual plan, so final validation mattered more than prose.

Key steps:
- Built and recreated the runner container multiple times until it had Docker Compose, the live repo mount, and the correct workdir semantics for sibling Docker containers.
- Re-ran `IaC Validate`, `IaC Deploy`, and `Renovate` in GitHub Actions until they all succeeded.
- Performed a final local sanity check of live containers and edge routing.

Reusable knowledge:
- The live repo HEAD on both `HEAD` and `origin/main` ended at `d345f8f`.
- GitHub Actions final run IDs that passed: `IaC Validate` `27918237623`, `IaC Deploy` `27918237614`, `Renovate` `27918292369`.
- The runner container was healthy and listening, with `docker compose version` available inside it.
- The live edge was still split: Traefik answered on `8088`, while NPM remained the public edge on `80/443`.
