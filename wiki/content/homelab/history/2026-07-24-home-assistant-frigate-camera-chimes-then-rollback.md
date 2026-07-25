# 2026-07-24T15-54-44-tTNo-home_assistant_frigate_camera_chimes_then_rollback

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f94d6-0dc7-7361-90d3-af0037e947da
updated_at: 2026-07-24T17:02:40+00:00
rollout_path: /home/ethan/.codex/sessions/2026/07/24/rollout-2026-07-24T15-54-44-019f94d6-0dc7-7361-90d3-af0037e947da.jsonl
cwd: /home/ethan

# Home Assistant Frigate camera indicator behavior was changed from red light to chimes, then later rolled back to the original red-light design after the user asked to switch back.

Rollout context: Worked in `/home/ethan` with the live Home Assistant stack under `/home/ethan/docker/home-assistant`; the user’s Home Assistant setup is bind-mounted and uses `HomeAssistant` as the primary container. The rollout involved a Frigate camera-view privacy/notification behavior change, then a later reversal back to the prior red-light behavior.

## Task 1: Replace Couch R red indicator with audible chimes

Outcome: success

Preference signals:

- The user asked to replace the red-light indicator with sound: "I want an audible chime to play when the home assistant camera stream is accessed, this would replace the light turning red, it would need a chime for connected and disconnected" -> the user prefers a direct behavioral swap rather than adding sound alongside the light.
- When asked where the sound should play, the user chose the living-room speaker -> in similar setups, default to the closest/most local speaker first, not a whole-home broadcast.
- When asked the cue style, the user chose ascending/descending chimes -> prefer nonverbal, brief directional cues over spoken notifications.
- When asked about busy-speaker behavior, the user chose "skip when busy" -> avoid interrupting active playback when possible.
- When asked about chime volume, the user chose "50% and restore" -> use a fixed audible cue volume with restoration afterward.
- When asked about chime failure, the user chose "Open camera anyway" -> camera access should not be blocked by notification failure.

Reusable knowledge:

- The live Home Assistant config is under `/home/ethan/docker/home-assistant/config/homeassistant` and is bind-mounted into the `HomeAssistant` container; restarting only `HomeAssistant` is enough to apply YAML/runtime changes.
- `ha-backup.sh --mode config` is the default backup path for this stack; it wrote a config backup to `/home/ethan/docker/home-assistant/backups/manual/20260724-161119` before edits.
- The living-room Cast entity `media_player.living_room_speaker` exists and supports `PLAY_MEDIA`, `VOLUME_SET`, `VOLUME_MUTE`, `TURN_ON`, `TURN_OFF`, `STOP`, and media browsing; it is a Google Home Mini device.
- Home Assistant’s media-source integration can expose authenticated local media under `/config/media` and use `media-source://media_source/local/...` URIs for playback.
- The initial chime implementation used `script.frigate_camera_chime`, a shared `frigate_camera_view_start` / `frigate_camera_view_stop` lifecycle, a 30-minute timer, and local MP3 assets under `/config/media/camera-chimes/`.
- The chime workflow succeeded only after changing Home Assistant’s `internal_url` from `https://home.ethanh.online` to `None` (automatic LAN resolution). The external URL remained `https://home.ethanh.online`.
- With the automatic internal URL, the Cast speaker accepted direct LAN media URLs like `http://192.168.1.113:8123/media/local/camera-chimes/camera-connected.mp3` and the chime workflow verified live.
- The chime files were generated as short mono MP3s (~0.993s each) and validated with `ffprobe`.
- The live acceptance checks confirmed: 50% playback/restoration worked, initially-off speaker returned to off, busy-speaker skip worked, repeated start/stop calls were idempotent, fail-safe cleanup worked, both cameras still returned JPEG snapshots, Couch R remained unchanged, and post-fix Cast errors were absent.
- The implementation required updating the Obsidian note at `/data/Obsidian/Main/Homelab/Documentation/Home Assistant - Frigate Dashboard.md` to record the chime behavior and rollback path.

Failures and how to do differently:

