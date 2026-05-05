#!/bin/sh

find_with_command() {
    command -v "$1" 2>/dev/null || true
}

for candidate in \
    "${SYNOPKG_PKGDEST}/python/bin/python3" \
    "/var/packages/Python3/target/usr/local/bin/python3" \
    "/var/packages/Python3.11/target/usr/local/bin/python3.11" \
    "/usr/local/bin/python3" \
    "/usr/bin/python3" \
    "/bin/python3" \
    "$(find_with_command python3)"
do
    if [ -n "${candidate}" ] && [ -x "${candidate}" ]; then
        echo "${candidate}"
        exit 0
    fi
done

exit 1
