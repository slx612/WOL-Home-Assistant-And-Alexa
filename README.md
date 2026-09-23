# WakeLink

[English](README.md) | [Espanol](docs/README.es.md)

Local, subscription-free power control for Windows PCs and Linux hosts through Home Assistant. WakeLink is the visible name of the Windows app and Home Assistant integration. Existing `PC Power Free` installation paths and the `pc_power_free` integration ID stay unchanged so updates keep paired devices.

## Download

**[Download for Windows x64: beta.10 installer](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/download/v0.2.0-beta.10/pcpowerfree-windows-x64-setup.exe)**

Use one Windows installer, not the individual executables. It installs the WakeLink dashboard, agent and tray app together.

**Home Assistant is separate:** install or update WakeLink through [HACS](#hacs). The Matter guide is in the beta.11 Home Assistant preview; Windows remains beta.10. [Installation and rollback instructions](docs/MATTER-PREVIEW-beta.11.md#english). Other platforms and the beta.10 manual integration ZIP are on the [beta.10 release page](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.10).

### Beta.10 update

`0.2.0-beta.10` is a public **prerelease**. It includes the WakeLink dashboard, the beta.8 certificate-access and desktop-shortcut fixes, and left-click-to-open behavior for the tray icon. Right-click still shows the menu. The update checker offers the direct installer download.

Upgrading from beta.5 through beta.9 uses the existing installation: **do not uninstall, reset credentials or pair again**. Keep the port, token, machine ID and existing TLS certificate/key. See the [beta.10 instructions](docs/WINDOWS-beta.10.md).

Manual Windows installation and hardware power cycles are still required to validate beta.10. Beta.11 only changes the Home Assistant integration and does not claim Alexa control is validated.

## What this is

This project covers the full local flow:

- Install a local agent on Windows or Linux
- Let Home Assistant discover the device automatically
- Pair it with a temporary code
- Wake supported hardware with Wake-on-LAN
- Shut it down or restart it over the local network
- Expose it to Alexa through Home Assistant without paying for a third-party subscription

Home Assistant control is local and needs no subscription or open internet ports. Alexa voice recognition can still require Amazon connectivity.

## Included

- A Home Assistant custom integration in [`custom_components/pc_power_free`](custom_components/pc_power_free)
- A shared cross-platform runtime core in [`agent_core`](agent_core)
- A Windows agent in [`windows_agent`](windows_agent)
- An experimental Linux agent in [`linux_agent`](linux_agent)
- A single Windows installer, linked above
- A Home Assistant integration ZIP on the public release page, as an alternative to HACS
- An experimental Linux source bundle published as a GitHub release asset: `pcpowerfree-linux-agent.tar.gz`

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
- Alexa is optional; its route through Home Assistant remains experimental

## Windows installation

The download above installs beta.10. The following dashboard flow requires Windows x64.

### First-time configuration (beta.10)

1. Run the beta.10 Windows installer once, select English or Spanish and choose whether to create a desktop shortcut. It is off by default. Windows asks for administrator permission for installation.
2. Leave **Open WakeLink** selected on Finish, then choose **Enable and continue**. WakeLink detects the local network, creates the local firewall rule and enables automatic startup. This configures the installed app; it is not a second installation.
3. Pair with the separately installed Home Assistant integration on a trusted LAN. Compare the certificate fingerprint shown in WakeLink, then enter the temporary code within ten minutes. The dashboard shows local-agent status; this alone does not prove Wake-on-LAN or Alexa works.

### Upgrade from beta.5 through beta.9

**Do not uninstall.** Back up the existing data folder, close the dashboard and run the beta.10 installer over the same installation. Keep the existing installation and data locations, normally `C:\Program Files\PC Power Free` and `C:\ProgramData\PC Power Free`.

The finish page reports that settings and pairing were preserved. Its checked launch option opens the tray **and** dashboard, not onboarding; no new code or second setup is required. The port, token, machine ID, existing TLS certificate/key, guard and startup choices are retained. An older installation without TLS files creates them during migration; existing certificates must not be replaced. Disabled automatic startup stays disabled. No Windows restart is requested by the installer.

Read the [beta.10 manual instructions](docs/WINDOWS-beta.10.md) before testing. If Home Assistant is still on beta.5/6, follow the separate [beta.7 integration upgrade guide](docs/UPGRADE-beta.7.md) for HTTPS compatibility; do not remove the existing device entry.

The dashboard supports English and Spanish. First-time launch follows the installer language; upgrades do not override a saved app language. The optional desktop shortcut is called `WakeLink`; old desktop links to this installation are removed. `PCPowerSetup.exe` is the dashboard's legacy filename, not another installer. Agent and tray startup roles are unchanged; opening the dashboard later should not request administrator permission just to view it.

### SmartScreen and updates

The preview is unsigned. SmartScreen may show an unrecognized-app or unknown-publisher warning. Verify the source and supplied SHA-256 checksum before deciding whether to proceed; a matching checksum is not a publisher signature. Do not disable antivirus, SmartScreen or organizational policy. Free code signing for the open-source project is pending, and signing would not guarantee that all warnings disappear. See [Microsoft's SmartScreen explanation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

Update checks need Internet access; local dashboard use does not depend on GitHub. An offline check must not be reported as "up to date". The tray asks before opening the installer download; it never runs the installer automatically.

### Advanced: standalone executables

`PCPowerAgent.exe`, `PCPowerTray.exe` and `PCPowerSetup.exe` are for development or advanced troubleshooting only. The installer includes all three; normal installation and upgrades do not require downloading or launching them separately.

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
sudo /opt/pc-power-free/.venv/bin/python -m pip install ifaddr zeroconf cryptography
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
curl --cacert /etc/pc-power-free/agent-cert.pem https://127.0.0.1:58477/v1/discovery
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
4. Add `WakeLink`

### HACS

The repository is prepared for HACS with [`hacs.json`](hacs.json).

1. In HACS, search for `WakeLink` in the integrations list.
2. Install the latest Home Assistant prerelease (beta.11 for the Matter guide). If updating an older beta, keep the existing device and pairing; the [beta.7 upgrade guide](docs/UPGRADE-beta.7.md) explains the HTTPS migration from beta.5/6.
3. Restart Home Assistant. Existing installations keep their pairing.

If the integration tile still shows the generic placeholder icon, your Home Assistant version is likely older than `2026.3`, which is the first release that supports bundled `brand/` assets for custom integrations.

The repository is already included in the default HACS list; [submission #7156 was merged](https://github.com/hacs/default/pull/7156). Adding a custom repository is only an alternative, not a prerequisite.

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
2. `WakeLink`
3. `Set up by IP manually`
4. Enter the current host IP and agent port
5. Enter the pairing code

If the code expires:

- on Windows, open WakeLink and generate a new code on its Home Assistant page for first-time pairing, not a routine upgrade
- on Linux, rerun `linux_agent/setup_cli.py`

## Alexa

The experimental beta.11 route is `Alexa + Matterbridge + Home Assistant`. Open **Configure > Connect with Alexa (Matter preview)** on an existing WakeLink PC. This guide does not install Matterbridge automatically; see [the detailed setup and rollback guide](docs/MATTER-PREVIEW-beta.11.md#english). Do not expose other Home Assistant entities unintentionally. Alexa control is not yet validated end-to-end.

The earlier `emulated_hue` route remains an experimental manual fallback. Do not expose the same PC through both bridges at once.

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
.\windows_agent\build-exe.ps1 -Clean
```

### Windows installer

```powershell
.\windows_agent\build-installer.ps1
```

### Release assets

```powershell
.\build-release-assets.ps1
```

## Security

- Do not expose port `58477` to the internet
- Restrict access to the Home Assistant IP or at least your LAN
- Use a VPN if you need remote access
- The pairing code is temporary

## Publishing state

Current `default HACS repository` status:

- Included in HACS default following [merged submission #7156](https://github.com/hacs/default/pull/7156).
- Windows installer: `v0.2.0-beta.10`. Home Assistant Matter guide preview: `v0.2.0-beta.11`. The [Windows manual checks](docs/WINDOWS-beta.10.md) remain pending.

Still pending before calling it truly final:

- Real beta.10 installation/upgrade, HA/Alexa and hardware power-cycle tests.
- DSM power-action privilege model
