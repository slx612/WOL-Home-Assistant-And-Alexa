# Existing-pairing TLS migration

This is an application-specific migration binding using standard HMAC-SHA-256
and TLS certificate pinning, not a new cryptographic primitive or a claim of an
independently audited protocol. It needs no Internet service, CA, account or new
pairing code. It applies only to entries that have an existing API token but no
stored certificate fingerprint. Existing pins are never silently overwritten.

## Exchange

1. HA reads the peer's actual DER certificate during a TLS handshake without
   credentials. Discovery on that same pinned certificate selects the expected
   machine ID (or the MAC for older entries). Public identity fields alone do
   not establish trust.
2. HA creates a fresh random 32-byte nonce and posts its lowercase hexadecimal
   representation to `POST /v1/pairing/upgrade`, pinning that observed certificate.
   The request contains no Authorization header, API token or pairing code.
3. The agent restricts access to its allowed networks and TLS connections. It
   validates the nonce and returns only `{"proof":"<64 lowercase hex chars>"}`.
   The proof is HMAC-SHA-256 keyed by the existing UTF-8 API token over these
   concatenated bytes:

   ```text
   ASCII("pc-power-free/tls-upgrade/v1") || 0x00 || nonce[32] || SHA256(server_certificate_DER)[32]
   ```

   The certificate digest is loaded from the agent's own configured TLS identity
   at startup. A client-supplied fingerprint is never used in the proof.
4. HA computes the same proof with its saved token and compares it in constant
   time. Only then may it send the normal bearer token over the pinned TLS
   connection. A valid proof for another certificate or another nonce is rejected.
5. HA saves the fingerprint in the existing config entry. Normal status polling
   persists it after authenticated status succeeds; verified mDNS discovery can
   also complete migration. Subsequent connections use the saved pin. The agent
   does not rotate the token, consume a code or alter its config during migration,
   so multiple already-paired HA instances can update independently.

The building blocks follow Python's [HMAC API](https://docs.python.org/3/library/hmac.html)
and aiohttp's [SHA-256 certificate pinning](https://docs.aiohttp.org/en/stable/client_advanced.html#example-verify-certificate-fingerprint).
Entries are updated through [Home Assistant's config-entry lifecycle](https://developers.home-assistant.io/docs/config_entries_index/).

## Failure and limits

- There is no HTTP fallback. An old/offline/unverifiable agent leaves migration
  pending and retries on subsequent polling/discovery without deleting the entry
  or asking for a new code. WOL still uses the saved MAC/broadcast settings.
- An already-pinned certificate mismatch still rejects credential delivery.
  Recovery after deliberate identity replacement is an explicit repair operation.
- The published default is a randomly generated long API token. A manually
  chosen weak token can be guessed offline from a proof; use the generated secret.
  A previously stolen beta.6 token already compromises that pairing. This update
  cannot retroactively revoke it while preserving that same secret.
- The nonce prevents replay for a different attempt. Binding to the actual peer
  certificate prevents relaying a real agent's proof onto an attacker's different
  TLS identity. An attacker can still block traffic or disrupt discovery.
- First-time pairing remains a separate trusted-LAN, fingerprint-comparison flow.
  This migration is not a replacement for securing first enrollment or local
  file permissions. Keep the token/private key secret and do not expose the agent
  to the Internet.

## Compatibility tests

`tests/test_published_upgrade.py` loads the actual Python code at Git tag
`v0.2.0-beta.6` and runs old/new clients and agents on loopback with fake power
actions. It checks HA-first, Windows-first and multiple existing clients. Fetch
that tag before running the tests; without it these specific tests report a skip.
Other tests cover wrong secrets, machine mismatch, altered/replayed proofs,
unchanged configuration, persisted fingerprints and installer update dispatch.
HA lifecycle tests use doubles, not a real HA instance. Real installer and
hardware acceptance checks remain in [the upgrade guide](UPGRADE-beta.7.md).
