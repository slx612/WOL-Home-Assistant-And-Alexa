# Project Context

Last updated: 2026-04-25

## What This Project Is

This repository is a local solution to control the power state of a Windows PC from Home Assistant and Alexa.

The real supported flow is:

1. A Windows program installs a local agent on the PC.
2. The program shows a temporary 6-digit pairing code.
3. Home Assistant discovers the PC on the LAN and pairs with that code.
4. Home Assistant can wake, shut down, and restart the PC.
5. Alexa support happens through Home Assistant.

Important: there is no native Alexa skill implemented in this repository. Alexa is expected to work through Home Assistant as the bridge.

## Why This Exists

The goal is to replace the old Alexa WOL approach used by a third-party skill that moved to a paid yearly subscription.

The project is meant to be public and usable by other people, not just as a private one-off setup.

## Current Product Scope

Current intended v1 scope:

- Windows agent + installer
- Home Assistant custom integration
- Alexa through Home Assistant

Not in current scope:

- Alexa-only operation without Home Assistant
- A direct Alexa skill inside this repo

There is a future design/roadmap folder for broader ideas, but it is not the current shipped product.

## Important Folders

- `windows_agent/`: active Windows installer and local agent
- `custom_components/pc_power_free/`: active Home Assistant integration
- `release_assets/`: packaged Home Assistant integration zip
- `docs/`: docs and release notes
- `v2_universal/`: future architecture ideas, not current runtime product
- `Programa antiguo WOL (wake on lan/`: legacy material, not active source

## How It Works

Windows side:

- `windows_agent/setup_wizard_gui.py` installs and configures the PC agent
- It detects network info, creates local config, generates a token, and shows a temporary pairing code
- It can create the firewall rule and startup task

Agent side:

- `windows_agent/pc_power_agent.py` runs a local HTTP server on port `58477`
- It advertises the PC with mDNS `_pcpowerfree._tcp.local.`
- It exposes status, pairing, shutdown, and restart endpoints

Home Assistant side:

- `custom_components/pc_power_free/config_flow.py` handles discovery and pairing
- `custom_components/pc_power_free/api.py` sends Wake-on-LAN packets and calls the Windows agent
- `custom_components/pc_power_free/switch.py` exposes the on/off entity
- `custom_components/pc_power_free/button.py` exposes the restart button

## Naming

Current integration name: `PC Power Free`

Current Home Assistant domain: `pc_power_free`

Main repo:

- `slx612/WOL-Home-Assistant-And-Alexa`

The repo name is not ideal, but the in-product naming currently points to `PC Power Free`.

## Current Publication State

The repo is already published as a public prerelease and the HACS default submission is already open.

Changes already made:

- `hacs.json` cleaned up to pass HACS validation
- `.github/workflows/validate.yml` uses HACS validation without the old `ignore` exemptions
- `.github/workflows/hassfest.yml` exists and passes
- `custom_components/pc_power_free/manifest.json` was fixed for hassfest and later moved forward to `0.2.0-beta.4`
- `custom_components/pc_power_free/__init__.py` has `CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)` for hassfest
- README and docs were updated for HACS publishing

Current public prerelease:

- `v0.2.0-beta.6`

Validation runs used for HACS submission:

- HACS action: `https://github.com/slx612/WOL-Home-Assistant-And-Alexa/actions/runs/24668678461`
- Hassfest: `https://github.com/slx612/WOL-Home-Assistant-And-Alexa/actions/runs/24668678393`

Original release used when the HACS submission was first opened:

- `https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.3`

Current latest published prerelease:

- `https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.6`

## HACS Default Repository Submission

Status at last check:

- PR open in `hacs/default`
- PR number: `#7156`
- Title: `Adds new integration [slx612/WOL-Home-Assistant-And-Alexa]`

Related PRs:

- `#7139` closed
- `#7155` closed
- `#7156` is the active one

Fork used for the HACS submission:

- `slx612/default`

Branch used for the active PR:

- `add-pc-power-free`

Important:

- Do not open more PRs for the same thing
- Do not comment on the HACS PR unless there is an actual blocker or a maintainer asks for something
- Do not touch the `slx612/default` fork or the `add-pc-power-free` branch unless HACS asks for changes
- It is fine to keep working on the main project repo while waiting

## What Can Be Touched Safely

Safe to keep changing:

- `slx612/WOL-Home-Assistant-And-Alexa`
- code
- docs
- releases
- real-world testing

Better not touch while the HACS PR is waiting:

- `slx612/default`
- branch `add-pc-power-free`
- PR `hacs/default#7156`

## Known Reality Checks

