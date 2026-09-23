# Windows beta.8 local preview validation

**Later finding:** the user installed beta.8 and reported two unwanted desktop shortcuts plus a certificate permission error on both. The source tests below missed that Windows ACL behavior. Beta.8 must not be treated as release-ready; see [beta.9](WINDOWS-beta.9.md).

Date: 2026-09-23. Scope: Windows desktop, tray and installer only.
Not published. Not installed over the user's existing installation.

## Verified locally

- `python -m unittest discover -s tests -q`: 102 tests passed on Windows/Python 3.13.
- Temporary Tk widget tests cover first run, existing configuration, language persistence, explicit credential generation, narrow layout and protected settings.
- A real TLS loopback agent with a fake power adapter validates desktop status and protection requests without any OS power action.
- Existing published beta.6 protocol migration tests still pass. Tests preserve token, machine identity, custom port, guard and TLS identity. No new pairing is required by the upgrade path.
- GitHub's live API returns beta.7 and its installer; the shared checker correctly orders beta.7 after beta.5 and before this local beta.8.
- Update regressions cover optional-cache permission failure, explicit manual results, offline/timeouts, available installers, repeated checks and language changes. This reproduces code-level failure paths, not the user's original native tray click.
- All three PyInstaller executables built successfully. Their embedded application/core/TLS code matches the source; new UI/update/preferences modules, icon and version resources are included.
- All three application executable manifests use `asInvoker`; the NSIS installer requires administrator access. Protected operations explicitly request elevation.
- Packaged setup's read-only `--upgrade-existing --config <nonexistent-test-path>` probe returned 3 and did not create a configuration file.
- NSIS installer compiled without warnings. Its extracted executables match the verified build byte-for-byte.
- `git diff --check` passed. Line-ending conversion notices are not whitespace errors.

## Still pending

- Real in-place installation from the user's beta.5, and separate beta.6/beta.7 Windows installer baselines. There is no beta.5 Git tag available locally or on the remote to run the exact published-source migration suite against it.
- Human visual review at 100/150/200 percent scaling, multiple monitors, a standard-user account and alternate administrator credentials. Layout/widget tests do not substitute for this.
- A real native-tray update check after installing, plus manual network-failure testing.
- Physical Wake-on-LAN, shutdown/restart and complete Alexa/Matter pairing. Matterbridge configuration is deliberately unchanged by this work.
- Trusted code signing. The preview remains unsigned; neither its checksum nor successful tests remove SmartScreen warnings.
- Linux/DSM/Home Assistant package rebuild and public release/CI. Those artifacts were not rebuilt or published by this Windows-only task. Use `python tests/verify_packages.py --windows-only` for this preview; full multi-platform archive parity requires rebuilding all release assets.

Manual installation and smoke checklist: [Windows beta.8](WINDOWS-beta.8.md).
