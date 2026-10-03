# WakeLink

![WakeLink logo](https://raw.githubusercontent.com/slx612/WOL-Home-Assistant-And-Alexa/main/custom_components/pc_power_free/brand/logo.png)

[English](README.md) | [Español](docs/README.es.md)

Turn your computer or NAS on, shut it down or restart it from Home Assistant, without a WakeLink subscription. Install the WakeLink app on that device and its integration in Home Assistant. Pair them once with a temporary code.

**Home Assistant is required and must stay running on another device when the controlled computer/NAS is off.** Alexa is optional and needs the separate Matterbridge app; an Echo and a powered-off PC alone are not enough.

## Start here

Choose **one** guide for your device. Each includes Home Assistant setup, pairing, a safe first test and updates. You do not need the other systems' guides.

| Your device | Follow this guide | File to install |
| --- | --- | --- |
| Windows x64 PC | [Windows + Home Assistant](docs/GETTING_STARTED.en.md) | `WakeLink-Windows-x64-Setup.exe` |
| Ubuntu 24.04 Desktop PC | [Ubuntu + Home Assistant](docs/INSTALL_UBUNTU.en.md) | `WakeLink-Ubuntu-<version>.deb` |
| Synology NAS, DSM 7 | [DSM + Home Assistant](docs/INSTALL_DSM.en.md) | `pcpowerfree-dsm-noarch-<version>.spk` |

<a id="download"></a>

**Downloads:** open [beta.13](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.13), expand **Assets**, and choose your system's file. This release includes Windows, Ubuntu Desktop and DSM installers, plus the Home Assistant ZIP. Older DSM packages lack the current assistant. Follow the system guide below; updates keep existing pairing.

In HACS, search for `WakeLink`. Install the integration **once**, then pair each device separately. Do not download the individual Windows executables or GitHub's **Source code** archives for normal installation.

[![Open WakeLink in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=slx612&repository=WOL-Home-Assistant-And-Alexa&category=integration)

**HACS already installed and configured?** Click the button, check the Home Assistant address and select **Open link**, then **Download** in HACS. If asked for your instance URL, enter the address you normally use to open Home Assistant. Sign in to your Home Assistant if requested. Restart Home Assistant afterwards and continue with your system's pairing guide. The button opens the repository; it does not install HACS or pair a device automatically.

## After installation

| You want to... | Go here |
| --- | --- |
| Connect the paired device to Alexa | [Alexa: illustrated guide](docs/ALEXA.en.md) |
| Fix discovery, power, updates or SmartScreen problems | [Help and updates](docs/HELP.en.md) |
| Understand the missing HACS list icon | [Known HACS issue](docs/KNOWN_ISSUES.md#english) |
| Change language or find another guide | [Documentation](docs/README.md) |

**Updating? Install over the existing app/package, update WakeLink in HACS, and restart Home Assistant. Do not uninstall, delete the device or pair it again just to update.** Old internal IDs, data directories and compatibility filenames preserve existing connections; the visible name is WakeLink.

## What to expect

- **Wake:** Home Assistant sends Wake-on-LAN. Your hardware, firmware and network must support it. Pairing is not proof that wake works. WakeLink cannot start a stopped VM through its hypervisor.
- **Shutdown/restart:** the running agent receives an authenticated local request. Save your work first. DSM needs the one-time permission in its guide.
- **Alexa:** Home Assistant -> Matterbridge + `matterbridge-hass` -> Matter-compatible Echo/Alexa. Discovery has been reported working; a complete shutdown-and-wake test on a real Echo is still pending. Matterbridge needs a broad Home Assistant access token and must stay running. No third-party subscription is required, but Alexa voice services may need internet access.
- **Beta:** Ubuntu's desktop upgrade was checked on a VM; a fresh desktop installation remains pending. DSM's fresh installation and controls have been reported working on the DSM 7.2 test VM; other DSM versions, physical NAS wake and downgrade remain unvalidated.

No fixed computer IP is normally needed. Use a trusted LAN and never expose the agent port to the internet. Windows may warn about the unsigned installer: [check it safely](docs/HELP.en.md#windows-smartscreen), without disabling protection.

## Development

User installation ends at the guides above. For source/build work: [Windows](windows_agent), [Linux and manual servers](linux_agent/README.md), [DSM packaging](dsm_package/README.md), and [release/HACS checklist](docs/HACS_PUBLISHING.md). Install test dependencies from `tests/requirements.txt`, then run `python -m unittest discover -s tests -q`. [Historical notes](docs/HISTORY.md) are not setup instructions.

Report problems in [GitHub Issues](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/issues). Include system, installed versions, failing step and a redacted error; never include passwords, tokens or pairing codes.