- Home Assistant itself, `zeroconf` discovery, and pairing-code linking have now been validated on a real setup
- Alexa-only local control without Home Assistant is still not solved in a clean way without external cloud pieces
- The current serious path is still `Windows agent + Home Assistant + Alexa through Home Assistant`
- The only remaining real-world validation still pending is Alexa through Home Assistant

## Best Next Step

The main remaining engineering step is the Alexa validation:

1. Expose the Home Assistant entity through the chosen Alexa path
2. Test voice-driven wake, shutdown, and restart end-to-end
3. Fix whatever breaks in that real setup

## Recent Local Changes

Changes made locally on 2026-04-21 after the context above:

- `windows_agent/network_info.py` was reworked because the setup GUI could fail with:
  `Expecting value: line 1 column 1 (char 0)`
- The old detection path relied on `Get-NetIPConfiguration` returning JSON, but on this Windows machine that call could return empty stdout from Python
- The new detection path uses `Win32_NetworkAdapterConfiguration` via PowerShell/CIM
- Adapter selection is now ranked with a clearer heuristic:
  current outbound IPv4 first, then default gateway, then non-link-local, then non-virtual adapters
- This fixed the real detection case on this machine and correctly selected:
  `Ethernet / 192.168.100.193 / 74:56:3C:BA:22:44`

- `windows_agent/setup_wizard_gui.py` now checks GitHub releases for updates
- The check runs automatically shortly after the GUI opens
- There is also a manual `Check updates` / `Buscar actualizaciones` button
- If a newer release exists, the app offers to open the GitHub release page in the browser
- The update check is threaded so the Tkinter UI does not freeze while talking to GitHub
- That work first landed while the line still showed `0.2.0-beta.3`, but the current shipped version was later bumped to `0.2.0-beta.4`

- `windows_agent/pc_power_tray.py` was added as a new Windows tray companion app
- The tray app is intended to be started in the user session and show up in Windows startup apps
- It talks to the local agent over a localhost-only authenticated API
- Current tray protection modes implemented:
  allow requests
  ignore for 15 minutes
  ignore for 1 hour
  ignore until manually re-enabled

- `windows_agent/pc_power_agent.py` now includes a persistent command-guard state
- New local endpoints exist for the tray app to read and change that state:
  `GET /v1/local/guard`
  `POST /v1/local/guard`
- When command guard is active, shutdown/restart requests are rejected instead of being executed
- The authenticated status payload now also reports:
  `command_guard_active`
  `command_guard_mode`
  `command_guard_until_ts`

- `custom_components/pc_power_free/api.py` was updated so Home Assistant treats the guard block as a command rejection instead of a generic network failure
- `custom_components/pc_power_free/switch.py` now exposes the command guard attributes as extra diagnostics

- `windows_agent/setup_wizard_gui.py` was simplified visually
- The setup window now has a branded header drawn directly in Tkinter
- Only the most relevant fields are shown by default
- Advanced fields are hidden behind a `Show advanced settings` / `Mostrar ajustes avanzados` toggle
- `Install at startup` was reframed as starting the full PC Power Free experience with Windows
- The setup now registers the tray app in `HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`
- The setup also tries to launch the tray app immediately after a successful install

- Build and installer pipeline changes:
  `windows_agent/build-exe.ps1` now installs `pillow` and `pystray`
  `windows_agent/build-exe.ps1` now builds `PCPowerTray.exe`
  `windows_agent/build-installer.ps1` now requires `PCPowerTray.exe`
  `windows_agent/pcpowerfree-installer.nsi` now ships `PCPowerTray.exe`
  uninstall now removes the tray autorun value and tries to stop `PCPowerTray.exe`
  installer upgrades now try to stop the scheduled task plus `PCPowerAgent.exe` and `PCPowerTray.exe` before overwriting binaries

- `windows_agent/pcpowerfree-installer.nsi` was aligned to `0.2.0-beta.3`
- This avoids a version mismatch between the installer metadata and the setup app update checker

- Rebuilt binaries after these changes:
  `windows_agent/dist/PCPowerAgent.exe`
  `windows_agent/dist/PCPowerTray.exe`
  `windows_agent/dist/PCPowerSetup.exe`
  `windows_agent/dist/pcpowerfree-windows-x64-setup.exe`

- Home Assistant branding assets were refreshed in:
  `custom_components/pc_power_free/brand/icon.png`
  `custom_components/pc_power_free/brand/logo.png`
- The old logo was visually cropped; the new assets now match the desktop app branding:
  green monitor mark, orange power accent, and a clean dark badge for the wide logo

- The Windows agent status payload now reports:
  `uptime_seconds`
  `booted_at`
- Home Assistant now exposes those via:
  `custom_components/pc_power_free/sensor.py`
