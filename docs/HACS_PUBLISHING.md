# HACS publishing checklist

Use this checklist to keep the repository aligned with the current HACS situation and with the active prerelease.

## Current status

- Latest GitHub prerelease already published: `v0.2.0-beta.6`
- Release assets already attached for `v0.2.0-beta.6`
- HACS default submission already open: `hacs/default#7156`
- Repository code and release assets are now aligned with `v0.2.0-beta.6`

## 1. Repository metadata on GitHub

Configure the repository `About` section on GitHub:

- Add a short description
- Add topics
- Keep issues enabled

Suggested topics:

- `home-assistant`
- `hacs`
- `custom-integration`
- `wake-on-lan`
- `windows`
- `linux`
- `alexa`

## 2. Validation workflows

Before publishing a new prerelease:

- `HACS validation` must pass with no ignored checks
- `hassfest` must pass

## 3. Release

For each new prerelease:

1. Create a full GitHub prerelease
2. Do not publish only a tag
3. Attach release notes
4. Attach the current release assets

Current published assets for `v0.2.0-beta.6`:

- `pcpowerfree-windows-x64-setup.exe`
- `PCPowerAgent.exe`
- `PCPowerTray.exe`
- `PCPowerSetup.exe`
- `pcpowerfree-home-assistant-integration.zip`
- `pcpowerfree-linux-agent.tar.gz`
- `pcpowerfree-dsm-noarch-0.2.0-0006.spk`

Suggested release path from this point:

- Keep using prereleases until `Alexa + Home Assistant` has been validated on a real setup
- Keep Linux marked as experimental until it has packaging beyond the source bundle
- Keep DSM marked as experimental until shutdown, restart, and wake have been validated on real hardware

## 4. HACS default repository submission

The submission step itself is already done:

1. The repository was already added in a PR to `hacs/default`
2. The PR is already open as `#7156`
3. The remaining step is HACS maintainer review and merge

Important:

- Default-list review can take a long time
- The project can already be installed before that as a normal HACS custom repository

## 5. Recommended validation status

Already validated on real setups:

- Home Assistant discovery
- Pairing code flow
- Windows path with Home Assistant
- Linux path with Home Assistant
- Linux power-off from Home Assistant
- DSM 7 package install, service start, discovery, and pairing

Still pending:

- Real Wake-on-LAN boot validation on Linux hardware if that path is going to be advertised broadly
- Real restart validation on Linux hardware
- Real Alexa test through Home Assistant
- DSM shutdown, restart, and wake validation
