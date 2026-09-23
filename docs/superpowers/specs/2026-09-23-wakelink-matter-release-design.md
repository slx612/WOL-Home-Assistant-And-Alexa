# WakeLink naming and guided Matterbridge release

Status: design for review; no implementation or release has been approved by this document.
Date: 2026-09-23.
Baseline: published v0.2.0-beta.10. The Windows updater was observed to find that version; a downloaded unsigned installer still triggers SmartScreen.

## User outcome

The next version presents one name, WakeLink, across the Windows installer and app, Home Assistant integration, HACS listing, documentation, release title and primary downloads. Existing users update in place without re-pairing a PC or recreating automations. The same version adds an English/Spanish guided Alexa setup through the upstream Matterbridge Home Assistant application and its `matterbridge-hass` plugin. Alexa support remains experimental until real Echo pairing and power tests pass. No paid skill, proprietary server or own Matter stack is added.

The user explicitly chose to keep the current GitHub repository address for now. It is a compatibility URL, not another product name.

## Stable identities versus public names

Do not rename the Home Assistant domain `pc_power_free`, its directory, entity unique IDs, config-entry IDs, stored PC machine IDs, API credentials, Zeroconf service type, Windows data/install directories, registry uninstall key, task identity, or internal executable names in this release. These are upgrade and pairing anchors, not public branding. Do not silently rewrite user-chosen entity names or Alexa routines. Show WakeLink in the HACS metadata, Home Assistant manifest/strings/translations, device manufacturer where appropriate, Windows Start menu, shortcuts, tray, installer, primary documentation and new release assets.

Remove old visible Start menu entries on upgrade only after creating working WakeLink replacements; keep legacy install/data paths. Explain an old filesystem path only in an upgrade/advanced note. Keep the repository URL and API endpoints unchanged. Audit every user-facing string in English and Spanish, including errors and onboarding. Do not treat source filenames as a branding defect if users do not encounter them.

Publish a primary Windows installer named for WakeLink, plus a byte-identical `pcpowerfree-windows-x64-setup.exe` alias in the next release. Beta.10's update checker requires that exact legacy asset name; removing it would strand existing installations. The next app may prefer the new asset, but must accept both as needed. Build/release verification must check both assets, their checksums and the beta.10-to-next-version update path. Retain the integration's `pc_power_free` folder inside a clearly named ZIP because Home Assistant requires the domain folder.

## Matterbridge architecture and flow

```text
Alexa app + compatible Echo -- Matter on LAN --> Matterbridge + matterbridge-hass
                                               |
                                       Home Assistant WakeLink switch
                                         /                 \
                               Wake-on-LAN packet     authenticated HTTPS
                                      to PC              to Windows agent
```

Home Assistant and Matterbridge must run on a separate, always-on host; this is not an Echo-plus-PC-only solution. Alexa voice recognition may still require Amazon connectivity. Matterbridge owns the Matter QR/setup code, controller pairing and persistent identity. The Windows app's six-digit code is only for pairing the PC with Home Assistant. No custom Alexa skill, AWS account or Thread radio is required for the LAN-based bridge.

In the Home Assistant integration options, offer a separate **Connect with Alexa** guide without replacing the existing device/network settings. Show the current integration's power switch for that paired PC, resolving its entity ID from the registry so user renames work. Explain prerequisites and link to installing/opening the official Matterbridge Home Assistant application and `matterbridge-hass` plugin. Guide the user to grant the plugin Home Assistant access using its own documented token flow. WakeLink must never read, store, display or log that token.

Guide restrictive export of *only* selected WakeLink power switches, not every HA entity or all entities of a PC device. The upstream plugin has area/label filters, white/black lists and split-entity settings; the exact safe combination must be confirmed against its current version and the actual preview before pairing. An empty selection must never mean expose all. Do not configure another application's internals using undocumented endpoints. The user scans Matterbridge's own QR code in the Alexa app and chooses the final device name there. A completed guide means instructions completed, not Alexa verified.

The existing manual `emulated_hue` route can remain documented as experimental fallback, but must not be the default or enabled concurrently for the same PC. No existing Alexa device or routine is migrated automatically.

## Failure and safety behavior

Normal Home Assistant control must keep working if Matterbridge or Alexa setup fails or is cancelled. The guide must not power-cycle the PC, open router ports, disable TLS validation, change shutdown protections or alter pairing. Removing a PC from Matterbridge export must not remove it from Home Assistant. Do not reset Matterbridge storage on update; preserving bridge identity is necessary for Alexa to retain pairing. Before first exposure, users verify that only intended switches appear, with a warning about the plugin's default broad export behavior.

The SmartScreen warning is separate from Matterbridge and naming. The current unsigned GitHub download can trigger it; a new version number, filename or self-signed certificate is not a fix. Investigate qualifying open-source signing or another trusted distribution path separately; do not promise a warning-free installer or instruct users to turn off Windows protections. The release notes should identify the warning plainly if still present.

## Verification and publication gate

- Automated checks cover preserved Windows config/data locations and task identity, unchanged HA domain and entity IDs, Windows/HACS/HA visible naming in EN/ES, both installer filenames and update discovery from beta.10, and cancellation/normal options behavior for the guide.
- Test the HA options flow against a real supported HA runtime, not only contract doubles. Check renamed, missing and disabled power entities; exclude foreign entities and non-power controls; verify no HA token leakage.
- On HAOS, record Matterbridge/plugin versions. Confirm preview contains only a selected PC switch, pair an actual compatible Echo, test voice on and off deliberately after saving work, test protection behavior, restart HA/bridge/Echo, then update the integration without re-pairing. Test at least one third-generation Echo or Echo Dot and a newer model before claiming that range validated.
- Do not claim Matter/Alexa support is hardware-validated or the SmartScreen warning is fixed until evidence exists. Release both the HACS integration and Windows installer together only after package checks and CI pass. Record completed live tests and any gaps explicitly; the next beta may be marked experimental if Echo testing is still pending.

## Sources

- [Matterbridge Home Assistant application](https://github.com/Luligu/matterbridge-home-assistant-addon/blob/main/DOCS.md)
- [Matterbridge Home Assistant plugin and export filters](https://github.com/Luligu/matterbridge-hass/blob/main/README.md)
- [Matterbridge filter defaults and selection](https://github.com/Luligu/matterbridge-hass/discussions/186)
- [Amazon Matter connection](https://developer.amazon.com/docs/alexaplus/smarthome/matter-support.html)
- [Amazon compatible Echo models](https://developer.amazon.com/en-US/alexa/matter)
- [Microsoft SmartScreen reputation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