- New sensor entities added:
  `Uptime`
  `Boot time`
- `custom_components/pc_power_free/switch.py` also exposes the same fields as extra diagnostics

- The public GitHub repository was updated on `main` with these branding and desktop-agent changes
- Commit published:
  `d271306` - `Refresh branding and publish desktop app updates`
- The root `README.md` and `docs/README.es.md` now include the brand image and summarize the new tray/update/sensor features

- Local release preparation for `v0.2.0-beta.4` is complete
- Updated version constants to `0.2.0-beta.4` in:
  `custom_components/pc_power_free/manifest.json`
  `windows_agent/pc_power_agent.py`
  `windows_agent/pc_power_tray.py`
  `windows_agent/setup_wizard_gui.py`
  `windows_agent/pcpowerfree-installer.nsi`
- Rebuilt release artifacts for beta 4:
  `windows_agent/dist/PCPowerAgent.exe`
  `windows_agent/dist/PCPowerTray.exe`
  `windows_agent/dist/PCPowerSetup.exe`
  `windows_agent/dist/pcpowerfree-windows-x64-setup.exe`
  `release_assets/pcpowerfree-home-assistant-integration.zip`
- The integration zip was regenerated without `__pycache__` or `.pyc` files and keeps the expected path:
  `custom_components/pc_power_free/...`
- Those beta 4 prep changes were published to GitHub `main` in:
  `3406d9e` - `Prepare v0.2.0-beta.4 release`

- `README.md` and `docs/README.es.md` were revised again after beta 4 prep to better match the real user flow:
  publication status now explicitly says the repo code targets `v0.2.0-beta.4`
  Alexa is now clearly documented as `experimental` until a real end-to-end validation is done
  Windows install instructions now mention the tray app, startup behavior, and update checker
  HACS instructions now mention prerelease visibility and the Home Assistant `2026.3+` requirement for bundled local `brand/` images
- Those README changes were later published to GitHub `main` after initially being left only in local files:
  `7fa78d4` - `Update README for beta 4 status and current flow`
  `27f6f67` - `Update Spanish README for beta 4 status and current flow`
- The publication-state sections in both READMEs were then corrected again to reflect the real public status:
  `v0.2.0-beta.4` prerelease is already published
  `hacs/default#7156` is already open
  what remains on the HACS side is maintainer review, not opening the PR or publishing the release
  published commits:
  `6a39e45` - `Fix README publishing status after beta 4 release`
  `d5d3e27` - `Fix Spanish README publishing status after beta 4 release`
- The README status sections were updated once more after confirming real-world validation progress:
  Home Assistant itself, `zeroconf` discovery, and pairing-code linking are now treated as validated on a real setup
  the only remaining real-world validation still pending is Alexa through Home Assistant
  published commits:
  `15aa19f` - `Update README validation status after real Home Assistant testing`
  `252a977` - `Actualizar estado de validacion en README es tras pruebas reales`
- The redundant section that said the repository was "prepared for" several distribution paths was removed from both READMEs:
  it now jumps directly from the publishing header to the current HACS-default status
  published commits:
  `c734516` - `Remove redundant publishing-prepared section from README`
  `e92f0fb` - `Eliminar bloque redundante de publicacion en README es`
- The recommended pairing flow in both READMEs was refined to match the real UX better:
  install the Windows side first
  keep the temporary pairing code visible after install
  then complete the Home Assistant flow while that code is still active
  the docs now also mention the 10-minute expiry and that a new code can be generated from the Windows configurator
  published commits:
  `59b06ad` - `Clarify pairing flow in README`
  `440ca2c` - `Aclarar flujo de vinculacion en README es`
- The tray app now checks GitHub releases automatically after Windows startup:
  the existing setup-app update checker still exists
  the tray now performs a delayed startup check, throttled to at most once every 6 hours
  if a newer release is found, it shows a native yes/no prompt offering to open the release page
  the tray menu also now includes a manual `Check for updates` action
  automatic prompts are only shown once per release version unless the user checks manually
- The setup summary text was also adjusted so the recommended pairing flow matches the real install UX:
  install Windows first, keep the code visible, then complete Home Assistant before the 10-minute expiry
- Source and rebuilt binaries were published to GitHub `main` in:
  `f3e2f09` - `Add startup update checks to tray app`
- README docs were updated to mention the automatic tray update check in:
  `a256893` - `Document automatic tray update checks in README`
  `0744fc5` - `Documentar comprobacion automatica de updates en README es`

## Shutdown Checkpoint 2026-04-22

If the conversation is lost again, the important current truth is:

