# Cross-Platform Agent Plan

## Goal

Keep a single Home Assistant integration while allowing different local runtimes:

- Windows desktop app
- Linux agent
- DSM package

## Core rule

The user experience can change per operating system, but the contract with Home Assistant should stay aligned.

Shared externally:

- same `zeroconf` service type: `_pcpowerfree._tcp.local.`
- same pairing flow with temporary code
- same token-based API
- same core endpoints:
  - `GET /v1/discovery`
  - `POST /v1/pairing/exchange`
  - `GET /v1/status`
  - `POST /v1/power/shutdown`
  - `POST /v1/power/restart`
  - `GET/POST /v1/local/guard`

Different per platform:

- setup experience
- startup registration
- power commands
- firewall/system integration
- packaging

## Current structure

- `agent_core/`
  - shared HTTP server
  - config loading/saving
  - pairing code hashing/generation
  - guard-state persistence
  - zeroconf advertisement
  - platform adapter interface
- `windows_agent/`
  - Windows adapter
  - existing setup GUI
  - existing tray app
  - Windows-specific network detection
- `linux_agent/`
  - Linux adapter
  - Linux network detection
  - CLI setup flow
  - example `systemd` unit
- `dsm_package/`
  - package planning area for Synology-specific work

## Why DSM is not just "Linux packaging"

DSM can reuse most of the Linux-side runtime shape, but it still needs its own work for:

- `.spk` package layout
- DSM 7 privilege model
- package lifecycle scripts
- install/start/stop integration
- possible DSM-specific setup flow

So DSM should reuse the shared protocol and as much Linux runtime logic as possible, but not pretend to be the same product surface.

## Recommended next implementation steps

1. Extend Home Assistant to read optional `platform` and `capabilities` metadata from the agent.
2. Test the new Linux runtime end-to-end on a real machine.
3. Improve Linux setup UX if needed:
   - small local web UI
   - or richer CLI flow
4. Start DSM packaging on top of the shared agent core.
5. Validate how DSM 7 can safely expose shutdown/restart without breaking package privilege rules.
