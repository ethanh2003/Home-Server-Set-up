# 2026-07-23T18-57-00-37aq-home_assistant_frigate_dashboard_and_nic_kiosk_restriction

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f9056-918d-7032-98b1-3a3f0d415d7a
updated_at: 2026-07-23T19:44:20+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/23/rollout-2026-07-23T18-57-00-019f9056-918d-7032-98b1-3a3f0d415d7a.jsonl
cwd: /home/ethan

# Home Assistant Frigate dashboard was built, then Nic was restricted to that dashboard via Browser Mod user-scoped kiosk settings.

Rollout context: Work happened in `/home/ethan` with the Home Assistant stack under `/home/ethan/docker/home-assistant`, Frigate under `/home/ethan/docker/frigate`, and Obsidian notes under `/data/Obsidian/Main`. The user first asked for a dedicated Frigate dashboard with a click-to-view red-light behavior, then later asked to limit user Nic to only that dashboard as a kiosk-style restriction.

## Task 1: Build a standalone Frigate dashboard with red-light-on-view behavior

Outcome: success

Preference signals:
- When the user said “i want a dashboard that only has that on it,” they explicitly rejected extending the existing `Device - Cameras` dashboard and wanted a dedicated purpose-built dashboard instead.
- When asked what should turn the light back off, the user chose “Close the viewer (Recommended)” -> this indicates they want close/dismiss behavior to end the viewing session, not a manual stop button or timeout-driven flow.
- When asked which light should turn red, the user chose `Couch R`; when asked how to restore it, they chose “Restore prior state (Recommended)” -> this suggests a preference for minimal physical impact and exact restoration rather than a fixed off/white fallback.
- When asked whether the dashboard would be viewed by more than one device at once, the user chose “Single viewer (Recommended)” -> this allowed a simpler single-session design without concurrency tracking.

Key steps:
- Inspected the existing HA YAML dashboards and confirmed `Device - Cameras` was already present.
- Found the live Frigate integration and the actual camera entities: `camera.living_room_dog_view` and `camera.living_room_couch_view`.
- Installed Browser Mod through HACS (version `3.1.0`) and configured Frigate as a Home Assistant integration pointing at `http://127.0.0.1:5000`.
- Added a standalone YAML dashboard at `frigate-cameras` with two picture cards, each opening a fullscreen Browser Mod popup.
- Added a helper package with:
  - `input_boolean.frigate_camera_view_active`
  - `timer.frigate_camera_view_failsafe`
  - `script.frigate_camera_view_start`
  - `script.frigate_camera_view_stop`
  - an automation that calls the stop script on `timer.finished`
- The start script snapshots `light.smart_rgbtw_bulb_5` (Couch R) into a temporary scene, marks the session active, starts the timer, and turns the light red.
- The stop script restores the scene, cancels the timer, deletes the temp scene, and clears the helper.

Failures and how to do differently:
- A first attempt to use the Frigate API over LAN would have been incorrect; the correct stable path was loopback-only (`127.0.0.1:5000`) from Home Assistant.
- A forced fail-safe test initially looked like it failed because Matter/attribute propagation lagged behind the automation; the real issue was the test’s immediate assertion, not the implementation. Switching to condition-based polling showed the restore completed successfully.

Reusable knowledge:
- In this stack, the Frigate HA entity IDs were normalized to `camera.living_room_dog_view` and `camera.living_room_couch_view`; both returned streaming state and JPEG snapshots through `/api/camera_proxy/...`.
- Browser Mod services `browser_mod.sequence` and `browser_mod.popup` were available after HACS install.
- `Browser Mod 3.1.0` supports `dismiss_action` and `timeout_action`, which made close-based cleanup viable.
- The Frigate container was exposed to HA only on host loopback port `5000`; LAN access to that port was blocked.

