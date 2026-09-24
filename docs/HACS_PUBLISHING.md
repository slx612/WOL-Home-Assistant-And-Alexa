# WakeLink release and HACS checklist (maintainers)

For user installation instructions, use [English](GETTING_STARTED.en.md) or [Espanol](GETTING_STARTED.es.md). This file is for maintainers, not another setup route.

WakeLink is already on the HACS default list ([accepted submission #7156](https://github.com/hacs/default/pull/7156)); do not submit it again for each beta. HACS reads `custom_components/pc_power_free`, `hacs.json` and the GitHub release. Keep the visible name WakeLink but retain `pc_power_free` as the integration domain and discovery type to preserve pairings.

## Before a prerelease

1. Bump the integration manifest, Windows app, installer and Windows executable version resources together when both platforms change. If only one platform changes, state that explicitly in release notes.
2. Run unit tests, package checks, HACS validation and hassfest. Review actual Windows installer and integration ZIP contents.
3. Test installation over an existing WakeLink installation without uninstalling. Confirm the Home Assistant entry, token, certificate and PC identity survive. Upload both the user-facing `WakeLink-Windows-x64-Setup.exe` and identical legacy `pcpowerfree-windows-x64-setup.exe`; installed updaters still require the latter.
4. Build release assets and `SHA256SUMS.txt`. Do not imply the unsigned installer has a publisher signature; a checksum only detects a different file.
5. Create a **GitHub prerelease** with notes and uploaded assets, not just a tag. Check that direct Windows and integration download links work and that the Windows update checker finds the uploaded installer.
6. Keep Alexa labelled experimental until pairing and both power directions have been tested on a compatible Echo. Matterbridge and `matterbridge-hass` are external dependencies; do not claim they are bundled with WakeLink.

Current user guides must not hardcode a beta number. Version-specific validation and old releases are listed in the [documentation index](README.md) as historical records.
