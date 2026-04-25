# PC Power Free

![PC Power Free](custom_components/pc_power_free/brand/logo.png)

Language:

- [English](README.md)
- [Espanol](docs/README.es.md)

Local, subscription-free power control for Windows PCs and Linux hosts through Home Assistant and Alexa.

Current status: `0.2.0-beta.5 prepared in the repository, Windows and Linux Home Assistant paths validated on real setups, Alexa path still pending real-world validation`.

Publication status:

- Repository code currently targets `v0.2.0-beta.5`
- Latest GitHub prerelease published: `v0.2.0-beta.4` on April 21, 2026
- Next planned GitHub prerelease: `v0.2.0-beta.5`
- HACS default submission is already open in `hacs/default#7156`
- Supported distribution paths: manual install, HACS custom repository, GitHub prerelease downloads, Windows installer, experimental Linux source install
- The only remaining real-world validation still pending is `Alexa + Home Assistant`

Recent additions:

- Experimental Linux agent runtime with the same discovery and pairing protocol as Windows
- Home Assistant flow now validated against both Windows and Linux hosts
- Default local agent port moved to `58477`
- Windows tray protection and update checks remain part of the current desktop build

## What this is

This project covers the full local flow:

- Install a local agent on Windows or Linux
- Let Home Assistant discover the device automatically
- Pair it with a temporary code
- Wake supported hardware with Wake-on-LAN
- Shut it down or restart it over the local network
- Expose it to Alexa through Home Assistant without paying for a third-party subscription

No cloud dependency. No open internet ports required.

## Included

- A Home Assistant custom integration in [`custom_components/pc_power_free`](custom_components/pc_power_free)
- A shared cross-platform runtime core in [`agent_core`](agent_core)
- A Windows agent in [`windows_agent`](windows_agent)
- An experimental Linux agent in [`linux_agent`](linux_agent)
- A full Windows installer in [`windows_agent/dist/pcpowerfree-windows-x64-setup.exe`](windows_agent/dist/pcpowerfree-windows-x64-setup.exe)
- A packaged Home Assistant integration zip in [`release_assets/pcpowerfree-home-assistant-integration.zip`](release_assets/pcpowerfree-home-assistant-integration.zip)
- An experimental Linux source bundle published as a GitHub release asset: `pcpowerfree-linux-agent.tar.gz`
- Standalone Windows binaries:
  - [`windows_agent/dist/PCPowerAgent.exe`](windows_agent/dist/PCPowerAgent.exe)
  - [`windows_agent/dist/PCPowerTray.exe`](windows_agent/dist/PCPowerTray.exe)
  - [`windows_agent/dist/PCPowerSetup.exe`](windows_agent/dist/PCPowerSetup.exe)

## How it works

### Power on

1. Home Assistant sends a Wake-on-LAN magic packet.
2. The device powers on if BIOS or UEFI and the operating system are configured correctly.

### Shutdown and restart

1. Home Assistant calls the local Windows or Linux agent.
2. The agent validates the source network and internal token.
3. The agent runs the local shutdown or restart command.

### Discovery and pairing

1. The local agent advertises the device over `zeroconf` on the LAN.
2. Home Assistant discovers it automatically.
3. The user enters a temporary 6-digit pairing code shown by the local setup tool.
4. Home Assistant exchanges that code for the internal token and stores the configuration.

## Requirements

- Home Assistant on the same local network
- A Windows PC or Linux host
- Wake-on-LAN support if you want power-on from a full shutdown
- Home Assistant `2026.3` or newer if you want the bundled integration logo from `custom_components/.../brand/`
- Alexa is optional and works through Home Assistant

## Windows installation

Recommended path:

1. Run [`windows_agent/dist/pcpowerfree-windows-x64-setup.exe`](windows_agent/dist/pcpowerfree-windows-x64-setup.exe)
2. Complete the installer
3. Review the detected settings
4. Leave these enabled:
   - `Create firewall rule`
   - `Install at startup`
5. Click `Install`
6. Confirm the tray app is enabled at startup
7. Use the tray icon to temporarily or permanently ignore Home Assistant power requests when needed
8. Keep the pairing code visible or copied somewhere because Home Assistant will ask for it next
9. Pair the device in Home Assistant within 10 minutes, or generate a new code later from the Windows configurator

The setup program auto-detects:

- Computer name
- Active network adapter
- Current IP
- Primary MAC
- Wake-on-LAN broadcast
- Discovery subnet

The setup UI supports `English` and `Spanish`.
It also includes a `Check for updates` action against GitHub releases.
The tray app also checks for updates automatically after Windows starts and can offer to open the latest release page.

## Linux installation

Current Linux packaging is still `experimental` and source-based, but the Home Assistant path has already been validated on a real Ubuntu machine.

Recommended path:

1. Download the Linux source bundle `pcpowerfree-linux-agent.tar.gz` from the latest GitHub prerelease, or copy `agent_core` and `linux_agent` from this repository
2. Extract it under `/opt/pc-power-free`
3. Create a Python virtual environment there
4. Install runtime dependencies: `ifaddr` and `zeroconf`
5. Run the Linux setup CLI and let it generate `/etc/pc-power-free/config.json`
6. Install `linux_agent/pcpowerfree-agent.service` as a `systemd` unit
7. Start and enable the service
8. Pair the device in Home Assistant with the temporary code shown by the CLI