- latest published prerelease: `v0.2.0-beta.4`
- active HACS PR: `hacs/default#7156`
- Home Assistant path is already validated on a real setup
- remaining real-world validation: Alexa through Home Assistant
- the Windows tray app now auto-checks GitHub releases at Windows startup, throttled to once every 6 hours
- the tray can also check manually from its menu and show a native prompt offering to open the release page
- the recommended pairing flow in docs now matches the real install UX:
  install Windows first, keep the code visible, then complete the Home Assistant flow before the 10-minute expiry
- latest source commit published for the tray startup-update behavior:
  `f3e2f09` - `Add startup update checks to tray app`

- Validation already done for these local changes:
  Python syntax check passed
  `detect_primary_adapter()` was verified from Python
  GitHub release lookup was verified against the real GitHub API
  the new localhost command-guard API was verified with a temporary local agent instance
- Not yet fully verified:
  manual click-through smoke test of the newly packaged GUI after rebuild
  real Windows startup-app visibility after install
  real tray-icon interaction from the packaged `PCPowerTray.exe`

## End Of Day Checkpoint 2026-04-22

This is the shortest correct resume point for the work done today:

- current public release line: `v0.2.0-beta.4`
- active HACS submission: `hacs/default#7156`
- Home Assistant integration, `zeroconf` discovery, and pairing-by-code have already been validated on a real setup
- the only remaining real end-to-end validation still pending is Alexa through Home Assistant
- the Windows setup app checks GitHub releases automatically when opened and can also check manually
- the Windows tray app now also checks GitHub releases automatically after Windows startup, throttled to once every 6 hours, and can prompt the user to open the latest release page
- the tray menu includes manual update checking plus guard modes to ignore Home Assistant power requests for 15 minutes, 1 hour, or until manually re-enabled
- the recommended pairing flow is now documented as:
  install Windows first, keep the temporary code visible, then complete Home Assistant within the 10-minute expiry window
- both `README.md` and `docs/README.es.md` were corrected and published so they now reflect:
  beta 4 already published
  HACS PR already open
  Home Assistant path already validated
  Alexa still experimental/pending real validation
- branding assets exist in `custom_components/pc_power_free/brand/`, but bundled custom-integration branding only shows automatically on Home Assistant `2026.3+`; older versions will still show the generic placeholder unless the integration is added to the official `home-assistant/brands` repo
- latest source commit published for today's tray auto-update behavior: `f3e2f09`
- latest README commits published for today's documentation alignment:
  `a256893` - `Document automatic tray update checks in README`
  `0744fc5` - `Documentar comprobacion automatica de updates en README es`

## Cross-Platform Bootstrap 2026-04-25

Work started to open the project beyond Windows without forking Home Assistant into separate integrations.

Important current architectural direction:

- keep one Home Assistant integration: `pc_power_free`
- keep one external contract for discovery, pairing, status and power actions
- allow different local runtimes per platform:
  Windows desktop app
  Linux agent
  DSM package
- do not try to force the same UI on every OS
- DSM is expected to reuse the shared protocol and as much Linux runtime logic as possible, but it still needs its own packaging and privilege work

Changes created locally on 2026-04-25:

- a full snapshot backup of the repository was created at:
  `C:\Users\sergi\Desktop\copia de seguridad\wake on lan`
- new shared agent package:
  `agent_core/`
- `agent_core/common.py` now contains the shared HTTP server, config handling, pairing helpers, guard-state logic, and zeroconf advertisement
- the shared runtime now expects a platform adapter to provide:
  primary adapter detection
  MAC address lookup
  uptime
  actual local shutdown/restart execution
- `windows_agent/pc_power_agent.py` was reduced to a Windows wrapper over that shared runtime
- `windows_agent/network_info.py` was adjusted so the existing Windows setup GUI can still import it safely after the new shared package was introduced
- first Linux runtime added in:
  `linux_agent/pc_power_agent.py`
- first Linux network detection added in:
  `linux_agent/network_info.py`
  based on `ifaddr`, `/proc/net/route`, and `/sys/class/net`
- first Linux setup flow added in:
  `linux_agent/setup_cli.py`
  it writes `config.json`, generates token + temporary pairing code, and prints the summary for Home Assistant linking
- Linux support files added:
  `linux_agent/config.example.json`
  `linux_agent/pcpowerfree-agent.service`
  `linux_agent/README.md`
- DSM planning placeholder added:
  `dsm_package/README.md`
- design note added:
  `docs/CROSS_PLATFORM_PLAN.md`

Validation already done for the 2026-04-25 work:

- `py -3 -m compileall` passed for the new shared core and Linux files
- `py_compile` passed for:
  `agent_core/common.py`
  `agent_core/__init__.py`
  `windows_agent/setup_wizard_gui.py`
  `linux_agent/pc_power_agent.py`
  `linux_agent/setup_cli.py`
