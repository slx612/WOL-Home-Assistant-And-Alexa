# Install WakeLink on Ubuntu

[English](INSTALL_UBUNTU.en.md) | [Español](INSTALL_UBUNTU.es.md) | [Choose another system](../README.md#start-here)

This guide is for **Ubuntu 24.04 Desktop**, with a graphical desktop. For a headless server, see the [manual installation](../linux_agent/README.md#manual-installation-for-servers). The computer and Home Assistant must be on the same trusted local network. Home Assistant must stay running on another device when this PC is off. You need HACS in Home Assistant. Set up Alexa afterwards.

**Status:** the `.deb` is a local test build, not published in GitHub Releases yet. An upgrade over a manual installation has been tested on the Ubuntu VM; a complete fresh installation is still untested. Pairing alone does not prove that the hardware supports Wake-on-LAN.

## 1. Choose the right file

The current local test file is **`WakeLink-Ubuntu-0.2.0-beta.12.deb`**. Future installers use `WakeLink-Ubuntu-<version>.deb`. Use the `.deb` supplied for the test, not the older Linux source bundle in public Releases. Do not use a Windows `.exe` or a DSM `.spk`. If you do not have the `.deb`, this route is not available as a normal download yet; you do not need to build it yourself once a test installer is supplied.

Back up Home Assistant before testing a beta. The computer needs Internet access during installation to download Ubuntu dependencies.

## 2. Install and open the app

1. Open **Files** and find the `.deb`.
2. Open it with a package installer and select **Install**. Enter your password when Ubuntu requests authorization. If you have no application that installs this file, use the terminal alternative below.
3. Open Ubuntu's applications menu and find **WakeLink**.
4. In WakeLink, choose **EN** for English or **ES** for Spanish.
5. Select **Enable WakeLink** and approve Ubuntu's request. This configures the service; it does not shut down the computer.
6. Wait for **Agent running**. The service starts with Ubuntu; do not add the window to your startup applications, and you do not need to leave it open.

If the file does not open with a package installer, open a terminal **in the folder containing the `.deb`** and run this command, replacing `FILE_NAME.deb` with its actual name:

```sh
sudo apt install ./FILE_NAME.deb
```

## 3. Pair with Home Assistant

[![Open WakeLink in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=slx612&repository=WOL-Home-Assistant-And-Alexa&category=integration)

HACS must already be installed and configured. The button opens WakeLink's card, not an automatic installation. Check the Home Assistant address before selecting **Open link**. If asked for your instance URL, enter the address you normally use to open Home Assistant, such as `http://homeassistant.local:8123`. Sign in to your Home Assistant if requested.

1. Use the button above, or in Home Assistant open **HACS**, search for `WakeLink`, open its card and select **Download**. Choose the release you want to test; enable HACS's beta-version option if needed. Restart Home Assistant when prompted. If search finds nothing, use **... > Custom repositories**, enter `https://github.com/slx612/WOL-Home-Assistant-And-Alexa`, choose **Integration**, select **Add**, then search again. Install this integration only once, even for several devices.
2. In WakeLink, use the six-digit code shown after enabling the agent. If it is missing or expired, select **Generate pairing code** and approve Ubuntu's request.
3. In Home Assistant, open **Settings > Devices & services** and select the discovered computer. If it is missing, select **Add integration > WakeLink**. Check that you selected your computer, not another device on the network.
4. Enter the code within ten minutes. If discovery is unavailable and the form asks for an IP, use the computer's address and port `58477`, unless you changed it.
5. Check that the computer appears under WakeLink with **Power**, **Restart**, **Boot time** and **Uptime**. **Do not turn it off just to check its state.**

**Checkpoint:** your computer is listed in Home Assistant. The pairing screen shows its TLS fingerprint; check the intended device name/IP and pair only on the trusted network. This preview's Ubuntu window does not yet show a fingerprint for side-by-side comparison.

The code pairs Home Assistant; it is not your Ubuntu password. Updates do not need a new code. A fixed IP is normally unnecessary, but guest networks and VLANs may block discovery.

## 4. Test shutdown and wake

1. Save your work and stop tasks you do not want to interrupt.
2. When you want a real shutdown, turn the computer's switch off in Home Assistant.
3. Afterwards, turn that switch on to test Wake-on-LAN.

Use **Restart** only for a real restart. Sensors may be unavailable during startup and recover on a later poll (30 seconds by default). **Boot time** is the last system boot date/time; **Uptime** is time since that boot.

If shutdown works but wake does not, check firmware and network adapter Wake-on-LAN settings, preferably using Ethernet. WakeLink does not automatically configure firmware or persistent Ubuntu network-adapter wake settings. A VM is not equivalent to a physical PC: WakeLink does not start virtual machines through their hypervisor.

## 5. Updates and troubleshooting

Install the newer `.deb` **over** the existing one. Do not uninstall or delete the Home Assistant device. Configuration, certificates and pairing remain in `/etc/pc-power-free/`. This old internal name does not refer to another application.

| What you see | What to do |
| --- | --- |
| No code | Select **Generate pairing code**, approve Ubuntu's request, and return to Home Assistant. |
| Agent does not start | Check the installer's result and whether you approved **Enable WakeLink**. Do not delete configuration. |
| Home Assistant finds no computer | Check that the agent is running and both devices share a network; use the manual IP option if needed. |
| Ubuntu authorization error | Use a desktop session that can display an administrator prompt. For a headless server, use the manual guide. |

Keep the older `.deb` and a protected backup of `/etc/pc-power-free/` if you need to go back. Never publish this directory: it contains credentials. Restoring an older version still needs testing before rollback can be considered guaranteed.

For HACS updates, backups, rollback and network errors, use [Help and updates](HELP.en.md). A missing HACS list icon is a [known display issue](KNOWN_ISSUES.md#english), not a failed installation.

Once this works, follow the [Alexa guide](ALEXA.en.md). Matterbridge is not required for Home Assistant computer control.
