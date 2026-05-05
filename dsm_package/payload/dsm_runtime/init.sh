#!/bin/sh

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
APP_ROOT="$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)"
VAR_DIR="${SYNOPKG_PKGVAR:-${APP_ROOT}/../var}"
CONFIG_PATH="${VAR_DIR}/config.json"
SUMMARY_PATH="${VAR_DIR}/setup-output.txt"
PYTHON_FINDER="${SCRIPT_DIR}/find-python.sh"
VENDOR_PATH="${APP_ROOT}/vendor"

mkdir -p "${VAR_DIR}"

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
        return 0
    fi

    "${PYTHON_BIN}" "${APP_ROOT}/linux_agent/setup_cli.py" --config "${CONFIG_PATH}" | tee "${SUMMARY_PATH}"
}

case "$1" in
    --check)
        [ -f "${CONFIG_PATH}" ] || fail "Config file missing at ${CONFIG_PATH}"
        echo "python3 and DSM agent config are available."
        ;;
    --ensure-config|"")
        ensure_config
        ;;
    *)
        fail "Unknown argument: $1"
        ;;
esac

exit 0