Ubuntu or Debian example:

```bash
sudo mkdir -p /opt/pc-power-free /etc/pc-power-free
sudo tar -xzf pcpowerfree-linux-agent.tar.gz -C /opt/pc-power-free
sudo python3 -m venv /opt/pc-power-free/.venv
sudo /opt/pc-power-free/.venv/bin/python -m pip install --upgrade pip ifaddr zeroconf
sudo /opt/pc-power-free/.venv/bin/python /opt/pc-power-free/linux_agent/setup_cli.py --config /etc/pc-power-free/config.json
sudo cp /opt/pc-power-free/linux_agent/pcpowerfree-agent.service /etc/systemd/system/pcpowerfree-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now pcpowerfree-agent.service
sudo systemctl status pcpowerfree-agent.service --no-pager
```

After the service starts:

- open Home Assistant and add `PC Power Free`
- wait for the Linux host to appear automatically, or add it by IP
- enter the temporary pairing code shown by `setup_cli.py`

Useful Linux-side checks:

```bash
curl http://127.0.0.1:58477/v1/discovery
sudo journalctl -u pcpowerfree-agent.service -n 50 --no-pager
```

Notes:

- the default local port is `58477`
- rerun `linux_agent/setup_cli.py` whenever you need a fresh pairing code
- if you use `ufw`, allow `58477/tcp`
- the example service file expects the runtime under `/opt/pc-power-free`

## Home Assistant installation

### Manual

1. Copy `custom_components/pc_power_free` into `/config/custom_components/`
2. Restart Home Assistant
3. Go to `Settings > Devices & services`
4. Add `PC Power Free`

### HACS

The repository is prepared for HACS with [`hacs.json`](hacs.json).

1. In HACS, open `Custom repositories`
2. Add the URL of this repository
3. Type: `Integration`
4. Install `PC Power Free`
5. Restart Home Assistant
6. Enable beta or prerelease updates for this repository if you want release notifications for the current prerelease line

If the integration tile still shows the generic placeholder icon, your Home Assistant version is likely older than `2026.3`, which is the first release that supports bundled `brand/` assets for custom integrations.

For the `default HACS list`, the submission is already in progress:

1. A GitHub prerelease already exists, and the repository is now prepared for `v0.2.0-beta.5`
2. The submission PR is already open in `hacs/default#7156`
3. The remaining step is maintainer review and merge on the HACS side

Checklist: [`docs/HACS_PUBLISHING.md`](docs/HACS_PUBLISHING.md)

## Pairing with Home Assistant

### Recommended flow

1. Install the local agent first on Windows or Linux
2. Finish the local setup and keep the temporary pairing code visible
3. Install or open the Home Assistant integration flow
4. Wait for the device to appear automatically
5. Select the discovered device
6. Enter the temporary pairing code while it is still active
7. Confirm the device name

### If automatic discovery fails

There is also a manual IP flow:

1. `Add integration`
2. `PC Power Free`
3. `Set up by IP manually`
4. Enter the current host IP and agent port
5. Enter the pairing code

If the code expires:

- on Windows, open the configurator and generate a new one
- on Linux, rerun `linux_agent/setup_cli.py`

## Alexa

The supported design path is `Alexa + Home Assistant`.
It is not yet validated end-to-end on a real installation, so treat the Alexa route as `experimental` until that test is complete.

The simplest local route is `emulated_hue`.

Example:

```yaml
emulated_hue:
  listen_port: 80
  entities:
    switch.pc_despacho_power:
      name: "Office PC"
      hidden: false
```

## Repository structure

```text
agent_core/
custom_components/pc_power_free/
linux_agent/
windows_agent/
release_assets/
hacs.json
README.md
docs/README.es.md
LICENSE
```

## Main files

- [`agent_core/common.py`](agent_core/common.py)
- [`custom_components/pc_power_free/config_flow.py`](custom_components/pc_power_free/config_flow.py)
- [`custom_components/pc_power_free/api.py`](custom_components/pc_power_free/api.py)
- [`linux_agent/pc_power_agent.py`](linux_agent/pc_power_agent.py)
- [`linux_agent/setup_cli.py`](linux_agent/setup_cli.py)
- [`windows_agent/pc_power_agent.py`](windows_agent/pc_power_agent.py)
- [`windows_agent/setup_wizard_gui.py`](windows_agent/setup_wizard_gui.py)
- [`windows_agent/build-exe.ps1`](windows_agent/build-exe.ps1)
- [`windows_agent/build-installer.ps1`](windows_agent/build-installer.ps1)
- [`build-release-assets.ps1`](build-release-assets.ps1)

## Build again

### Windows executables

```powershell
.\\windows_agent\\build-exe.ps1 -Clean
```

### Windows installer

```powershell
.\\windows_agent\\build-installer.ps1
```

### Release assets

```powershell
.\\build-release-assets.ps1
```

## Security

- Do not expose port `58477` to the internet
- Restrict access to the Home Assistant IP or at least your LAN
- Use a VPN if you need remote access
- The pairing code is temporary

## Publishing state

Current `default HACS repository` status:

- submission PR already open: `hacs/default#7156`
- latest prerelease already published: `v0.2.0-beta.4`
- next planned prerelease: `v0.2.0-beta.5`
- waiting for HACS maintainer review

Still pending before calling it truly final:

- real Alexa test through `emulated_hue`
- DSM package and privilege model
