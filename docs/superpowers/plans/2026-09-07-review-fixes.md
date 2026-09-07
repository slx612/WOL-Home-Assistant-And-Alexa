# Review Fixes Implementation Plan

**Goal:** Correct the reproduced beta.6 defects without external services or real power operations during testing.
**Spec:** docs/REVIEW_2026-09-07.md
**Architecture:** Preserve the shared runtime and HA entities. Use TLS with a persistent self-signed certificate and SHA-256 pinning, never downgrade to HTTP. First enrollment is trust-on-first-use on a trusted LAN. Existing beta.6 entries automatically authenticate the new certificate using their saved secret, a fresh nonce and HMAC-SHA-256, without re-pairing. Keep identifiers and automations. This supersedes the initial breaking-upgrade decision.
**Tech Stack:** Python stdlib, aiohttp, cryptography for certificate creation (native OpenSSL fallback on DSM), Windows Task Scheduler, NSIS.

- [x] Shared runtime: regression tests, atomic state, fail-closed guard, serialized pairing, bounded HTTP, TLS.
- [x] HA: pinned transport, bounded discovery, error classification, managed reload, migration/reauth, connection settings in data only, agent power defaults.
- [x] Windows: regression tests, unlimited/recoverable task, checked restart/removal, UAC launch, uninstall stop, 64-bit uptime, local TLS client.
- [x] DSM: propagate configuration failures; retain explicit experimental power-support limitation.
- [x] Verify tests and packaging, update English/Spanish upgrade notes; no claim of real HA/DSM or power-cycle validation.
- [x] Correct upgrade compatibility: preserve published Windows settings without repeating setup, persist migrated HA trust, and test both update orders against actual beta.6 Python code.

Evidence for the original review: 35 checks. The compatibility correction expands this suite; see docs/VALIDATION-beta.7.md for the latest run, artifact verification and exact limits.

Work in the visible workspace. The clean Git checkout is `.repo_push_beta6`; synchronize only changed product files after comparing the baseline. Do not commit, publish, install, or execute real power commands as part of this correction pass.
