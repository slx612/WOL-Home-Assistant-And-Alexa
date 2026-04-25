# Linux Agent

This directory contains the experimental Linux runtime for `PC Power Free`.

Current scope:

- shared HTTP API with the Windows agent
- same `zeroconf` service type and pairing flow
- CLI setup that generates `config.json` and a temporary pairing code
- example `systemd` unit for persistent installs

Current limitations:

- no desktop GUI yet
- no tray app
- no distro-specific installer yet
- DSM packaging is not solved here; that will build on this Linux runtime with Synology-specific packaging and privilege work

Quick install on Ubuntu or Debian:

```bash
sudo mkdir -p /opt/pc-power-free /etc/pc-power-free
sudo tar -xzf pcpowerfree-linux-agent.tar.gz -C /opt/pc-power-free
sudo python3 -m venv /opt/pc-power-free/.venv
sudo /opt/pc-power-free/.venv/bin/python -m pip install --upgrade pip ifaddr zeroconf
sudo /opt/pc-power-free/.venv/bin/python /opt/pc-power-free/linux_agent/setup_cli.py --config /etc/pc-power-free/config.json
sudo cp /opt/pc-power-free/linux_agent/pcpowerfree-agent.service /etc/systemd/system/pcpowerfree-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now pcpowerfree-agent.service
sudo systemctl status pcpowerfree-agent.service --no-pager
```

What the setup step does:

- detects the active adapter, current IP, MAC, subnet and Wake-on-LAN broadcast
- writes `/etc/pc-power-free/config.json`
- generates a temporary 6-digit pairing code for Home Assistant

Useful follow-up commands:

```bash
curl http://127.0.0.1:58477/v1/discovery
sudo journalctl -u pcpowerfree-agent.service -n 50 --no-pager
sudo systemctl restart pcpowerfree-agent.service
sudo /opt/pc-power-free/.venv/bin/python /opt/pc-power-free/linux_agent/setup_cli.py --config /etc/pc-power-free/config.json
```

Notes:

- the default local port is `58477`
- rerun `setup_cli.py` if you need a fresh pairing code
- if you use `ufw`, allow at least `58477/tcp`
- the shipped `systemd` unit expects the files to live under `/opt/pc-power-free`