- `py -3 windows_agent/pc_power_agent.py --help` works
- `py -3 linux_agent/pc_power_agent.py --help` works
- `py -3 linux_agent/setup_cli.py --help` works

Not yet validated for the 2026-04-25 work:

- real Linux end-to-end pairing with Home Assistant
- actual Linux shutdown/restart execution on hardware
- DSM packaging or DSM privilege model
- Home Assistant consuming the new optional `platform` / `capabilities` metadata

Immediate next step after this checkpoint:

- test the Linux runtime on a real machine
- then start the DSM `.spk` packaging layer on top of the shared core

## Linux Runtime Test 2026-04-25

The first real Linux smoke test was completed on an Ubuntu machine on the same LAN.

Environment used:

- Ubuntu host IP: `192.168.100.157`
- Python: `3.12.3`
- temporary test user created for SSH-based validation
- a temporary working copy of the repo was uploaded to the Linux home directory

What was validated successfully:

- the Linux setup flow in `linux_agent/setup_cli.py` generated a real config and pairing code
- detected Linux network values were correct on that machine:
  host `sergio-VirtualBox`
  adapter `enp0s3`
  IP `192.168.100.157`
  MAC `08:00:27:3A:65:0A`
  subnet `192.168.100.0/24`
  broadcast `192.168.100.255`
- the Linux agent in `linux_agent/pc_power_agent.py` started successfully with the shared `agent_core`
- `GET /v1/discovery` worked from another machine on the LAN
- pairing worked end-to-end with a real temporary code and returned a real API token
- pairing correctly invalidated the temporary code in `config.json`
- authenticated `GET /v1/status` worked and reported:
  `platform = linux`
  `capabilities = ["shutdown", "restart", "guard", "pairing", "discovery"]`
  valid `uptime_seconds`
- local command guard endpoints worked:
  `GET /v1/local/guard`
  `POST /v1/local/guard`
- `zeroconf` advertisement was visible from another machine on the LAN as:
  `sergio-VirtualBox-eaf5e1ed._pcpowerfree._tcp.local.`

What was intentionally not tested yet:

- real Linux shutdown execution
- real Linux restart execution
- systemd service installation on the host
- Home Assistant UI flow consuming the Linux agent directly
- DSM packaging and DSM privilege handling

Important note:

- after the smoke test, the temporary Linux agent process was stopped again so port `58477` is no longer left open on that Ubuntu test machine

## Port Migration 2026-04-25

The project default agent port was moved away from `8777` to reduce the chance of conflicts with other self-hosted software and future DSM workloads.

Current default agent port:

- `58477`

Scope of the migration already completed:

- shared runtime defaults in `agent_core`
- Home Assistant integration defaults
- Windows setup and tray defaults
- Windows helper scripts and config examples
- Linux config example
- rebuilt Windows binaries and installer in `windows_agent/dist`
- regenerated Home Assistant integration zip in `release_assets/pcpowerfree-home-assistant-integration.zip`

Reasoning used for the choice:

- `58477` is in the IANA dynamic/private range, which is not assigned to registered services
- this makes it a safer fixed default than a more obvious or commonly reused user port

Extra validation already done after the migration:

- the Linux setup flow was rerun on the Ubuntu test machine and generated `config.json` with port `58477`
- the Linux agent was started successfully on `58477`
- `GET /v1/discovery` was confirmed from another LAN machine against `http://192.168.100.157:58477/v1/discovery`
- after the check, that temporary Linux agent process was stopped again

## Home Assistant Multiplatform Integration Work 2026-04-25

The Home Assistant integration was updated so it no longer assumes that every discovered agent is a Windows machine.

Changes completed locally:

- `custom_components/pc_power_free/api.py`
  now normalizes and carries:
  `platform`
  `capabilities`
  through discovery, pairing and authenticated status
- `custom_components/pc_power_free/config_flow.py`
  now stores discovered `platform` / `capabilities` into the config entry
  and shows discovered devices with a platform label in the selection list
- config-flow wording was generalized away from Windows-only phrasing in:
  `strings.json`
  `translations/en.json`
  `translations/es.json`
- shared platform metadata helpers added in:
  `custom_components/pc_power_free/platforms.py`
- shared entity device metadata helper added in:
  `custom_components/pc_power_free/device_info.py`
- entity device model labels are now derived from the platform instead of being hardcoded as `Windows PC`
- the restart button is now hidden when an agent explicitly reports capabilities and does not include `restart`
- switch extra attributes now expose:
  `platform`
  `capabilities`

Validation done for this step:

- `py -3 -m compileall custom_components/pc_power_free` passed after the changes

Not yet validated for this step:

