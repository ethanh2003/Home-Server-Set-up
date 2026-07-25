# 2026-07-01T23-40-48-5jAo-pingvin_share_nic_access_smtp_self_signed_cert_fix

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f200e-7fd2-72a2-98f4-d3e3cf0c8ba4
updated_at: 2026-07-01T23:43:57+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/01/rollout-2026-07-01T23-40-48-019f200e-7fd2-72a2-98f4-d3e3cf0c8ba4.jsonl
cwd: /home/ethan/Documents/Codex/2026-07-01-nic-needs-share-access-at-nicholas

# Added Nic to Pingvin Share by fixing SMTP TLS validation and creating the user

Rollout context: The user said Nic needed share access at `nicholas.t.jensen2121@gmail.com` with username `nic`, and the first add attempt had errored. The work happened in `/home/ethan/docker/pingvin-share` with the shared `smtp-relay` stack also inspected.

## Task 1: Fix failed Pingvin user creation for Nic

Outcome: success

Preference signals:

- The user’s request was concrete and operational: "Nic needs share access at nicholas.t.jensen2121@gmail.com username nic but I tried adding it and got an error" -> in similar cases, the agent should treat this as a live failure to debug and resolve, not as a request for advice.
- The rollout showed the user wanted the account created despite the error path, which implies future similar requests should aim to complete the account/mail workflow end-to-end rather than stop at explaining the problem.

Key steps:

- Checked Pingvin compose/runtime state, logs, and SQLite config after loading prior memory that Pingvin settings are DB-backed.
- Found the root cause in app logs: invite mail failed with `self-signed certificate` during STARTTLS to the local SMTP relay.
- Confirmed the create path is transactional and sends the invite email inside the transaction, so the email failure caused the user creation to roll back.
- Backed up `data/pingvin-share.db`, changed `smtp.allowUnauthorizedCertificates` to `true` in the Pingvin Config table, and restarted only `pingvin-share`.
- Created `nic` via the app sign-up path and sent the invite/temporary password to the Gmail address through `smtp-relay`.
- Verified the account exists in SQLite, Pingvin health returns `200`, and the relay log shows delivery to Gmail with `status=sent`.

Failures and how to do differently:

- The first add failed because Pingvin rejected the relay’s self-signed STARTTLS certificate; for this stack, a failing invite can prevent the user row from persisting.
- When this happens, check Pingvin’s SMTP TLS setting in SQLite before trying broader app changes.
- Keep the fix minimal: adjust the DB-backed SMTP toggle, restart Pingvin, then retry the user creation/invite flow.

Reusable knowledge:

- Pingvin Share X here is DB-configured; `smtp.allowUnauthorizedCertificates` lives in the `Config` table and controls Nodemailer TLS `rejectUnauthorized`.
- User creation for admin-added accounts goes through a transactional path that sends the invite email during `UserService.create`; if the mail send throws, the user row may not persist.
- The local relay `smtp-relay` accepted the message and forwarded it to Google successfully once Pingvin stopped rejecting the cert.

References:

- `docker compose ps` in `/home/ethan/docker/pingvin-share` showed `pingvin-share` and `pingvin-redis` healthy.
- App log error: `Error: self-signed certificate; if the root CA is installed locally, try running Node.js with --use-system-ca`.
- `UserController.create` calls `UserDTO().from(await this.userService.create(user))`.
- `UserService.create` creates the user and then calls `this.emailService.sendInviteEmail(dto.email, randomPassword)` inside a transaction.
- `EmailService.getTransporter()` sets `tls.rejectUnauthorized: !this.config.get("smtp.allowUnauthorizedCertificates")`.
- SQLite backup created before edit: `/home/ethan/docker/pingvin-share/data/pingvin-share.db.bak-nic-access-20260701T234214Z`.
- Verification evidence: DB row for `nic` / `nicholas.t.jensen2121@gmail.com`; `share_health_http=200`; relay log line with `dsn=2.0.0, status=sent`.
