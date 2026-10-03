#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VERSION=$(sed -n 's/^AGENT_VERSION = "\([^"]*\)"/\1/p' "$ROOT/agent_core/common.py")
[ -n "$VERSION" ] || { echo "Cannot read WakeLink version" >&2; exit 1; }
DEB_VERSION=$(printf '%s' "$VERSION" | sed 's/-beta\./~beta/')
OUTPUT=${1:-"$ROOT/release_assets"}
mkdir -p "$OUTPUT"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT
chmod 0755 "$STAGE"

install -d "$STAGE/DEBIAN" "$STAGE/opt/pc-power-free/agent_core" \
    "$STAGE/opt/pc-power-free/linux_agent" "$STAGE/usr/lib/wakelink" \
    "$STAGE/usr/lib/systemd/system" "$STAGE/usr/share/applications" \
    "$STAGE/usr/share/icons/hicolor/256x256/apps"
cp "$ROOT/agent_core/"*.py "$STAGE/opt/pc-power-free/agent_core/"
cp "$ROOT/linux_agent/"*.py "$STAGE/opt/pc-power-free/linux_agent/"
chmod 0644 "$STAGE/opt/pc-power-free/agent_core/"*.py "$STAGE/opt/pc-power-free/linux_agent/"*.py
install -m 0644 "$ROOT/linux_package/pcpowerfree-agent.service" \
    "$STAGE/usr/lib/systemd/system/pcpowerfree-agent.service"
install -m 0755 "$ROOT/linux_package/setup-helper.sh" "$STAGE/usr/lib/wakelink/setup-helper"
install -m 0644 "$ROOT/linux_package/wakelink.desktop" "$STAGE/usr/share/applications/wakelink.desktop"
install -m 0644 "$ROOT/custom_components/pc_power_free/brand/icon.png" \
    "$STAGE/usr/share/icons/hicolor/256x256/apps/wakelink.png"
install -m 0755 "$ROOT/linux_package/postinst" "$STAGE/DEBIAN/postinst"
install -m 0755 "$ROOT/linux_package/prerm" "$STAGE/DEBIAN/prerm"

cat > "$STAGE/DEBIAN/control" <<EOF
Package: wakelink
Version: $DEB_VERSION
Section: utils
Priority: optional
Architecture: all
Maintainer: WakeLink Contributors <noreply@github.com>
Depends: python3 (>= 3.10), python3-tk, python3-ifaddr, python3-zeroconf, python3-cryptography, pkexec, systemd
Description: Local WakeLink agent and graphical setup for Ubuntu
 Turn this computer on through Wake-on-LAN and control shutdown from
 Home Assistant. The desktop app guides pairing without a terminal.
EOF

dpkg-deb --build --root-owner-group "$STAGE" "$OUTPUT/WakeLink-Ubuntu-$VERSION.deb"