- full Home Assistant UI smoke test with a Linux-discovered entry
- config-entry migration behavior for already-installed older entries inside a live HA instance

## Linux Remote Install 2026-04-25

The Ubuntu test machine was then converted from a temporary smoke-test host into a persistent Linux install target for a live Home Assistant check.

Installed target:

- host `192.168.100.157`
- hostname `sergio-VirtualBox`
- agent installed under `/opt/pc-power-free`
- config stored at `/etc/pc-power-free/config.json`
- `systemd` service installed as `pcpowerfree-agent.service`
- runtime port `58477`

What was completed:

- latest local `agent_core` and `linux_agent` were uploaded to the Ubuntu host
- Python virtual environment created at `/opt/pc-power-free/.venv`
- runtime dependencies installed in that venv:
  `ifaddr`
  `zeroconf`
- systemd service enabled and started successfully
- remote verification confirmed:
  service active
  TCP listener on `0.0.0.0:58477`
  `GET /v1/discovery` responding from another machine on the LAN
  `platform = linux`
  `capabilities = ["shutdown", "restart", "guard", "pairing", "discovery"]`
  active pairing code present after service restart

Purpose of this checkpoint:

- ready for a real Home Assistant-side discovery and pairing test against the Linux runtime

Follow-up result from the first live Home Assistant check:

- Linux discovery/pairing path appears to be working well enough for real use
- real power-off from Home Assistant against the Linux host was confirmed by the user
- the remaining gap is updating/reloading the Home Assistant integration build in use so the newer multiplatform metadata and UI behavior show correctly

## Beta 5 Release Prep 2026-04-25

Local release prep was moved forward for the next prerelease line.

Prepared target version:

- `v0.2.0-beta.5`

What was updated locally:

- version constants bumped to `0.2.0-beta.5` in:
  `agent_core/common.py`
  `custom_components/pc_power_free/manifest.json`
  `windows_agent/pc_power_tray.py`
  `windows_agent/setup_wizard_gui.py`
  `windows_agent/pcpowerfree-installer.nsi`
- root documentation and Spanish documentation updated to reflect:
  Windows and Linux support
  repository code targeting `v0.2.0-beta.5`
  `v0.2.0-beta.5` becoming the next planned prerelease at that time
  Linux still being experimental and source-based
- new release helper script added:
  `build-release-assets.ps1`
- new release notes draft added:
  `docs/RELEASE_DRAFT_v0.2.0-beta.5.md`

Intent for the next release:

- keep Windows installer assets
- keep the packaged Home Assistant integration zip
- add an experimental Linux source bundle as a release asset

Linux install documentation was also tightened after that prep:

- `README.md`
- `docs/README.es.md`
- `linux_agent/README.md`

Those Linux instructions now include:

- explicit Ubuntu or Debian commands
- installation under `/opt/pc-power-free`
- config path `/etc/pc-power-free/config.json`
- `systemd` enable and status commands
- verification commands with `curl` and `journalctl`
- note that the example service now runs the agent through `/opt/pc-power-free/.venv/bin/python`

## If Conversation Context Is Lost Again

Start from this understanding:

- This is not an Alexa skill project right now
- This is a Windows agent plus Home Assistant integration project
- Alexa is only expected to work through Home Assistant
- HACS submission has already been done with PR `hacs/default#7156`
- The active published prerelease is now `v0.2.0-beta.5`
- Home Assistant path is already considered validated on a real setup
- Linux discovery, pairing and shutdown are also already validated on a real Ubuntu machine
- The current longer-term engineering front after Linux is the DSM package scaffold and DSM privilege model

## DSM Scaffold Checkpoint 2026-04-26

The `dsm_package` placeholder was converted into a real initial DSM package scaffold.

What now exists in source form:

- builder script:
  `dsm_package/build-dsm-package.ps1`
- DSM package metadata template:
  `dsm_package/template/INFO.in`
- DSM privilege config:
  `dsm_package/template/conf/privilege`
- DSM lifecycle scripts:
  `dsm_package/template/scripts/`
- DSM runtime wrappers reusing the Linux agent:
  `dsm_package/payload/dsm_runtime/`

Important design decisions:

- DSM package versions need to stay numeric in `INFO`, so the builder maps upstream app version `0.2.0-beta.5` to DSM package version `0.2.0-0005`
- the package currently reuses `agent_core` plus `linux_agent`
- the package currently assumes `python3` exists on the NAS and that the required Python modules are available
- the package still does not claim SynoCommunity-ready status
- DSM shutdown and restart still need real privilege validation before they should be presented as safe NAS controls

Builder output verified locally:

