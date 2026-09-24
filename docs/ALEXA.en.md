# Connect a WakeLink PC to Alexa (Matter preview)

[English](ALEXA.en.md) | [Espanol](ALEXA.es.md) | [Windows + Home Assistant first](GETTING_STARTED.en.md)

**Status: experimental, not yet tested end to end with an Echo.** WakeLink does **not** speak Matter itself. The current path is **WakeLink PC -> Home Assistant -> Matterbridge + `matterbridge-hass` -> Alexa**. Matterbridge is a separate Home Assistant app/plugin and must stay running when the PC is off. You need a [Matter-compatible Echo](https://developer.amazon.com/docs/alexaplus/smarthome/matter-support.html), the Alexa phone app and a trusted local network. No third-party subscription is needed. These steps can change when Matterbridge or Alexa updates.

## Before you start

1. [Install and pair WakeLink with Home Assistant](GETTING_STARTED.en.md). In **Settings > Devices & services > WakeLink > your PC > Configure > Connect with Alexa**, note the switch ID shown on the first screen, such as `switch.my_pc_power`. Do not press that switch yet: turning it off shuts down the PC.
2. Make a Home Assistant backup in **Settings > System > Backups**. Include Home Assistant configuration and the Matterbridge app if already installed. Keep its encryption key private.
3. If you previously exposed this same PC through Emulated Hue, remove that exposure before pairing Matter, or Alexa may show two copies. If your existing Matterbridge is *already paired* with Alexa or another controller, stop here: adding an unfiltered Home Assistant plugin could expose unrelated devices. Use a new isolated Matterbridge instance or configure a safe filter before connecting it.

## Set up Matterbridge

4. In Home Assistant open **Settings > Apps > App store > three-dot menu > Repositories**. Add the [official Matterbridge app repository](https://github.com/Luligu/matterbridge-home-assistant-addon): `https://github.com/Luligu/matterbridge-home-assistant-addon`. Install **Matterbridge**, start it and open **Web UI**. The menu can be called **Add-ons** on older Home Assistant versions.
5. In Matterbridge, find **Settings > Matter mDNS interface** and choose the same network interface shown by **Home Assistant > Settings > System > Network**. Do not guess an interface name; it depends on your host. Matterbridge and the Echo must be able to discover each other on the local network.
6. In Matterbridge's plugin page, install **`matterbridge-hass`**. It is a separate plugin; WakeLink does not install it. Do **not** scan Matterbridge's QR in Alexa yet.
7. Create a **Long-Lived Access Token** in your Home Assistant profile (**your name > Security**). This token grants broad Home Assistant access. Paste it only into the `matterbridge-hass` plugin's **Token** field, never into WakeLink or a support message. In its **Host** field use your Home Assistant WebSocket address, usually `ws://homeassistant.local:8123` on a trusted LAN. If Home Assistant uses HTTPS with a trusted certificate, use `wss://` instead. `ws://` does not encrypt the token; do not use it on an untrusted network. Do not disable certificate verification to bypass an HTTPS error.

## Export only this PC

8. In the plugin settings, set **Domain Whitelist** to `switch`. Set **Split Entities** to the exact switch ID from step 1, and **Whitelist** to that same ID. Save and restart the plugin. **An empty whitelist can expose other devices.** `Split Entities` is deprecated upstream; if it is missing, stop and follow the plugin's [Split By Label instructions](https://github.com/Luligu/matterbridge-hass#readme) instead of guessing.
9. Inspect Matterbridge's device list **before pairing**. The Home Assistant plugin must export only your intended PC switch, not other Home Assistant entities. If more devices appear, fix the filters and restart. Do not proceed with the QR until this is true.

## Pair Alexa

10. Open the Alexa phone app: **Devices > + > Add Device > Other > Matter > Yes > Scan QR Code**. Scan the **Matterbridge Matter QR code** shown in Matterbridge. It is *not* WakeLink's six-digit PC pairing code. Keep the phone, Echo and Matterbridge on the same discoverable local network. Alexa's menu wording may vary by app version.
11. Give the discovered switch a distinct name such as **Office PC**. First check whether Alexa shows it. Only test "turn off Office PC" after saving your work and deciding to shut down the PC. Then test turning it on from shutdown, if Wake-on-LAN already works from Home Assistant. Finishing WakeLink's on-screen guide does not verify these actions.

## If something fails or you want to undo it

- **No QR/device found:** confirm the mDNS interface, Echo Matter support, local discovery/multicast and that Matterbridge is running.
- **PC appears but will not wake:** first get Wake-on-LAN working from Home Assistant; Matterbridge cannot fix BIOS or network settings.
- **Wrong devices appear:** unpair Matterbridge from Alexa, correct the plugin filters, and pair again only after checking the exported list.
- **Undo:** remove Matterbridge from Alexa, disable/remove `matterbridge-hass`, then revoke its token in your Home Assistant profile. Leave the WakeLink PC and integration installed. A Home Assistant backup can restore HA/app settings, but revoking a token and removing an Alexa device must be checked separately.

Official references: [Matterbridge Home Assistant app](https://github.com/Luligu/matterbridge-home-assistant-addon/blob/main/DOCS.md), [`matterbridge-hass` filters](https://github.com/Luligu/matterbridge-hass#readme), [Amazon Matter support](https://developer.amazon.com/docs/alexaplus/smarthome/matter-support.html).
