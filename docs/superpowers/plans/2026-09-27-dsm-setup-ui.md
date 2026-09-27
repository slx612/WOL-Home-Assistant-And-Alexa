# WakeLink DSM Setup UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An administrator opens WakeLink in DSM, checks agent status, and obtains a temporary Home Assistant pairing code without SSH, while existing pairings survive the upgrade.

**Architecture:** DSM serves a small packaged page and same-origin CGI. The CGI forwards only status and pairing requests to new loopback-only routes on the existing TLS agent; the agent verifies DSM administrator authentication and modifies its own protected config. No browser access to the agent token or private key, and no new public listener.

**Tech Stack:** DSM 7 `.spk`, Python 3 standard library, shell package scripts, vanilla HTML/CSS/JavaScript, `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-27-dsm-setup-ui-design.md`

## Global Constraints

- Keep the internal package ID `pcpowerfree` and stored config/TLS identity; visible name is WakeLink.
- ES and EN UI; only status and pairing-code generation, never NAS power buttons.
- Pairing code is six digits, expires after ten minutes, and does not rotate existing credentials.
- Install/test only on DSM test VM `.167`; do not touch `.177` or send NAS power commands.
- Never make config, token, private key, or DSM cookie web-readable or log them.

## Review Focus

- Missing, expired, or non-admin DSM session must fail closed: Task 1 and 2 tests.
- Direct LAN request to a DSM setup route must be denied: Task 2 test.
- Cross-site form POST without WakeLink's exact header must not generate a code: Task 2 and 3 tests.
- Re-pairing must preserve token, machine ID, certificate, key, and existing HA connection: Task 2 and 4 tests.
- Unavailable agent or network detection must produce a useful UI error, not a blank page: Task 3 and 4 tests.

---

### Task 1: DSM Authentication Feasibility

**Files:** Create `dsm_package/payload/dsm_runtime/setup_auth.py`; test in `tests/test_dsm_setup.py`.

**Interfaces:** Produce `authenticate_admin(cookie: str, remote_addr: str, server_addr: str) -> bool`, with fixed executable path `/usr/syno/synoman/webman/modules/authenticate.cgi` and an administrator-group check. Reject missing/invalid values and fail closed on subprocess errors/timeouts. No raw cookie in errors.

- [ ] Write tests for no cookie, invalid/expired session, non-admin user, admin user, and subprocess failure; run `python -m unittest tests.test_dsm_setup -v` and confirm failures.
- [ ] Implement the minimal function using subprocess argument arrays and DSM's authenticated username; run the tests and confirm they pass.
- [ ] On `.167`, inspect (read-only) the authenticator and group-check tools under the package account; if they are not usable, stop and revise the design before building or installing anything.
- [ ] Commit only this task's source and tests.

### Task 2: Agent Setup Routes

**Files:** Modify `agent_core/common.py`, `linux_agent/pc_power_agent.py`; extend `tests/test_dsm_setup.py`.

**Interfaces:** `DsmPlatformAdapter.authenticate_setup_request(cookie: str, remote_addr: str, server_addr: str) -> bool` delegates to Task 1. Add `GET /v1/dsm/setup` and `POST /v1/dsm/pairing-code` only for DSM and loopback callers. The POST requires `X-WakeLink-Action: pair`; it returns the new code once and persists pairing fields under the existing config lock.

- [ ] Write HTTP tests against the real loopback test server for non-DSM platform, non-loopback source, missing/non-admin session, missing action header, successful status, and successful code generation; verify each new test fails first.
- [ ] Implement route dispatch and adapter hook; reuse existing `generate_pairing_code`, `hash_pairing_code`, and `persist_config`, without changing power routes.
- [ ] Run `python -m unittest tests.test_dsm_setup tests.test_api tests.test_runtime -v`; check config/token/machine ID and TLS file hashes in the tests.
- [ ] Commit only this task's source and tests.

### Task 3: DSM Page and Package

**Files:** Create `dsm_package/payload/ui/config`, `index.html`, `style.css`, `app.js`, `setup.cgi`; modify `dsm_package/template/INFO.in`, `dsm_package/build-dsm-package.ps1`, `dsm_package/payload/dsm_runtime/init.sh`, and `dsm_package/README.md`; extend `tests/test_dsm_setup.py`.

**Interfaces:** DSM `dsmuidir="ui"` and `dsmappname="com.wakelink.Setup"` point **Open** and the DSM menu at `3rdparty/pcpowerfree/index.html`. `setup.cgi?action=status` accepts GET and `setup.cgi?action=pair` accepts POST only. CGI forwards DSM session context to Task 2 over localhost HTTPS, validates the agent against `target/ui/agent-cert.pem` (public certificate, mode `0644`), and returns no-store JSON. UI shows status/network, ES/EN toggle, code/copy button, and brief HA steps.

- [ ] Write failing tests for launcher metadata, `.spk` UI contents, CGI route allowlist, POST header, non-cacheable code response, and no power-action buttons.
- [ ] Implement the smallest static UI and CGI; copy only the public agent certificate to the UI-accessible path during setup, never config or key. Show a clear offline/authentication error.
- [ ] Run `python -m unittest tests.test_dsm_setup -v`, `git diff --check`, and shell syntax checks for modified scripts.
- [ ] Commit only this task's source, docs, and tests.

### Task 4: Build, Upgrade, and VM Verification

**Files:** Rebuild `dsm_package/dist/*.spk` and update release notes/docs only if the VM test succeeds. Do not change HA or other platforms to accommodate an unverified DSM package.

**Interfaces:** DSM package version must exceed the version actually installed on `.167`; the internal package ID and state path stay unchanged. If `.167` already has `0.2.0-0012`, add a DSM-only revision argument to the builder and use `0.2.0-0013`, without changing the shared agent version just to force an upgrade.

- [ ] Inspect the current package/version and config/cert/key hashes on `.167`; back up those files and the previous installer before installation. Verify backup contents without printing secrets.
- [ ] Build the new `.spk`, inspect archive metadata/UI/scripts, and run relevant local tests. If packaging or authentication checks fail, stop.
- [ ] Install only on `.167`; confirm DSM **Open** and menu icon, ES/EN rendering, status, code generation, and Home Assistant's pre-existing online pairing. Do not send shutdown/restart commands.
- [ ] Compare config identity and TLS hashes with the backup; report any intentional pairing-code-field change separately. If upgrade fails, stop and ask before recovery.
- [ ] Commit tested documentation/artifacts only after verification; keep the build labeled beta until the UI and pairing flow pass.
