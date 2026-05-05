PC Power Free DSM package scaffold

This package reuses the Linux runtime and generates its config inside:

  /var/packages/pcpowerfree/target/var/config.json

If initial setup succeeds, the generated pairing summary is written to:

  /var/packages/pcpowerfree/target/var/setup-output.txt

Current limitations:

- this package scaffold assumes python3 is available on the NAS
- ifaddr and zeroconf must be available for the runtime to start
- shutdown and restart behavior still needs DSM-specific privilege validation

For packaging work only. Not yet a SynoCommunity-ready package.
