# Install WakeLink: Windows + Home Assistant

[English](GETTING_STARTED.en.md) | [Espanol](GETTING_STARTED.es.md) | [Home](../README.md)

This is the basic route. **Alexa is optional** and has a [separate guide](ALEXA.en.md). You need a Windows x64 PC, Home Assistant, and both on the same trusted local network. For waking from a full shutdown, your PC must support Wake-on-LAN in its firmware and network adapter.

## 1. Install the Windows app

1. Open [WakeLink releases](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases). In the newest beta with a Windows installer, download **`WakeLink-Windows-x64-Setup.exe`**. Do not download `PCPowerAgent.exe`, `PCPowerTray.exe` or `PCPowerSetup.exe` separately. The old `pcpowerfree-windows-x64-setup.exe` is an identical copy retained for existing app updaters.
2. Run the installer. Choose English or Spanish and, if you want, the desktop shortcut. Administrator permission is needed to install the local agent and firewall rule. Keep **Open WakeLink** selected on the last page.
3. In WakeLink, choose **Enable and continue**. It configures automatic startup and the local network. You do not need to put the app into Windows Startup yourself.
4. If SmartScreen warns about an unknown app, check that the file came from this project's release page and compare its SHA-256 with `SHA256SUMS.txt` on that release. The installer is not code-signed; a matching hash does not prove publisher identity. Do not disable SmartScreen or antivirus.

## 2. Install the Home Assistant integration

1. In Home Assistant, open **HACS**, search for `WakeLink`, and download the integration. For a beta, select the latest beta if HACS offers a version choice. Restart Home Assistant when prompted.
2. Open **Settings > Devices & services**. Select the discovered WakeLink PC. If nothing appears, use **Add integration**, search for `WakeLink`, and select the discovered PC there.
3. On the Windows app, open the **Pair** page and generate a temporary six-digit code. Compare the certificate fingerprint in both screens, then enter the code in Home Assistant within ten minutes.
4. Confirm that the PC and its power switch now appear under WakeLink in Home Assistant. This confirms pairing; it does not yet prove that Wake-on-LAN is configured on your hardware.

**No fixed PC IP is normally required.** WakeLink discovers its address over the local network. If discovery cannot cross your VLAN/guest network, use the manual host option and consider a DHCP reservation in your router; a MAC address alone cannot route normal shutdown requests to an unknown IP.

## 3. Test safely

1. With the PC on, check that the WakeLink app says its local agent is running. Do **not** press the Home Assistant power switch merely to check a state: turning it off requests a real shutdown.
2. Save your work. When you are ready, turn the switch off in Home Assistant and verify the PC shuts down.
3. Turn the switch on to test Wake-on-LAN. If nothing happens, check firmware/adapter Wake-on-LAN settings and your network's broadcast handling. A successful pairing cannot enable unsupported hardware by itself.

## Updating or going back

Install the newer Windows installer **over** WakeLink, then update the integration in HACS and restart Home Assistant. Do not uninstall or delete the device: that would risk losing its pairing. For rollback, use HACS to reinstall the previous integration version if available, or replace only its files with that version's published integration ZIP and restart Home Assistant. Keep the existing configuration entry and Windows app/data. A full Home Assistant backup before trying a beta is recommended.

The old `PC Power Free` directory, `pc_power_free` integration ID and installer filename are compatibility details, not a second product.
