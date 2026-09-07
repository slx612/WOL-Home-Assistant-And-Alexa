#!/bin/sh

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
APP_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
VAR_DIR="${SYNOPKG_PKGVAR:-${APP_ROOT}/../var}"
CONFIG_PATH="${VAR_DIR}/config.json"
SUMMARY_PATH="${VAR_DIR}/setup-output.txt"
PYTHON_FINDER="${SCRIPT_DIR}/find-python.sh"
VENDOR_PATH="${APP_ROOT}/vendor"

mkdir -p "${VAR_DIR}"
umask 077

fail() {
    echo "$1" >&2
    exit 1
}

if [ ! -x "${PYTHON_FINDER}" ]; then
    fail "Missing python finder script: ${PYTHON_FINDER}"
fi

PYTHON_BIN="$("${PYTHON_FINDER}")" || fail "python3 was not found on this DSM host."

PYTHONPATH="${VENDOR_PATH}:${APP_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONPATH

"${PYTHON_BIN}" -c "import ifaddr, zeroconf" >/dev/null 2>&1 || fail "python3 is available, but bundled modules ifaddr and zeroconf could not be imported."

ensure_config() {
    if [ -f "${CONFIG_PATH}" ]; then
        echo "Existing config detected at ${CONFIG_PATH}"
        "${PYTHON_BIN}" -c 'import sys; from pathlib import Path; from agent_core.common import load_config; from agent_core.tls import create_server_context; p=Path(sys.argv[1]); load_config(p); create_server_context(p.parent)' "${CONFIG_PATH}"
        return $?
    fi

    "${PYTHON_BIN}" "${APP_ROOT}/linux_agent/setup_cli.py" --config "${CONFIG_PATH}" >"${SUMMARY_PATH}" 2>&1
    result=$?
    cat "${SUMMARY_PATH}"
    [ "${result}" -eq 0 ] || return "${result}"
    "${PYTHON_BIN}" -c 'import sys; from pathlib import Path; from agent_core.common import load_config; load_config(Path(sys.argv[1]))' "${CONFIG_PATH}"
}

case "$1" in
    --check)
        [ -f "${CONFIG_PATH}" ] || fail "Config file missing at ${CONFIG_PATH}"
        ensure_config || fail "Invalid agent configuration or TLS identity."
        echo "python3 and DSM agent config are available."
        ;;
    --ensure-config|"")
        ensure_config || fail "Initial agent configuration failed. See setup-output.txt."
        ;;
    *)
        fail "Unknown argument: $1"
        ;;
esac

exit 0
