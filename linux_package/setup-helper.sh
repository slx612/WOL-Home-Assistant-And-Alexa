#!/bin/sh
set -eu

APP=/opt/pc-power-free
CONFIG=/etc/pc-power-free/config.json
SERVICE=pcpowerfree-agent.service

if [ "$(/usr/bin/id -u)" -ne 0 ]; then
    echo "Administrator permission is required." >&2
    exit 1
fi

case "${1:-}" in
    enable)
        if [ -f "$CONFIG" ]; then
            /usr/bin/python3 - "$CONFIG" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "/opt/pc-power-free")
from agent_core.common import load_config
from agent_core.tls import create_server_context
config = Path(sys.argv[1])
load_config(config)
create_server_context(config.parent)
PY
        else
            /usr/bin/install -d -m 0700 /etc/pc-power-free
            /usr/bin/python3 "$APP/linux_agent/setup_cli.py" --config "$CONFIG"
        fi
        /usr/bin/chmod 0700 /etc/pc-power-free
        /usr/bin/chmod 0600 "$CONFIG" /etc/pc-power-free/agent-key.pem
        /usr/bin/systemctl daemon-reload
        /usr/bin/systemctl enable "$SERVICE"
        /usr/bin/systemctl restart "$SERVICE"
        ;;
    pair)
        [ -f "$CONFIG" ] || { echo "Enable WakeLink first." >&2; exit 1; }
        /usr/bin/python3 "$APP/linux_agent/setup_cli.py" --config "$CONFIG" --pairing-only
        ;;
    update)
        /usr/bin/python3 "$APP/linux_agent/update_install.py"
        ;;
    *)
        echo "Usage: setup-helper enable|pair|update" >&2
        exit 2
        ;;
esac
