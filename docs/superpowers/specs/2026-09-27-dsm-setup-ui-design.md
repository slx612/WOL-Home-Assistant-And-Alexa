# WakeLink DSM setup UI

> **Historical record / Registro histórico.** Not current setup instructions. Use the [current guides / guías actuales](../../README.md). Old names, versions and test results below describe that point in development only.

## Goal

An administrator installs or upgrades one WakeLink `.spk`, opens **WakeLink** from DSM, sees whether the agent is running, and can create a six-digit Home Assistant pairing code without SSH or reading files. The page has Spanish and English text. Existing Home Assistant pairings survive the upgrade. No shutdown or restart control is added.

## Approach

Keep the internal DSM package ID `pcpowerfree` and the existing data directory, but change the visible package/app name to WakeLink. Package a small HTML/CSS/JavaScript page and DSM launcher using `dsmuidir` and `dsmappname`, so **Open** in Package Center and the DSM menu reach the same page. Do not require Web Station, Matterbridge, a cloud service, or a separate public port. Synology documents this launcher mechanism in its [Desktop Application guide](https://help.synology.com/developer-guide/integrate_dsm/desktopapp.html).

The page shows agent status, hostname, local address, and the pairing flow. It does not reveal the long-lived API token, TLS private key, or full config. A new code is displayed only in the response to the administrator who requested it, expires after ten minutes, and does not replace the existing API token or machine identity. The page explains how to enter it in Home Assistant and when no new code is needed.

## Trusted action path

The browser calls a same-origin DSM package CGI endpoint; it never calls the agent's self-signed HTTPS endpoint directly. The CGI forwards a narrowly defined request to a loopback-only setup endpoint in the existing WakeLink agent. The agent, running as its existing package user, validates the DSM session with Synology's `authenticate.cgi`, checks administrator membership, and performs only `status` or `generate pairing code`. Synology documents `authenticate.cgi` for package CGI authentication in its [Application Authentication guide](https://help.synology.com/developer-guide/integrate_dsm/web_authentication.html).

The setup endpoint rejects non-loopback clients. State-changing requests require POST, an exact custom header, a valid DSM session, and no cross-origin access; responses are non-cacheable. No DSM cookie or pairing code is logged. The CGI cannot read or write `config.json`, and no package secret is copied into web-readable files. It must verify the agent's TLS certificate using a public certificate copy rather than disabling TLS verification. If DSM authentication cannot be verified while running as the package user on the test VM, stop and revise the design rather than weaken authentication or file permissions.

The agent already reloads config changes; the new pairing action must use the existing pairing-code update logic and preserve `token`, `machine_id`, and TLS files. The DSM pre/post-upgrade backup must include config and TLS identity.

## Scope and verification

1. Build the DSM UI and its minimal backend, with ES/EN copy and the existing WakeLink icon. Keep package identity and stored credentials intact.
2. Unit-test authentication denial, local-only access, code expiry/persistence, and packaging metadata. Test that no shutdown route is exposed by the new UI.
3. Rebuild the `.spk` with a DSM package version greater than the one installed on the test VM. Inspect the archive before installation.
4. Back up the current WakeLink config, certificate, key, and previous `.spk` on DSM test VM `.167`; install only there. Confirm the page opens from DSM, status is correct, a new code links a test Home Assistant entry, and the pre-existing pairing remains online. Do not send any NAS power commands.
5. On failure, stop and report the exact failure before recovery. DSM `.177` is out of scope. Do not publish the package as stable until the test succeeds.

## Non-goals

No NAS shutdown/restart controls, full settings editor, remote access, automatic package repository, or Ubuntu/Windows UI changes in this work.
