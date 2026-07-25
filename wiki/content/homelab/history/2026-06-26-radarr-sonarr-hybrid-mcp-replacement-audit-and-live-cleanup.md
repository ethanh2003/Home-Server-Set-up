# 2026-06-26T23-36-09-lOaQ-radarr_sonarr_hybrid_mcp_replacement_audit_and_live_cleanup

> Generated from `/home/ethan/docker`. Edit the Git source, then run wiki sync.

thread_id: 019f064a-71bc-7fe0-814e-f4c17e4160b0
updated_at: 2026-06-28T06:44:49+00:00
rollout_path: /home/ethan/.codex/sessions/2026/06/26/rollout-2026-06-26T23-36-09-019f064a-71bc-7fe0-814e-f4c17e4160b0.jsonl
cwd: /home/ethan

# Implemented a dry-run Radarr/Sonarr replacement-audit workflow and then drove a live Radarr cleanup/replacement pass to reduce files over the 4 GiB cap.

Rollout context: The user wanted to audit arr-suite media libraries to downsize oversized files, grab missing items, and upgrade quality while generally capping files at 4 GiB for streaming reliability. The assistant first checked public MCP options and concluded a hybrid approach was best, then the user explicitly said to implement the plan. Work happened in `/home/ethan/docker` with the live arr-suite checkout at `/home/ethan/docker/arr-suite`; the repo root was already dirty with unrelated homelab changes.

## Task 1: Design/implement the hybrid MCP + dry-run audit plan
Outcome: success

Preference signals:
- The user first asked to "figure out if direct commands, existing radarr/sonarr mcp, new sonarr/radarr mcp is the best method" and later said "yep, create a new plan" -> future similar tasks should default to comparing live APIs vs MCPs before committing to a control path, and should keep a dry-run planning phase before making operational changes.
- The user then said "PLEASE IMPLEMENT THIS PLAN" -> once the plan is approved, proceed with implementation rather than re-litigating architecture.

Key steps:
- Discovered the live stack: `gluetun`, `qbittorrent`, `prowlarr`, `radarr`, `sonarr` in `arr-suite`.
- Verified the live APIs and qBittorrent endpoints were reachable; Radarr/Sonarr versions were `6.1.1.10360` and `4.0.17.2952`.
- Implemented a new dry-run audit script at `arr-suite/scripts/arr_replacement_audit.py` that writes CSV/Markdown/JSON snapshots and does not grab/delete/edit anything.
- Added a local-only MCP wrapper at `arr-suite/scripts/run-mcp-arr.sh`; verified `mcp-arr` starts over HTTP on localhost, and that its tool list includes `arr_status`, `radarr_get_queue`, `sonarr_get_queue`, `prowlarr_get_indexers`, and TRaSH profile tools.
- Added regression tests in `tests/test_arr_replacement_audit.py` before implementation and ran them until green.
- Wrote report files under `arr-suite/reports/replacement-audit-*`; added `arr-suite/reports/` to `.gitignore`.

Failures and how to do differently:
- `bash -n` was accidentally run against a Python file once; keep shell syntax checks scoped to shell scripts only.
- Sonarr v4 rejected the initial `episodefile` collection query with `400 BadRequest: seriesId or episodeFileIds must be provided`; the fix was to iterate per-series and map `episodeFileId` back through episode lists.
- A dataclass import edge case appeared when the module was loaded by file path in tests; replacing the dataclass with a plain class avoided the issue.
- The live host already had port `3000` bound, so the MCP wrapper needed an alternate port (verified with `MCP_ARR_PORT=3073`).

Reusable knowledge:
- `mcp-arr-server` is real and useful here; it exposes read-only and control tools for Radarr/Sonarr/Prowlarr plus TRaSH helpers, but the audit still needs direct API/DB logic for sizing, ETA, and batch gating.
- The dry-run audit script should stay read-only and output a snapshot plus per-report CSV/Markdown files.
- For Sonarr v4, per-series episode/file enumeration is safer than a global `episodefile` call.
- The repo root is already dirty; keep these changes scoped and do not assume clean git status.

