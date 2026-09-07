# Published-version fixtures

`beta6-config.json` uses the schema in `agent_core/common.py` at published tag
`v0.2.0-beta.6` (`74ddcc5`). Credentials and identity are synthetic, networking
is loopback-only, the old code has been consumed, and shutdown preferences are
non-default to detect accidental resets. Never use this token for an installation.

Windows upgrade tests preserve the file byte-for-byte. TLS migration tests use
the same persisted token and machine ID, without generating a pairing code.
