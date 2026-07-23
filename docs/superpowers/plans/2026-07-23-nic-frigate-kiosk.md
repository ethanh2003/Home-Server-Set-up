# Nic Frigate Kiosk Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Nic's normal Home Assistant experience open only the Frigate Cameras dashboard in kiosk presentation.

**Architecture:** Store five Browser Mod settings at Nic's user scope through the authenticated WebSocket settings command. Browser Mod merges these settings for Nic without changing global, browser-specific, or Ethan user settings.

**Tech Stack:** Home Assistant 2026.7.1, Browser Mod 3.1.0, Home Assistant WebSocket API.

## Global Constraints

- This is a kiosk presentation restriction, not authorization.
- Only Nic's Browser Mod user settings may change.
- Back up `.storage/browser_mod.storage` before mutation.
- Do not restart Home Assistant unless live verification shows it is necessary.

---

### Task 1: Apply Nic's User-Level Kiosk Settings

**Files:**
- Back up: `/home/ethan/docker/home-assistant/config/homeassistant/.storage/browser_mod.storage`
- Modify through Browser Mod API: `/home/ethan/docker/home-assistant/config/homeassistant/.storage/browser_mod.storage`

**Interfaces:**
- Consumes: Nic's Home Assistant user ID and Browser Mod WebSocket command `browser_mod/settings`.
- Produces: `user_settings[<Nic user ID>]` with the five approved settings.

- [ ] **Step 1: Capture the baseline and create a timestamped backup**

Confirm Nic has no existing Browser Mod settings, then copy the storage file into `/home/ethan/docker/home-assistant/backups/` with a UTC timestamp and mode `0600`.

- [ ] **Step 2: Apply the five settings over an authenticated admin WebSocket**

Send one `browser_mod/settings` message per value:

```json
{"type":"browser_mod/settings","user":"<Nic user ID>","key":"defaultPanel","value":"frigate-cameras"}
{"type":"browser_mod/settings","user":"<Nic user ID>","key":"defaultAction","value":{"action":"browser_mod.navigate","data":{"path":"/frigate-cameras/cameras"}}}
{"type":"browser_mod/settings","user":"<Nic user ID>","key":"kioskMode","value":true}
{"type":"browser_mod/settings","user":"<Nic user ID>","key":"hideSidebar","value":true}
{"type":"browser_mod/settings","user":"<Nic user ID>","key":"hideHeader","value":true}
```

- [ ] **Step 3: Verify storage isolation**

Read Browser Mod storage and assert that Nic has exactly the approved non-null values, Ethan has no user-level kiosk settings, and global Browser Mod settings remain unchanged.

### Task 2: Verify Runtime Health and Handoff

**Files:**
- Update: `/data/Obsidian/Main/Homelab/Documentation/Home Assistant - Frigate Dashboard.md`

**Interfaces:**
- Consumes: Browser Mod's stored settings and the existing `frigate-cameras` dashboard.
- Produces: Verified kiosk configuration and a durable operational note.

- [ ] **Step 1: Verify Browser Mod's user resolution**

Use Browser Mod's live `browser_mod/connect` subscription to confirm the stored user map contains Nic's settings. Verify the frontend default-panel patch resolves `frigate-cameras` when passed Nic's user ID and does not return that panel for Ethan.

- [ ] **Step 2: Verify Home Assistant health**

Confirm `HomeAssistant` remains healthy, `https://home.ethanh.online/frigate-cameras/cameras` returns HTTP 200, and recent logs contain no Browser Mod setup errors.

- [ ] **Step 3: Record and hand off**

Append the Nic-specific kiosk settings and limitation to the existing Obsidian deployment note. Tell the user that Nic must refresh or sign in again for final visual confirmation.
