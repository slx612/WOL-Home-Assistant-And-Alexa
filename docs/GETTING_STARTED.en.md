# Install WakeLink: Windows + Home Assistant

[English](GETTING_STARTED.en.md) | [Español](GETTING_STARTED.es.md) | [Choose another system](../README.md#start-here)

**You need:** a Windows x64 PC, administrator permission to install, Home Assistant with HACS, and a trusted local network connecting both. Home Assistant must remain on another device when this PC is off. Make a Home Assistant backup before installing or updating. Alexa is optional and comes afterwards.

## 1. Download the installer

1. Open [WakeLink Releases](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases).
2. Choose the newest release **with a Windows installer**, expand **Assets** and download **`WakeLink-Windows-x64-Setup.exe`**.
3. Do not download `PCPowerAgent.exe`, `PCPowerTray.exe`, `PCPowerSetup.exe` or **Source code** separately. The old `pcpowerfree-windows-x64-setup.exe` is an identical compatibility copy, not another app.

If Windows shows an unknown-app warning, use the [SmartScreen checklist](HELP.en.md#windows-smartscreen) to verify the source and checksum before deciding to run it. The installer is unsigned; do not disable security protection.

## 2. Install and enable WakeLink

1. Run the installer and approve Windows's administrator prompt after checking the source.
2. Choose English or Spanish. Keep the suggested folders unless you already use a custom installation. You may leave the **desktop shortcut** unchecked.
3. Keep **Open WakeLink** selected on the final page.
4. For a new installation, select **Enable and continue** in WakeLink. If a new elevated window opens, approve Windows's prompt and repeat the action there when requested.
5. Wait for **Agent is running**. Opening the dashboard alone is not the same as enabling the agent.

WakeLink configures the background agent, local firewall access and Windows startup. You do not need to place it in Startup yourself or keep the dashboard open. Later, open WakeLink from Start or **left-click** its tray icon; **right-click** opens the tray menu. Change the app's language with its **Language** selector.

**Checkpoint:** the app can see its running agent. This does not test Alexa or hardware Wake-on-LAN.

<a id="2-install-the-home-assistant-integration"></a>

## 3. Install the Home Assistant integration

[![Open WakeLink in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=slx612&repository=WOL-Home-Assistant-And-Alexa&category=integration)

HACS must already be installed and configured. The button opens WakeLink's card, not an automatic installation. Check the Home Assistant address on the page before selecting **Open link**. If asked for your instance URL, enter the address you normally use to open Home Assistant, such as `http://homeassistant.local:8123`. Sign in to your Home Assistant if requested.

1. Use the button above, or open **HACS**, search for `WakeLink` and open it. It is in the default catalog. If your catalog does not show it, open **... > Custom repositories**, enter `https://github.com/slx612/WOL-Home-Assistant-And-Alexa`, choose **Integration**, and select **Add**. Search again.
2. Select **Download** and the latest stable release. You do not need to enable beta versions for v1.0.0.
3. Restart **Home Assistant**, not the PC, when prompted.
4. Open **Settings > Devices & services**. Do not add a second WakeLink installation if you already have one; one integration handles multiple devices.

The HACS list may show **icon not available**: this is a [known HACS display issue](KNOWN_ISSUES.md#english), not a failed installation. No YAML, manual API token or Windows executable belongs in HACS.

## 4. Pair this PC

1. Return to the Windows app and open **Home Assistant** in its left menu.
2. Select **Generate a code** if no active code is visible. Approve an administrator prompt if requested. It gives you six digits, valid for ten minutes.
3. In Home Assistant's **Settings > Devices & services**, select the discovered PC's **Add** button. If missing, select **Add integration > WakeLink**, then choose the PC; if no device is found, use the manual form with its current IP and agent port `58477`.
4. Check the name/IP and compare the **certificate fingerprint** in Home Assistant with the Windows **Home Assistant** page. If they differ, stop.
5. Enter the six-digit code and confirm. Do not enter your Windows password, a Home Assistant token or a Matter QR code.
6. Open the new device under WakeLink. You should see its **Power** switch, **Restart** button, **Boot time** and **Uptime**.

**Already paired? Skip this section when updating.** No fixed PC IP is normally required; changed addresses are rediscovered on the local network. If discovery is blocked by a guest network/VLAN, see [Help](HELP.en.md#home-assistant-does-not-find-my-device).

## 5. Test safely

1. Leave the PC on and check its state in Home Assistant. **Do not turn Power off just to refresh:** it requests a real shutdown.
2. Before testing wake, confirm that your physical PC's BIOS/UEFI and network adapter support and enable Wake-on-LAN; Ethernet is the simplest starting point. WakeLink cannot configure every manufacturer's firmware. Use the computer/network-card manufacturer's instructions.
3. Save your work. When ready for a real shutdown, turn **this PC's Power** switch off. Check that it shuts down.
4. Turn that switch on and allow time for startup. Verify the PC itself boots and then appears online again. If it does not wake, use [wake troubleshooting](HELP.en.md#shutdown-works-wake-does-not), rather than re-pairing.
5. Use **Restart** only when you actually intend to restart the PC. It is not a status-refresh button.

Sensors can be unavailable while the PC is off or starting. They return on a later status poll once the agent responds. Boot time means the last boot date/time, not startup duration.

## 6. Update or continue with Alexa

For Windows updates, open **Updates > Check for updates**, download the offered installer and install it **over** WakeLink. Update the integration in HACS separately and restart Home Assistant. Do not uninstall, delete the device, reset certificates or generate another pairing code just to update.

[Backups, rollback and update problems](HELP.en.md#update-without-pairing-again) explain both components. Old `PC Power Free` folders are intentional compatibility paths: leave them unchanged.

**Home Assistant works?** You are finished for local control. Only if you want voice control, follow [Alexa's illustrated guide](ALEXA.en.md). Matterbridge is not required for Home Assistant control.