- generated `package.tgz`
- generated `.spk` layout with:
  `INFO`
  `package.tgz`
  `scripts/`
  `conf/privilege`
  `PACKAGE_ICON.PNG`
  `PACKAGE_ICON_256.PNG`
  `LICENSE`
- icons verified as:
  `64x64`
  `256x256`
- final local artifact path:
  `dsm_package/dist/pcpowerfree-dsm-noarch-0.2.0-0005.spk`

What is still pending for DSM:

- real install test on DSM 7 hardware
- verification of runtime dependency strategy on DSM
- better DSM-facing setup UX than log and summary file output
- SynoCommunity `spksrc` packaging if the package moves from local scaffold to community distribution

## Hotfix Checkpoint 2026-04-29

Two post-`v0.2.0-beta.5` issues were identified and corrected after release testing.

### 1. Home Assistant integration source on GitHub was inconsistent

Symptom seen on a real Home Assistant boot:

- import failure:
  `ImportError: cannot import name 'STATUS_CAPABILITIES' from 'custom_components.pc_power_free.const'`

Root cause:

- the public GitHub source in `main` had a mixed integration state
- `api.py` expected the newer multiplatform constants and helpers
- but `const.py`, `config_flow.py`, `button.py`, `switch.py`, `sensor.py` and related files in the repo were still older versions

What was fixed in GitHub `main`:

- updated:
  `custom_components/pc_power_free/const.py`
  `custom_components/pc_power_free/button.py`
  `custom_components/pc_power_free/config_flow.py`
  `custom_components/pc_power_free/switch.py`
  `custom_components/pc_power_free/sensor.py`
  `custom_components/pc_power_free/strings.json`
  `custom_components/pc_power_free/translations/en.json`
  `custom_components/pc_power_free/translations/es.json`
- added:
  `custom_components/pc_power_free/device_info.py`
  `custom_components/pc_power_free/platforms.py`

Important nuance:

- the local regenerated integration ZIP was already correct
- the breakage affected installs pulling from the stale GitHub source
- release assets on GitHub may still need manual replacement or a new hotfix release

### 2. Windows setup EXE was missing `agent_core`

User-facing symptom:

- the Windows setup app failed on launch with:
  `ModuleNotFoundError: No module named 'agent_core'`

Root cause:

- `setup_wizard_gui.py` imports `network_info.py`
- `network_info.py` imports `agent_core.common`
- the PyInstaller build for the Windows desktop tools did not include the project root in analysis paths and did not force `agent_core.common` as a hidden import

What was fixed locally and in source:

- updated:
  `windows_agent/build-exe.ps1`
  `windows_agent/PCPowerAgent.spec`
  `windows_agent/PCPowerSetup.spec`
- added/updated:
  `windows_agent/PCPowerTray.spec`

Build packaging changes:

- PyInstaller now receives `--paths` pointing at the repo root
- PyInstaller now receives hidden import `agent_core.common`
- the tray build also keeps `pystray._win32` as a hidden import

Validation performed:

- rebuilt:
  `windows_agent/dist/PCPowerAgent.exe`
  `windows_agent/dist/PCPowerTray.exe`
  `windows_agent/dist/PCPowerSetup.exe`
  `windows_agent/dist/pcpowerfree-windows-x64-setup.exe`
- `PCPowerAgent.exe --help` works
- `PCPowerSetup.exe` launches without reproducing the original `agent_core` crash
- installer rebuild completed successfully

Practical consequence:

- source is now corrected
- local rebuilt Windows binaries are corrected
- if the public release assets still contain the older Windows build, they need to be manually re-uploaded or superseded by a new release

### 3. Bitdefender false positive during local Windows validation

What happened:

- Bitdefender flagged a PowerShell command line as malicious
- the command referenced a temporary file named:
  `pcpowerfree-test-config.json`

Important clarification:

- that specific command line did not come from the published app flow
- it matched an ad-hoc local validation command used during debugging
- no persistent temp config file was left behind afterwards

Preventive fix applied anyway:

- `windows_agent/network_info.py` no longer launches `powershell.exe` to detect the active adapter
- adapter detection now uses the native Windows IP Helper API via `GetAdaptersAddresses`

Validation:

- native adapter detection correctly resolved:
  `Ethernet`
  `192.168.100.193`
  `74:56:3C:BA:22:44`
- `PCPowerSetup.exe` and the installer were rebuilt locally after the change

Related build-system hardening:

- `windows_agent/build-exe.ps1` now fails fast if PyInstaller returns a non-zero exit code
- this avoids false "build completed" messages when an EXE is locked by a running process

## DSM Packaging Checkpoint 2026-05-04

The DSM scaffold was tightened so a real NAS test is now more reasonable.

What changed:

