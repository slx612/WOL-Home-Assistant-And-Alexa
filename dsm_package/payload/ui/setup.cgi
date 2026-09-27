#!/bin/sh

PATH=/bin:/usr/bin:/usr/local/bin
export PATH
PYTHON_BIN="$(command -v python3)"
if [ -z "${PYTHON_BIN}" ]; then
    printf 'Status: 503 Service Unavailable\r\nContent-Type: application/json\r\nCache-Control: no-store\r\n\r\n{"error":"Python 3 unavailable"}'
    exit 0
fi
exec "${PYTHON_BIN}" "$(dirname "$0")/setup_cgi.py"
