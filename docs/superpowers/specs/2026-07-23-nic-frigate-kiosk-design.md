# Nic Frigate Kiosk Design

## Goal

Restrict Nic's normal Home Assistant interface to the standalone `Frigate Cameras` dashboard without changing Ethan's interface or presenting the restriction as a security boundary.

## Design

Use Browser Mod 3.1.0 user-level settings keyed to Nic's Home Assistant user ID. Set:

- `defaultPanel` to `frigate-cameras`
- `defaultAction` to navigate to `/frigate-cameras/cameras`
- `kioskMode` to `true`
- `hideSidebar` to `true`
- `hideHeader` to `true`

The default panel opens the camera dashboard after login. The default action redirects full page loads back to the camera view. Kiosk mode and the explicit sidebar/header settings remove normal navigation controls.

Only Nic's Browser Mod user settings change. Global settings, browser-specific settings, Ethan's settings, Home Assistant groups, and dashboard content remain unchanged.

## Limitations

This is a kiosk presentation restriction, not authorization. Nic remains a standard Home Assistant user and could bypass the kiosk with direct API access or sufficiently deliberate frontend manipulation.

## Verification

- Back up `.storage/browser_mod.storage`.
- Apply settings through Browser Mod's authenticated WebSocket settings command.
- Confirm the stored user-level settings exist only under Nic's user ID.
- Confirm Ethan has no user-level kiosk settings.
- Authenticate a WebSocket session as Nic and verify Browser Mod returns the expected effective settings.
- Confirm Home Assistant and the Frigate dashboard remain healthy.
- Have Nic refresh or sign in again and verify the dashboard opens without a sidebar or header.