References:
- `arr-suite/scripts/arr_replacement_audit.py`
- `arr-suite/scripts/run-mcp-arr.sh`
- `tests/test_arr_replacement_audit.py`
- `arr-suite/reports/replacement-audit-20260626T234807Z/summary.md`
- MCP verification output showed `mcp-arr` over HTTP with tools including `arr_status`, `radarr_get_queue`, `sonarr_get_queue`, `prowlarr_get_indexers`, and TRaSH tools.

## Task 2: Live Radarr replacement pass, queue cleanup, and import handling
Outcome: success

Preference signals:
- The user accepted the dry-run-first plan, but the live pass showed they care about practical completion of the actual downsizing, not just reports.
- The workflow repeatedly adapted to what was actually downloading; future similar runs should treat live queue state as the truth and continue iterating until the queue is genuinely clear or blocked.

Key steps:
- Ran live Radarr replacement batches against the final reports and actively monitored qBittorrent progress.
- Removed and blocklisted metadata-only or stalled zero-seed downloads when they were clearly dead-end candidates.
- Triggered Radarr manual import when a completed download was considered "not an upgrade" but still represented the desired downsize.
- Kept checking qBittorrent speed, ETA, and queued movie status until queue items cleared.
- Final Radarr queue became empty (`radarr_queue_total 0`).

Failures and how to do differently:
- The first executor behavior matched rows by title only, which is unsafe for duplicate-title movies like `Scream` and `How to Train Your Dragon`. That was fixed by matching on `movie_id` when present, or `title + year` otherwise.
- Retry logic initially treated too many skipped rows as permanently complete. It was narrowed so only `already_under_cap` is treated as completed; retryable skips stay retryable.
- Rejected-title matching initially missed HTML entities, symbols, and truncated release names; normalization was hardened with HTML unescape plus aggressive punctuation cleanup.
- Some candidate releases looked good in Prowlarr but were metadata-only or stalled in qBittorrent; the practical rule became: if it stalls with zero seeds / metadata-only behavior, remove and blocklist it rather than letting it occupy the queue.

Reusable knowledge:
- The final audit counts moved from `133` oversized Radarr files down to `2` remaining rows (`The Devil Wears Prada 2` and `Avalon High`); several others were successfully reduced below cap.
- The successful downsize path for live downloads was often `1080p WEBRip/WEB-DL` or `1080p BluRay` candidates under the 4 GiB cap, with Prowlarr indexer availability and actual qBittorrent behavior used as the real gate.
- qBittorrent had unrelated Sonarr stale/meta items still present; those should not block Radarr-only work if the gate is set appropriately.
- Manual imports are sometimes needed after a completed download if Radarr marks the result as not an upgrade.

References:
- Final Radarr audit report directory: `arr-suite/reports/replacement-audit-radarr-final-20260628T064330Z`
- State log: `arr-suite/reports/radarr-deep-all-replace-state.jsonl`
- Fresh verification at the end showed `radarr_queue_total 0`.
- Final validation passed: `python3 -m unittest tests.test_arr_replacement_audit -v` -> `35` tests OK; `python3 tests/test-secret-hygiene.py` -> PASS; `py_compile` for both scripts -> OK.
- Live blockers that were handled repeatedly were `metadata_only`, `stalled_zero_seed`, and `not_meaningfully_smaller`.

## Task 3: Repo hygiene and verification discipline
Outcome: success

Preference signals:
- The user did not explicitly ask for tests, but the workflow showed the agent should verify aggressively before claiming completion; in similar future homelab automation work, default to fresh tests and live queue checks instead of relying on prior success logs.

Reusable knowledge:
- `python3 -m unittest tests.test_arr_replacement_audit -v` is a good target check for this workflow; it reached 35 passing tests after the fixes.
- `python3 tests/test-secret-hygiene.py` passed and is a useful guard for avoiding inline-secret regressions in repo edits.
- `radarr_mass_replace.py` now has safer persistence semantics: it no longer treats all skipped rows as complete, and it records failures/rejected titles for future retries.

References:
- `.gitignore` was updated to ignore `arr-suite/reports/`.
- The repo root remained dirty with unrelated changes; only the arr-suite scripts/tests and `.gitignore` were part of this rollout.