References:
- [1] `/home/ethan/docker/frigate/docker-compose.yml:15-20` — added `127.0.0.1:5000:5000` loopback binding.
- [2] `/home/ethan/docker/home-assistant/config/homeassistant/configuration.yaml:84-85` — registered the `frigate-cameras` dashboard.
- [3] `/home/ethan/docker/home-assistant/config/homeassistant/packages/frigate_dashboard.yaml:1-83` — session helpers, timer, scripts, and fail-safe automation.
- [4] `/home/ethan/docker/home-assistant/config/homeassistant/dashboards/frigate-cameras.yaml:1-75` — standalone two-tile Frigate dashboard.
- [5] `/data/Obsidian/Main/Homelab/Documentation/Home Assistant - Frigate Dashboard.md:1-56` — deployment note and verification summary.
- [6] Verification snippets: `camera_snapshots=2/2`, `normal_restore=exact`, `off_restore=exact`, `failsafe_restore=exact`, `dashboard=1_view_2_cards`, `completion_verification=passed`.

## Task 2: Restrict Nic to the Frigate dashboard with Browser Mod kiosk settings

Outcome: success

Preference signals:
- When the user said “kiosk restriction,” they clarified they wanted a presentation restriction rather than a true auth boundary.
- The user accepted the proposed per-user approach, so future similar requests should default to Browser Mod user-scoped kiosk settings rather than changing all dashboards or trying to enforce hard authorization.
- The user later said “approved, apply now,” indicating they want the implementation carried through immediately once the design is approved.

Key steps:
- Inspected Home Assistant users and confirmed Nic is a normal user (`system-users`) and not an admin.
- Determined Browser Mod stores per-user settings in `browser_mod.storage` and already has user-level settings support.
- Chose a per-user kiosk design using Nic’s Home Assistant user ID, not browser-wide settings.
- Created and committed a design spec and an implementation plan in `docs/superpowers/specs/...` and `docs/superpowers/plans/...` before changing the live instance.
- Backed up `browser_mod.storage` to `/home/ethan/docker/home-assistant/backups/browser-mod-before-nic-kiosk-20260723T194102Z.json`.
- Applied Nic’s Browser Mod user settings via authenticated WebSocket fire-and-forget calls:
  - `defaultPanel = frigate-cameras`
  - `defaultAction = browser_mod.navigate` to `/frigate-cameras/cameras`
  - `kioskMode = true`
  - `hideSidebar = true`
  - `hideHeader = true`
- Verified the settings persisted exactly under Nic’s user ID, with Ethan’s settings unchanged and global Browser Mod settings still empty.
- Verified Browser Mod’s live resolver returns `frigate-cameras` for Nic but not for Ethan.
- Updated the existing Obsidian note with a Nic-specific kiosk section and the backup path.

Failures and how to do differently:
- The first WebSocket client waited for a response to `browser_mod/settings`, but the handler is fire-and-forget and does not send one. The command succeeded on the server; the client timeout was the only failure. Future similar calls should send the settings and verify persistence from storage, not expect a reply.
- An impersonated Nic session was not available because Nic had no active refresh token. For future user-scoped Browser Mod verification, verify via stored settings plus Browser Mod’s resolver, and use a real client session only when the user actually has one.

Reusable knowledge:
- Browser Mod 3.1.0 stores per-user kiosk settings in `browser_mod.storage` under `user_settings[<user_id>]`.
- Browser Mod’s `browser_mod/settings` command persists values via WebSocket but does not emit a success message to the client.
- Browser Mod’s frontend patch resolves default panels by priority: user settings first, then browser settings, then global settings.
- For this setup, user-scoped kiosk changes are presentation-only: Nic gets redirected and hidden navigation, but the account remains a normal Home Assistant user.

References:
- [1] Backup path: `/home/ethan/docker/home-assistant/backups/browser-mod-before-nic-kiosk-20260723T194102Z.json`.
- [2] Persisted settings verification: `nic_settings=exact`, `ethan_settings=unchanged`, `global_settings=unchanged`.
- [3] Resolver verification: `default_panel_nic=frigate-cameras`, `default_panel_ethan=unchanged`, `browser_mod_live_subscription=verified`.
- [4] Health verification: `home_assistant=running/healthy`, `dashboard_http=200`, `browser_mod_errors=none`.
- [5] Obsidian note updated at `/data/Obsidian/Main/Homelab/Documentation/Home Assistant - Frigate Dashboard.md` with a `Nic Kiosk` section and the presentation-vs-authorization limitation.
- [6] Committed planning artifacts: `docs/superpowers/specs/2026-07-23-nic-frigate-kiosk-design.md` and `docs/superpowers/plans/2026-07-23-nic-frigate-kiosk.md`.
