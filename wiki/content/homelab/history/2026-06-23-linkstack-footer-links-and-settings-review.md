# 2026-06-23T02-30-59-EOLb-linkstack_footer_links_and_settings_review

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019ef251-0ffa-7da0-81a5-95eff8f2b295
updated_at: 2026-06-23T02:39:29+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/23/rollout-2026-06-23T02-30-59-019ef251-0ffa-7da0-81a5-95eff8f2b295.jsonl
cwd: /home/ethan/docker/linkstack
git_branch: main

# LinkStack footer-link cleanup and follow-up review of hardening settings

Rollout context: The work happened in `/home/ethan/docker/linkstack` against a LinkStack container backed by a persisted `/htdocs` Docker volume. The repo checkout only contained `compose.yml`, so the actual app files and `.env` lived inside the running container/volume.

## Task 1: Remove privacy/terms/linkstack links from public URLs/footer

Outcome: success

Preference signals:

- The user said: "i want to remove the privacy, toc, and link to linkstack site from my urls" -> they wanted the public-facing footer/navigation cleaned up without being forced to specify implementation details.
- The user then narrowed it further with: "remove Home Contact" -> they expected iterative, targeted edits to the same footer area, not a broad redesign.

Key steps:

- Confirmed the app was a running `linkstackorg/linkstack:latest` container with `/htdocs` mounted as an anonymous volume; the checkout itself only exposed `compose.yml`.
- Found the relevant controls by searching the mounted app files and `.env` inside the container.
- Identified that the public footer links were controlled by `.env` booleans: `DISPLAY_FOOTER_TERMS`, `DISPLAY_FOOTER_PRIVACY`, `DISPLAY_CREDIT_FOOTER`, plus `DISPLAY_CREDIT` for the user profile footer credit module, and later `DISPLAY_FOOTER_HOME` / `DISPLAY_FOOTER_CONTACT` for the remaining footer items.
- Backed up `/htdocs/.env` before each group of changes.
- Used LinkStack’s own `GeoSot\EnvEditor\Facades\EnvEditor::editKey()` path inside the container rather than editing raw files directly.
- Cleared Laravel caches with `php artisan cache:clear`, `config:clear`, and `view:clear` after changes.
- Verified by curling `http://localhost/@Percy` from inside the container and checking that the targeted footer strings were absent while normal profile links still rendered.

Failures and how to do differently:

- An initial check removed the admin/footer legal links but left the powered-by LinkStack branding on the profile footer, because that was controlled by `DISPLAY_CREDIT` in a separate template path.
- The agent had to trace the template split between `pages.blade.php` / `sidebar.blade.php` and `resources/views/linkstack/modules/footer.blade.php` before finding the right setting.
- The image lacked `sqlite3` and BusyBox `grep` was limited, so PHP/PDO and simpler shell commands were more reliable for inspection.

Reusable knowledge:

- In this LinkStack install, public footer/link visibility is largely driven by `.env` flags, not just Blade edits.
- `DISPLAY_FOOTER_TERMS`, `DISPLAY_FOOTER_PRIVACY`, `DISPLAY_FOOTER_HOME`, `DISPLAY_FOOTER_CONTACT`, `DISPLAY_CREDIT_FOOTER`, and `DISPLAY_CREDIT` are the key toggles for hiding the footer/legal/branding items on public pages.
- The user’s public profile page remained functional after these settings changed; only the footer chrome was removed.
- The container stayed healthy throughout (`linkstack-linkstack-1` remained `Up ... (healthy)`).

References:

- [1] `.env` keys changed inside the container volume:
  - `DISPLAY_FOOTER_TERMS=false`
  - `DISPLAY_FOOTER_PRIVACY=false`
  - `DISPLAY_CREDIT_FOOTER=false`
  - `DISPLAY_CREDIT=false`
  - `DISPLAY_FOOTER_HOME=false`
  - `DISPLAY_FOOTER_CONTACT=false`
- [2] Backup files created in `/htdocs/backups`:
  - `.env.footer-links-20260623T0234Z`
  - `.env.footer-home-contact-20260623T0237Z`
