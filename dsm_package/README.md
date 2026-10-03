# WakeLink DSM package / Paquete DSM

**For installation, use [English](../docs/INSTALL_DSM.en.md) or [Español](../docs/INSTALL_DSM.es.md).** This file describes the package, not a second user setup route.

**Para instalar, sigue [English](../docs/INSTALL_DSM.en.md) o [Español](../docs/INSTALL_DSM.es.md).** Aquí se describe el paquete, no otro recorrido de instalación.

## Current design / Diseño actual

- Visible name: **WakeLink**. Internal package ID: `pcpowerfree`; integration domain: `pc_power_free`. These IDs and stored identity are retained for upgrades.
- Opens a window inside the HTTPS DSM desktop. Uses the existing administrator session; hiding the launcher is not an access-control mechanism. Backend requests must authenticate and check administrator membership.
- The agent uses the shared runtime and runs as a package user, **not root**. The UI exposes status and pairing; power actions come from the paired Home Assistant integration.
- Initial shutdown/restart authorization uses DSM's native password confirmation. WakeLink does not store the password. A disabled, non-repeating task runs the fixed protected helper once, then is removed.
- Only normal, immediate `synoshutdown --shutdown` and `synoshutdown --reboot` are granted. No shell, arbitrary root command, forced shutdown or delay.
- Setup depends on DSM's installed native client interfaces. Future DSM versions need regression testing; this package is not distributed by SynoCommunity.

Nombre visible **WakeLink**; se conservan los identificadores internos y los datos para actualizar. La ventana usa la sesión administradora DSM; el servidor comprueba esa sesión, no se fía de ocultar el icono. El agente no es root. El permiso inicial confirma mediante el diálogo DSM y solo permite apagado/reinicio normales. No guarda la contraseña ni autoriza una consola. Se deben repetir pruebas de compatibilidad tras cambios DSM.

## v1.0.0

DSM package **1.0.0-0001**, app **1.0.0**, includes guided limited permission and the Package Center catalog. The beta.13-to-1.0 upgrade on DSM 7.2 preserved identity, guard state and power grant. Earlier guided fresh installation and controls were reported working by the tester. Other models/versions, physical NAS wake and downgrade remain unvalidated. See [release evidence](../docs/RELEASE_v1.0.0.md).

El paquete **1.0.0-0001**, app **1.0.0**, incluye permiso limitado guiado y catálogo. Actualizar beta.13 a 1.0 en DSM 7.2 conservó identidad, protección y permiso. El usuario había confirmado instalación limpia y controles. Otros modelos/versiones, encendido físico y vuelta atrás no están validados; consulta las [pruebas de versión](../docs/RELEASE_v1.0.0.md).

## Build / Compilar

From the repository root on Windows / Desde la raíz del repositorio en Windows:

```powershell
.\dsm_package\build-dsm-package.ps1 -DsmRevision 1
```

The builder produces `dsm_package/dist/pcpowerfree-dsm-noarch-1.0.0-0001.spk`. Increase the revision for later DSM-only changes within the same app version. Python 3 must be available on the target NAS; `ifaddr` and `zeroconf` are bundled. The package includes metadata, lifecycle scripts, desktop assets and the protected `conf/power_permissions.py` helper.

The package source generator is `build_repository.py`; publication steps and validation boundaries are in [the release checklist](../docs/HACS_PUBLISHING.md#dsm-package-source). Keep quick install/upgrade disabled for DSM's third-party warning. Publish the catalog only after its installer exists in Releases.

`build_repository.py` genera la fuente; la [lista de publicación](../docs/HACS_PUBLISHING.md#fuente-de-paquetes-dsm) explica cómo publicarla y sus límites de validación. No habilites instalación/actualización silenciosa para evitar el aviso DSM. Publica el catálogo después del instalador.

Se genera el archivo en `dsm_package/dist/`. Incrementa la revisión para cambios solo DSM dentro de la misma versión. El NAS necesita Python 3; se incluyen `ifaddr` y `zeroconf`.

## State and permissions / Datos y permisos

State lives under `/var/packages/pcpowerfree/var/` and contains credentials. Pre/post-upgrade scripts preserve configuration and TLS identity; never regenerate or publish them as part of an update. The limited grant is `/etc/sudoers.d/wakelink-power`.

El estado está en `/var/packages/pcpowerfree/var/` y contiene credenciales. Los scripts de actualización conservan configuración e identidad TLS; no las regeneres ni publiques. El permiso limitado está en `/etc/sudoers.d/wakelink-power`.

**Advanced administrator recovery only:** use the root-protected helper below, never the package-user-writable copy under `target/app`. Running it grants permission but sends no power command. Normal user setup uses the desktop button, not SSH.

**Solo recuperación administradora avanzada:** usa el auxiliar protegido siguiente, nunca la copia modificable por el usuario del paquete en `target/app`. Autoriza sin apagar. La instalación normal usa el botón DSM, no SSH.

```sh
sudo /usr/bin/python3 -I /var/packages/pcpowerfree/conf/power_permissions.py
```

Revoke **before uninstalling** / Retirar **antes de desinstalar**:

```sh
sudo /usr/bin/python3 -I /var/packages/pcpowerfree/conf/power_permissions.py --remove
```

Authentication references / Autenticación: [Synology's CGI authentication guide](https://help.synology.com/developer-guide/integrate_dsm/web_authentication.html). Signed desktop requests also pass the native client's `X-SYNO-TOKEN` and `X-SYNO-HASH`; do not log these. A native window remains browser-backed and still needs server-side authentication.

See [the release checklist](../docs/HACS_PUBLISHING.md) and [historical DSM design](../docs/HISTORY.md) for development, not additional installation steps.
