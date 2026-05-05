#!/bin/sh

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
APP_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
VAR_DIR="${SYNOPKG_PKGVAR:-${APP_ROOT}/../var}"
CONFIG_PATH="${VAR_DIR}/config.json"
PYTHON_FINDER="${SCRIPT_DIR}/find-python.sh"
INIT_SCRIPT="${SCRIPT_DIR}/init.sh"
VENDOR_PATH="${APP_ROOT}/vendor"

if [ ! -x "${INIT_SCRIPT}" ]; then
    echo "Missing init script: ${INIT_SCRIPT}" >&2
    exit 1
fi

"${INIT_SCRIPT}" --ensure-config >/dev/null

PYTHON_BIN="$("${PYTHON_FINDER}")" || exit 1
PYTHONPATH="${VENDOR_PATH}:${APP_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONPATH
PC_POWER_PLATFORM_ID="dsm"
export PC_POWER_PLATFORM_ID

exec "${PYTHON_BIN}" "${APP_ROOT}/linux_agent/pc_power_agent.py" --config "${CONFIG_PATH}"
