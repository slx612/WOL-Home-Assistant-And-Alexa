# WakeLink

[English](README.md) | [Espanol](docs/README.es.md)

Turn a PC on and off from Home Assistant, without a subscription. WakeLink installs a small app on the PC and a separate Home Assistant integration. Alexa is an **optional experimental route** through Matterbridge, not a built-in WakeLink feature.

## Start here

1. [Install WakeLink on Windows and pair it with Home Assistant](docs/GETTING_STARTED.en.md).
2. If you also want voice control, [connect the paired PC to Alexa](docs/ALEXA.en.md).

Download **`WakeLink-Windows-x64-Setup.exe`** from the latest beta on [GitHub Releases](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases). **Do not download the three individual `.exe` files** for normal installation. The old `pcpowerfree-windows-x64-setup.exe` is an identical compatibility copy for installed updaters. In HACS, search for `WakeLink` to install the Home Assistant side. No fixed PC IP is normally needed: WakeLink discovers the PC on the local network.

## What to expect

- **Turn on:** Home Assistant sends a Wake-on-LAN packet. Your PC and network hardware must support waking from shutdown; WakeLink cannot change BIOS/UEFI settings.
- **Shut down/restart:** Home Assistant contacts the local PC agent. Save your work before trying shutdown.
- **Alexa:** The route is Home Assistant -> Matterbridge + `matterbridge-hass` -> compatible Echo/Alexa. The separate Matterbridge app needs a broad Home Assistant access token. This is not one-click setup and has **not yet been validated end to end on an Echo**. No third-party subscription is needed, but Alexa voice services may require Amazon connectivity.
- **Privacy:** PC power requests stay on your LAN. Do not forward WakeLink's local agent port to the internet.

## Updates and compatibility

Install a newer Windows installer over the existing installation. In HACS, update WakeLink and restart Home Assistant. **Do not uninstall, delete the Home Assistant device, reset credentials or generate a new pairing code just to update.** The old `PC Power Free` program/data directories, `pc_power_free` integration ID and legacy installer filename are deliberately retained to preserve existing pairings. The visible name is WakeLink.

This remains a **beta**. Windows SmartScreen may warn about the unsigned installer; check the release source and SHA-256 checksum before deciding whether to run it. Do not disable SmartScreen or antivirus. The app can check GitHub for updates, but it does not execute an installer automatically.

For manual packages, Linux/DSM experiments, rollback and past beta notes, see the [documentation index](docs/README.md). Report problems in [GitHub Issues](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/issues).

## Development

The Home Assistant integration is in [`custom_components/pc_power_free`](custom_components/pc_power_free), the Windows app in [`windows_agent`](windows_agent), and the experimental Linux agent in [`linux_agent`](linux_agent). Run the test suite with `python -m unittest discover -s tests -q`. See [`docs/HACS_PUBLISHING.md`](docs/HACS_PUBLISHING.md) for maintainer release checks.