- [3] Verification result:
  - `OK: requested footer links/credit absent from /@Percy`
  - `docker compose ps` showed `linkstack-linkstack-1 ... Up ... (healthy)`
- [4] Root cause evidence from templates:
  - `resources/views/pages.blade.php` and `resources/views/layouts/sidebar.blade.php` use `DISPLAY_CREDIT_FOOTER`
  - `resources/views/linkstack/modules/footer.blade.php` uses `DISPLAY_CREDIT` and contains the `https://linkstack.org` / `powered-by-linkstack.svg` footer module

## Task 2: Review other LinkStack settings worth changing

Outcome: success

Preference signals:

- The user asked: "any other settings we should look at?" -> they wanted proactive review of adjacent settings, not only the one-off footer change.
- The follow-up response should prioritize the most impactful public-site hardening suggestions rather than a full dump of every setting.

Key steps:

- Inspected the current `.env` values without printing secret material.
- Queried the app through PHP/PDO to confirm the database shape and the current user/profile state.
- Looked at the admin config screen to map available toggles to current env values.
- Tested HTTP behavior by fetching `/@Percy`, `/login`, and `/register`.
- Checked URL generation with `Host: ethan-herring.com` and `X-Forwarded-Proto: https` to see whether the app was producing HTTPS or still generating HTTP share/meta URLs.

Failures and how to do differently:

- `APP_ENV=local`, `APP_DEBUG=true`, and `LOG_LEVEL=debug` were still set for a public site; this is a notable hardening gap.
- Even with forwarded HTTPS headers, the app generated `http://ethan-herring.com/@Percy`, so HTTPS-related settings deserve review.
- `register` was already effectively disabled (`/register` returned 404), so that part did not need extra action.

Reusable knowledge:

- The current public-site risk profile is mostly about production hardening rather than registration leakage.
- The most impactful settings to review next are `APP_ENV`, `APP_DEBUG`, `LOG_LEVEL`, `FORCE_HTTPS`, `FORCE_ROUTE_HTTPS`, and branding (`APP_NAME`).
- Current notable env state at the time of review:
  - `APP_ENV=local`
  - `APP_DEBUG=true`
  - `LOG_LEVEL=debug`
  - `APP_NAME="LinkStack"`
  - `FORCE_HTTPS=false`
  - `FORCE_ROUTE_HTTPS=false`
  - `ALLOW_USER_HTML=true`
  - `ALLOW_CUSTOM_CODE_IN_THEMES=true`
  - `REGISTER_AUTH=verified`
  - `ALLOW_REGISTRATION=false`
  - `MAIL_MAILER=built-in`
- The site generated `http://ethan-herring.com/@Percy` even when queried with `X-Forwarded-Proto: https`, which suggests HTTPS forcing may be needed if the intent is canonical HTTPS links.

References:

- [1] Current env snapshot captured during review:
  - `APP_ENV=local`, `APP_DEBUG=true`, `LOG_LEVEL=debug`
  - `FORCE_HTTPS=false`, `FORCE_ROUTE_HTTPS=false`
  - `APP_NAME="LinkStack"`
  - `ALLOW_USER_HTML=true`, `ALLOW_CUSTOM_CODE_IN_THEMES=true`
  - `ALLOW_REGISTRATION=false`, `/register` returned `404`
- [2] HTTP evidence:
  - `curl` with `Host: ethan-herring.com` and `X-Forwarded-Proto: https` returned `og:url` / `twitter:url` / `data-share` values using `http://ethan-herring.com/@Percy`
- [3] Repo/UI mapping:
  - `resources/views/components/config/config.blade.php` exposes toggles for `DISPLAY_CREDIT`, `DISPLAY_CREDIT_FOOTER`, `DISPLAY_FOOTER_*`, `FORCE_HTTPS`, `FORCE_ROUTE_HTTPS`, `ALLOW_USER_HTML`, `ALLOW_CUSTOM_CODE_IN_THEMES`, `ENABLE_BUTTON_EDITOR`, etc.
