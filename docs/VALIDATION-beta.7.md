# Beta.7 local validation

Date: 2026-09-07. Prepared on Windows 11 x64 / Python 3.13.2.
Git base: `865f0933a1fa9f6587355cade291f426a691460a`.
Prepared on branch `fix/review-beta7`. This report records local pre-publication verification; publication and CI status are tracked on the [release page](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.7) and repository Actions page.

## Verified

- 56 automated checks pass with `python -m unittest discover -s tests -v`, including the published-baseline tests (no skips on this Windows run).
- The actual beta.6 Python agent/client loaded from Git tag `v0.2.0-beta.6` is exercised on loopback: HA-first, Windows-first and multiple existing clients all recover without a new pairing code or rotated token. Temporary command adapters never control the real OS.
- Upgrade security cases cover wrong secrets, a different machine, invalid nonces, replayed proofs, proofs for a different certificate, absence of Authorization during the upgrade exchange and preservation of an existing certificate pin. HA contract tests verify persistence into the same entry and no repeated migration on subsequent refreshes.
- Windows upgrade tests preserve published-schema config and guard bytes exactly, preserve an existing TLS identity, retain disabled startup, reject corrupt configuration rather than generating credentials, and dispatch existing installations without the GUI. The native task calls are mocked.
- Actual loopback HTTPS exchanges cover pairing, token use, power defaults, guard rejection, expired/blocked codes, address recovery, wrong-certificate rejection and OS-command error classification. Power actions use a fake adapter.
- Guard/pairing concurrency, atomic-write failure and invalid body lengths are checked. Scans have bounded workers/address counts. The WOL packet is checked with a mocked UDP socket.
- HA flow/lifecycle contract tests cover reauthentication, entry preservation, migration, rejecting a different device, options and managed reload. They do not run Home Assistant itself.
- Windows tests mock task installation and UAC. Read-only native Task Scheduler settings report `ExecutionTimeLimit=PT0S`, both battery restrictions false, three retries and a one-minute retry interval. No task was registered.
- DSM failure propagation is exercised in a POSIX shell fragment. Shell scripts and PowerShell files parse successfully.
- All three Windows executables and the NSIS installer build successfully. `PCPowerAgent.exe --help` exits successfully without starting the service.
- `python tests/verify_packages.py` verifies all 16 integration ZIP files, nine Linux-bundle files, six DSM Python source files and the DSM runtime scripts against current sources. It compares embedded code in the three executables with the source, verifies TLS/crypto inclusion and their elevation manifests, and checks the Setup task script is bundled.
- The installer was extracted, not executed. Its three executable hashes and task-script hash match the rebuilt files.
- Ruff checks F821/F822/F823/F811 pass. This is a selected correctness check, not a claim that every style rule passes.

## Not Verified

No real PC was shut down, restarted or woken. No Windows installation/uninstallation, long-running task, battery transition, real HA instance, Alexa route, Linux service or DSM power action was tested in this pass. The old/new protocol tests do not substitute for installing over beta.6 on a real machine. CI fetches the published tag for upgrade tests; its remote results are separate from this local report. The installer is not code-signed.

First enrollment requires a trusted LAN and comparing the displayed certificate fingerprint. It is not a password-authenticated key exchange: entering the code without comparing fingerprints does not protect against an active first-enrollment impersonator. After pairing, TLS pinning protects subsequent token delivery.

Existing beta.6 pairings instead use the saved long-lived secret to authenticate the new certificate automatically. This application-specific HMAC/TLS binding has regression tests but no independent cryptographic audit. Its assumptions and limits, including already-compromised or weak old tokens, are documented in [TLS migration](TLS-MIGRATION.md). Both components must be updated; temporary unavailability between those updates is expected, not a lost pairing.

Remaining improvements and the real-device checklist are listed in [the upgrade guide](UPGRADE-beta.7.md). The old console-only Windows setup wizard is not covered by the updated GUI installation path. DSM privileged shutdown/restart remains experimental rather than being silently granted root access.
