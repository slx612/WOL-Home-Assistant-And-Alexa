# WakeLink help and updates

[English](HELP.en.md) | [Español](HELP.es.md) | [Choose your installation guide](../README.md#start-here)

Find the symptom below. **Do not uninstall, delete the Home Assistant device or reset credentials as a first troubleshooting step.**

## Which file do I download?

Open [Releases](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases), choose a release with an installer for your system and expand **Assets**. Not every release contains every platform. A tag or source archive is not an installer.

| System | Normal installation file |
| --- | --- |
| Windows x64 | `WakeLink-Windows-x64-Setup.exe` |
| Ubuntu Desktop | `WakeLink-Ubuntu-<version>.deb` (available from beta.13) |
| DSM | `pcpowerfree-dsm-noarch-<version>.spk` (beta.13 uses revision 0024) |
| Home Assistant | HACS: search **WakeLink**; `WakeLink-Home-Assistant.zip` is only for manual installation |

Old `PC Power Free` paths and `pc_power_free` / `pcpowerfree` IDs are compatibility details. Do not rename them. The legacy Windows installer is an identical updater-compatible copy, not another app.

## Home Assistant does not find my device

1. Keep the device on. Open WakeLink there and check that its agent is running. In DSM, also check Package Center; in Ubuntu, complete **Enable WakeLink**.
2. Check that Home Assistant and the device can communicate on a trusted local network. A guest network, VPN, VLAN or firewall can block discovery.
3. Generate a fresh six-digit code in the device's WakeLink app. Then open **Settings > Devices & services > Add integration > WakeLink**. If a manual form appears, use the device's current IP and agent port `58477`, not DSM's desktop port.
4. Enter the code within ten minutes. Codes are temporary and single-use; neither your OS password nor a Matter QR belongs in this form. Verify the device name/IP. On Windows, compare the certificate fingerprint shown by both screens before submitting.

WakeLink normally rediscovers changed addresses; a fixed IP is not normally required. If automatic discovery cannot work on your network, a router DHCP reservation is a practical fallback. Restricting agent access to a single Home Assistant IP also means keeping that IP stable or updating the restriction. MAC addresses identify network adapters, not trusted administrators.

## It is on, but Home Assistant shows Off or Unavailable

Check the local agent first. The switch reflects agent reachability, not a direct measurement of electrical power. A disconnected or blocked agent can make an on device appear off. **Do not press Off to refresh:** it sends a shutdown request.

The default status poll is 30 seconds, configurable in WakeLink's Home Assistant options. Allow the system to boot and the agent to start, then wait for another poll. **Boot time** is the last system boot date/time; **Uptime** is time since boot, not since opening the app. Sensors are unavailable while the device/agent cannot be reached.

## Shutdown or restart fails

| Message or symptom | First check |
| --- | --- |
| DSM power permission is not enabled | In DSM's HTTPS desktop, open WakeLink and complete [its one-time permission](INSTALL_DSM.en.md#3-allow-shutdown-and-restart-once). |
| Linux power command failed | Check the installed package and service permissions. DSM must use the current DSM package, not generic Linux instructions. Do not grant arbitrary root access. |
| Windows rejects the command | Check WakeLink's shutdown protection; select **Allow commands** only when you intend to allow remote power actions. |
| Certificate or authentication error | Check that this is the expected device and preserve existing state. Do not disable TLS checks or delete certificates to hide the error. |
| Applications prevent shutdown | Save/close the applications and retry when ready. Forced shutdown can lose work; DSM does not support force/delay. |

## Shutdown works, wake does not

Wake-on-LAN is separate from the agent. On a physical computer, check its BIOS/UEFI Wake-on-LAN setting and network adapter support. Ethernet is the simplest starting point. A switch changing state is not proof that hardware woke. Windows Fast Startup and the firmware's supported sleep/shutdown states can affect wake; changing one setting cannot guarantee support. See [Microsoft's wake-state explanation](https://learn.microsoft.com/en-us/troubleshoot/windows-client/setup-upgrade-and-drivers/wake-on-lan-feature) and your hardware manufacturer's instructions.

On a supported Synology model, enable Wake-on-LAN in DSM's **Control Panel > Hardware & Power > General**, for the correct LAN interface. Menus/support vary by model; see [Synology's instructions](https://kb.synology.com/en-us/DSM/help/DSM/AdminCenter/system_hardware_general?version=7).

Home Assistant must still be on, and its wake packet must reach the correct network. Never forward WakeLink ports to the internet. WakeLink cannot start a stopped VirtualBox/other VM through its host.

## Update without pairing again

There are **two updates**: the device's app and the Home Assistant integration. Updating one does not update the other. Alexa's Matterbridge/plugin are separate too.

1. Back up Home Assistant under **Settings > System > Backups**; wait for completion and keep the encryption key. Preserve a protected copy of the device's WakeLink state and the previous installer.
2. **Windows:** open WakeLink **Updates > Check for updates**, then download/run the offered installer. Left-click the tray icon to open the app; right-click for its menu. A manual check needs GitHub access and a newer release with a Windows installer; it does not see unpublished local builds or integration-only betas.
3. **Ubuntu:** open WakeLink, select **Check for updates > Install update**, and approve Ubuntu's request. This is included in the new local preview; a newer published `.deb` is required. **DSM:** install the newer `.spk` over WakeLink through **Package Center > Manual Install**. A native package source has been tested locally; see [DSM updates](INSTALL_DSM.en.md#update-or-revoke-permission) for its publication status.
4. In **HACS > WakeLink**, install the new integration version and restart Home Assistant. If a beta is missing, check the version selector and HACS's option to show beta versions. Do not select an untested default-branch commit merely to get a higher number.
5. Check the existing device and sensor values. No new pairing code should be needed. If installation unexpectedly asks for first-time setup, stop and preserve the backup/error.

A fresh HA backup covers HA, not a separate Windows/Ubuntu machine. Device state contains credentials and must not be shared. Default state locations: Windows `C:\ProgramData\PC Power Free` (unless customized), Ubuntu `/etc/pc-power-free/`, DSM `/var/packages/pcpowerfree/var/`.

## Rollback

Keep the existing Home Assistant configuration entry and app state. Reinstall the previous integration version from HACS if offered, or restore the verified pre-update HA backup. A restore can remove unrelated changes made since that backup; review its contents first.

For device-app rollback, follow the system guide and use a tested state-preserving backup. **An older installer alone is not a guaranteed rollback**, especially in DSM, which can reject a lower package revision. Do not uninstall to force a downgrade. Alexa devices/tokens may need separate removal; restoring HA alone does not undo external pairing.

## Windows SmartScreen

The installer is currently **unsigned**. Microsoft may warn about an unknown app; rebuilding or changing its name does not guarantee removal of that warning.

1. Confirm that you downloaded the installer from this project's release **Assets**.
2. Download `SHA256SUMS.txt` from the **same release**.
3. In PowerShell, run this read-only check, replacing the example path with your file's location:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath "$env:USERPROFILE\Downloads\WakeLink-Windows-x64-Setup.exe"
```

4. Compare the full hash with the line for that filename. A mismatch means **do not run it**. A match confirms the downloaded bytes, not publisher identity or independent safety review.
5. If you trust the verified source, you decide whether to use **More info > Run anyway**. If that option is absent or your organization blocks it, stop; do not disable SmartScreen/antivirus or work around policy.

Signing and reputation are separate: [Microsoft's explanation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

## HACS icon or Alexa problem

The missing HACS store icon is a [known upstream issue](KNOWN_ISSUES.md#english), not a failed installation. Re-pairing/reinstalling WakeLink does not fix it.

For Alexa, follow the [illustrated guide](ALEXA.en.md), including assigning and **saving** the entity label before configuring **Filter By Label**. Do not remove the filter when no device appears.

## Report a problem safely

Use [GitHub Issues](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/issues). Include the system/version, WakeLink app/package version, integration version, guide step, exact error and a redacted screenshot. For DSM include its numeric package revision. Do not share config/state backups, passwords, tokens, pairing codes or Matter QR codes.