- The first runtime probe failed because Home Assistant’s WebSocket media-source resolve command no longer accepted an `entity_id` field; the corrected probe omitted it and succeeded.
- An explicit Cast `turn_on` call to the Google speaker timed out; the final working design removed that wake call and relied on direct media playback.
- The initial runtime harness assumed the internal URL should stay HTTPS; that caused Cast fetch failures because the speaker needed the LAN URL/automatic internal URL instead.
- The live verification harness had to be adjusted twice: first for the media-source API shape, then for the Cast network path.

References:

- [1] Chime test file: `/home/ethan/docker/tests/test_home_assistant_frigate_chimes.py`
- [2] Chime package: `/home/ethan/docker/home-assistant/config/homeassistant/packages/frigate_dashboard.yaml`
- [3] Media directory: `/home/ethan/docker/home-assistant/config/homeassistant/media/camera-chimes/camera-connected.mp3`, `/config/media/camera-chimes/camera-disconnected.mp3`
- [4] Internal URL change verified: `internal_url=None`, `external_url=https://home.ethanh.online` during the chime rollout
- [5] Live verification snippets: `media_source_resolution=verified`, `volume_50_then_restore_37=verified`, `initially_off_returns_off=verified`, `busy_speaker_skip=verified`, `failsafe_cleanup=settled`, `couch_r_unchanged=verified`

## Task 2: Switch back to the original red-light indicator

Outcome: partial

Preference signals:

- The user said "swich back to the red light" and then confirmed "yes" when asked whether to do a full rollback -> once they ask to revert, restore the previously verified red-light behavior rather than keeping the newer notification scheme.
- The user accepted using the previously verified red-light design rather than drafting a new one -> in reversions, reuse the old working implementation and avoid inventing a new variant.

Reusable knowledge:

- The original red-light implementation lived in `frigate_camera_view_start` / `frigate_camera_view_stop` and used `scene.create` + `scene.turn_on` + `scene.delete` around `light.smart_rgbtw_bulb_5`.
- The pre-chime config backup contained the original behavior and the previous `internal_url` value of `https://home.ethanh.online`.
- The rollback backup of the chime state was saved at `/home/ethan/docker/home-assistant/backups/manual/20260724-165637`.
- The rollback restored the prior YAML, removed the chime assets and test file, and set `internal_url` back to `https://home.ethanh.online`.
- The rollback regression suite was rewritten to assert the red-light behavior instead of chimes and passed locally after the revert.
- The red-light suite needed to wait for the light to actually reach the final red state; checking too early during transitions produced false failures.
- The Matter bulb’s live red/blue/green rendering does not always match naive RGB thresholds exactly; a too-strict RGB predicate caused a false negative during rollback verification even though the production automation had already restored the correct state.

Failures and how to do differently:

- The first rollback runtime probe failed because it sampled the light too early during the configured transition, seeing an intermediate blended color instead of the final red state.
- A later rollback probe also used an overly strict color assertion for the Matter bulb; the bulb reported commanded blue as `[87, 89, 255]`, so a test that only accepts canonical RGB primaries can fail even when the scene/restore logic is correct.
- The rollback cleanup block successfully restored the user’s light state and left `HomeAssistant` healthy, but the verification harness still needs a better predicate for Matter color states (prefer HS/XY-aware checks or exact snapshot/restore comparisons instead of strict RGB primaries).
- Because the live workspace is shared and dirty, the rollback was done in place with backups rather than by creating a separate worktree.

References:

- [1] Original red-light test file created for rollback: `/home/ethan/docker/tests/test_home_assistant_frigate_red_light.py`
- [2] Restored package: `/home/ethan/docker/home-assistant/config/homeassistant/packages/frigate_dashboard.yaml`
- [3] Restored internal URL: `internal_url=https://home.ethanh.online`
- [4] Rollback backup: `/home/ethan/docker/home-assistant/backups/manual/20260724-165637`
- [5] Evidence that the rollback cleanup succeeded even when the probe failed early: `stale_session_cleaned=verified`, `user_light_state_preserved=verified`
- [6] Latest runtime state after rollback attempts showed `HomeAssistant` healthy and `input_boolean.frigate_camera_view_active off`, with the helper/timer clear; the remaining issue was the verification predicate, not the live configuration
