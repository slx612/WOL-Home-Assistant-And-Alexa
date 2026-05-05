# PC Power Free v0.2.0-beta.5

Fifth public beta release.

## Highlights

- Experimental Linux agent runtime added with the same LAN discovery and pairing protocol as the Windows build
- Home Assistant integration updated to understand `platform` and `capabilities`
- Default local agent port moved to `58477`
- Windows desktop flow keeps tray protection, update checks, and the simplified installer

## Included

- Home Assistant custom integration
- Shared cross-platform runtime core
- Windows installer and standalone Windows binaries
- Experimental Linux source bundle
- Automatic LAN discovery with `zeroconf`
- Pairing with a temporary code
- Wake-on-LAN power on
- Local shutdown and restart

## Assets to attach

- `pcpowerfree-windows-x64-setup.exe`
- `PCPowerAgent.exe`
- `PCPowerTray.exe`
- `PCPowerSetup.exe`
- `pcpowerfree-home-assistant-integration.zip`
- `pcpowerfree-linux-agent.tar.gz`

## Known status

- Windows path validated on a real Home Assistant installation
- Linux path validated on a real Ubuntu machine for discovery, pairing, and power off
- Alexa through Home Assistant is still pending real-world validation
- DSM packaging is not part of this beta yet

## Notes

Use this release as a prerelease or beta.
The Linux runtime is intentionally shipped as an experimental source bundle for now, not as a packaged installer.
