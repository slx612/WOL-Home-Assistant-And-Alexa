# WakeLink with Alexa: step-by-step guide

[English](ALEXA.en.md) | [Espanol](ALEXA.es.md) | [Install WakeLink first](GETTING_STARTED.en.md)

**Status: beta; not yet tested end to end with a real Echo.** WakeLink does not connect to Alexa directly. The route is **WakeLink PC -> Home Assistant -> Matterbridge -> Alexa**. Matterbridge and its `matterbridge-hass` plugin are separate software and must keep running on the Home Assistant host when the PC is off. There is no third-party subscription, but Alexa may need the internet for voice recognition.

You need a PC already paired with WakeLink in Home Assistant, Home Assistant OS with the **Apps** menu (formerly **Add-ons**), a [Matter-compatible Echo](https://developer.amazon.com/docs/alexaplus/smarthome/matter-support.html), and the Alexa phone app. Echo and Home Assistant must be discoverable on the local network. **You do not need Home Assistant's Matter integration:** it imports Matter devices into Home Assistant, not your PC into Alexa.

There are **two different codes**: WakeLink's **six-digit code** pairs the PC with Home Assistant; Matterbridge's **Matter QR code** pairs the bridge with Alexa. Do not scan the QR before step 6.

## 1. Check the PC and make a backup

1. Follow [the WakeLink installation guide](GETTING_STARTED.en.md) if the PC is not yet under **Settings > Devices & services > WakeLink**.
2. Open that PC and find its **power switch**. Open the entity details and note its **ID**, for example `switch.my_pc_power`. It must start with `switch.`. Do not toggle it just to inspect it: switching it off may shut down the PC.
3. Make a backup under **Settings > System > Backups**. Keep its encryption key private.
4. If you already share this PC with Alexa through Emulated Hue, remove that exposure first to avoid a duplicate. If **Matterbridge is already paired with Alexa**, do not follow this first-install recipe: a new unfiltered plugin could share unrelated devices. Set a safe filter before connecting it, or use an isolated instance.

**Checkpoint:** you have the exact `switch.` ID and a backup.

## 2. Install and open Matterbridge

1. In Home Assistant open **Settings > Apps > App store**. Older versions call **Apps** **Add-ons**.
2. Open **... > Repositories**, paste `https://github.com/Luligu/matterbridge-home-assistant-addon`, and select **Add**. This is the [official repository](https://github.com/Luligu/matterbridge-home-assistant-addon).
3. Find **Matterbridge**, select **Install**, and wait. Enable **Start on boot** so it runs when the PC is off. Select **Start** and **Open Web UI**. The first start may take several minutes; if the app is not ready, wait and retry.
4. The top navigation says **Home | Devices | Logs | Settings**. **Home** already shows a QR code. **Do not scan it yet.**

**Checkpoint:** Matterbridge opens and **Home** contains **Install plugins**. If not, check its app logs in Home Assistant.

## 3. Select the correct network

1. In another Home Assistant tab open **Settings > System > Network**. Note the name of the primary interface with your home-network address. It might be `end0`, `eth0`, or something else: do not blindly copy an example.
2. In Matterbridge select **Settings** at the top and find **Matter settings > Mdns interface**. Enter that exact name. Save and restart Matterbridge if prompted.

**Checkpoint:** on **Home > System info**, **Interface name** matches that network. A guest network isolating your Echo may prevent discovery.

## 4. Mark only the PC switch

1. In Home Assistant open **Settings > Areas, labels & zones > Labels > Create label**. Name it `WakeLink Alexa`. Capitalization and spaces matter.
2. Go to **Settings > Devices & services > Entities** and search for the `switch.` ID from step 1. Enable table selection mode, select **only that entity**, choose **Add label**, and select `WakeLink Alexa`. If your version has labels in entity settings, adding it there works too.
3. **Do not** put this label on the whole device, an area, or other entities. Confirm in the list that only the intended switch has `WakeLink Alexa`.

**Checkpoint:** the label identifies one entity. It is the filter before anything is shared with Alexa.

## 5. Install the plugin and limit what it exports

1. Under **Matterbridge > Home > Install plugins**, enter `matterbridge-hass` in **Plugin name or plugin path**, leave **Tag or version** at `latest`, and select **Install**. Wait for it to appear under **Plugins**. **Do not scan the QR.**
2. In Home Assistant select your username in the lower-left corner, then **Security > Long-Lived Access Tokens > Create token**. Name it, for example, `Matterbridge WakeLink`. Copy it when created. This credential gives broad Home Assistant access: never paste it into WakeLink, GitHub, screenshots, or chats.
3. Open the **Plugins > matterbridge-hass** configuration in Matterbridge. Set **Host** to your Home Assistant WebSocket address, usually `ws://homeassistant.local:8123` on a trusted private LAN. If you use HTTPS with a valid certificate, use `wss://` and your actual hostname. `ws://` does not encrypt the token: do not use it on an untrusted network. Do not disable certificate validation to hide an error.
4. Paste the token into **Token**. Set **Filter By Label** to exactly `WakeLink Alexa` and **Domain Whitelist** to `switch` only. Save and restart the plugin if prompted. **Do not use Split Entities:** it is deprecated and unnecessary here. An empty **Whitelist** is not a filter; **Filter By Label** is the filter for this route.
5. Open **Matterbridge > Devices**. There must be **exactly one device** from `matterbridge-hass`: your PC power switch. If there are zero, recheck Host, Token, and label. If there are more than one, **do not pair Alexa**: check the label and filter.

**Required checkpoint:** do not move to the QR until **Devices** shows only the intended PC. The plugin may show many devices if incorrectly filtered.

## 6. Pair Matterbridge with Alexa

1. Open **Home** in Matterbridge and leave **QR pairing code** visible. It is not WakeLink's six-digit code. Do not publish the QR or manual code: someone on your network could try to pair the bridge.
2. On your phone open **Alexa > Devices > + > Add Device > Other > Matter**. Confirm the prompts and select **Scan QR Code**. Scan Matterbridge's QR. Button labels may change across Alexa versions; look for **Matter**.
3. Wait for Alexa to find the bridge and switch. Give the PC a clear name such as **Office PC**. If other Home Assistant devices appear, remove the bridge from Alexa, fix the step 5 filter, and do not test voice commands.
4. First check that the PC **appears** in Alexa. To test shutdown, save your work and say “Alexa, turn off Office PC.” Only if Wake-on-LAN already works from Home Assistant, test “Alexa, turn on Office PC” while the PC is off.

**Expected result:** one PC device in Alexa responding to both commands. Completing the guide does not prove this works: test it on a real Echo.

## If it fails or you want to undo it

- **Matterbridge is not ready:** wait, retry, and if it persists check its app logs in Home Assistant.
- **Devices shows zero:** check WakeLink, the label on the `switch.` *entity*, and Host/Token for `matterbridge-hass`.
- **Devices shows more than one:** do not scan the QR. Remove extra labels or correct **Filter By Label**, restart the plugin, and count again.
- **Alexa cannot find it:** check **Mdns interface**, Echo Matter support, and local connectivity among Echo, phone, and Home Assistant.
- **Alexa cannot wake the PC:** first test Wake-on-LAN from Home Assistant. Matterbridge cannot change BIOS/UEFI or network-adapter settings.
- **Undo:** remove the Matterbridge bridge from Alexa, disable/uninstall `matterbridge-hass`, and **revoke its token** under **Home Assistant > your profile > Security**. You may remove the label. Keep your WakeLink PC and pairing. Restoring a backup does not revoke the token or remove Alexa's device by itself.

Sources: [Matterbridge app](https://github.com/Luligu/matterbridge-home-assistant-addon/blob/main/DOCS.md), [`matterbridge-hass` filters](https://github.com/Luligu/matterbridge-hass/discussions/186), [Home Assistant labels](https://www.home-assistant.io/docs/organizing/labels/), [Amazon Matter support](https://developer.amazon.com/docs/alexaplus/smarthome/matter-support.html).