- `dsm_package/build-dsm-package.ps1` now vendors the Python packages `ifaddr` and `zeroconf` into the package payload under:
  `app/vendor/ifaddr`
  `app/vendor/zeroconf`
- vendoring strips platform-specific binary extensions such as `.pyd` and keeps the Python source fallback files
- `dsm_package/payload/dsm_runtime/init.sh` now exports:
  `PYTHONPATH=${APP_ROOT}/vendor:${APP_ROOT}`
- `dsm_package/payload/dsm_runtime/run-agent.sh` now exports the same `PYTHONPATH` before launching the Linux agent runtime

Why this matters:

- the earlier DSM scaffold effectively required the NAS to already have `ifaddr` and `zeroconf` installed in its Python environment
- the package now only depends on finding a usable `python3` binary on DSM
- that makes the first install test much closer to a real package scenario instead of a manual preconfigured NAS

What was validated locally:

- `dsm_package/build-dsm-package.ps1` rebuilt successfully
- `dsm_package/build/package.tgz` contains:
  `app/vendor/ifaddr`
  `app/vendor/zeroconf`
- final rebuilt artifact:
  `dsm_package/dist/pcpowerfree-dsm-noarch-0.2.0-0005.spk`

What is still not validated:

- actual install on DSM 7 hardware
- whether the discovered DSM Python binary is present by default on the target NAS or requires the Synology Python package to be installed first
- DSM privilege behavior for shutdown/restart
- any DSM-native setup UX beyond generated config and log output

## Beta 0.2.0-beta.6 Preparation Checkpoint 2026-05-05

Local source and release preparation moved on from the published `v0.2.0-beta.5` line toward `v0.2.0-beta.6`.

Key fixes prepared for that next beta:

- Home Assistant repair flow now updates an existing config entry when a device is re-paired after token rotation instead of aborting as already configured
- zeroconf discovery now follows the same repair path, so existing entries can refresh their token there too
- Home Assistant now reloads the config entry after learning new live metadata such as `platform` and `capabilities`, which fixes stale device models like `Linux host` after a DSM install
- subnet rediscovery in `custom_components/pc_power_free/api.py` no longer sends the stored `Authorization: Bearer ...` token to every candidate IP on the subnet; it now probes `/v1/discovery` without the token
- agent pairing now tracks failed attempts and blocks the temporary code after repeated invalid tries, reducing brute-force exposure for the 6-digit pairing code
- config and guard-state files are now persisted with best-effort private file permissions

Version and release preparation done locally:

- source version bumped to `0.2.0-beta.6` in:
  `agent_core/common.py`
  `custom_components/pc_power_free/manifest.json`
  `windows_agent/pcpowerfree-installer.nsi`
- release draft added:
  `docs/RELEASE_DRAFT_v0.2.0-beta.6.md`
- HACS and README docs updated to describe:
  published prerelease still being `v0.2.0-beta.5`
  repository code now targeting `v0.2.0-beta.6`
  DSM install/discovery/pairing now validated on DSM 7.2
  DSM shutdown/restart/wake still pending validation

Validation completed locally before release prep:

- `py -3 -m compileall agent_core custom_components/pc_power_free linux_agent windows_agent dsm_package/payload/dsm_runtime`
- regenerated release assets:
  `release_assets/pcpowerfree-home-assistant-integration.zip`
  `release_assets/pcpowerfree-linux-agent.tar.gz`
- regenerated DSM package:
  `dsm_package/dist/pcpowerfree-dsm-noarch-0.2.0-0006.spk`

Recommendation:

- `v0.2.0-beta.6` is reasonable as a new prerelease focused on DSM packaging, re-pairing stability, and security hardening
- DSM should still be labeled experimental in release notes until shutdown, restart, and wake are validated on real hardware

## Beta 0.2.0-beta.6 Published 2026-05-06

The `v0.2.0-beta.6` prerelease has now been published on GitHub with the current release assets attached.

Published state:

- repository `main` updated through commit `74ddcc5` - `Prepare v0.2.0-beta.6 release`
- tag published: `v0.2.0-beta.6`
- prerelease published:
  `https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.6`

Assets attached to the published prerelease:

- `pcpowerfree-windows-x64-setup.exe`
- `PCPowerAgent.exe`
- `PCPowerTray.exe`
- `PCPowerSetup.exe`
- `pcpowerfree-home-assistant-integration.zip`
- `pcpowerfree-linux-agent.tar.gz`
- `pcpowerfree-dsm-noarch-0.2.0-0006.spk`

Public-facing docs were updated to reflect that `beta.6` is the active published prerelease line while real-world validation is still pending for:

- `Alexa + Home Assistant`
- DSM shutdown
- DSM restart
- DSM wake
