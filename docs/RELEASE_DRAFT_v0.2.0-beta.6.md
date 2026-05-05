# PC Power Free v0.2.0-beta.6

Sixth public beta release.

## Highlights

- DSM package scaffold now validated on real DSM 7.2 hardware for install, service start, discovery, and pairing
- Home Assistant can now repair an existing entry during re-pairing and refresh platform metadata correctly
- Home Assistant rediscovery no longer probes the local subnet with the stored API token
- Pairing now blocks the temporary code after repeated failed attempts

## Included

- Home Assistant custom integration
- Shared cross-platform runtime core
- Windows installer and standalone Windows binaries
- Experimental Linux source bundle
- Experimental DSM `.spk` package
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
- `pcpowerfree-dsm-noarch-0.2.0-0006.spk`

## Known status

- Windows path validated on a real Home Assistant installation
- Linux path validated on a real Ubuntu machine for discovery, pairing, and power off
- DSM package validated on a real DSM 7.2 NAS for install, service start, discovery, and pairing
- Alexa through Home Assistant is still pending real-world validation
- DSM shutdown, restart, and wake are still pending real-world validation

## Notes

Use this release as a prerelease or beta.
The Linux runtime and the DSM package should still be presented as experimental distribution paths.
