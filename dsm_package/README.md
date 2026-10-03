# WakeLink DSM package / Paquete DSM

**For installation, use [English](../docs/INSTALL_DSM.en.md) or [Español](../docs/INSTALL_DSM.es.md).** This file describes the package, not a second user setup route.

**Para instalar, sigue [English](../docs/INSTALL_DSM.en.md) o [Español](../docs/INSTALL_DSM.es.md).** Aquí se describe el paquete, no otro recorrido de instalación.

## Current design / Diseño actual

- Visible name: **WakeLink**. Internal package ID: `pcpowerfree`; integration domain: `pc_power_free`. These IDs and stored identity are retained for upgrades.
- Opens a window inside the HTTPS DSM desktop. Uses the existing administrator session; hiding the launcher is not an access-control mechanism. Backend requests must authenticate and check administrator membership.
- The agent uses the shared runtime and runs as a package user, **not root**. The UI exposes status and pairing; power actions come from the paired Home Assistant integration.
- Initial shutdown/restart authorization uses DSM's native password confirmation. WakeLink does not store the password. A disabled, non-repeating task runs the fixed protected helper once, then is removed.
- Only normal, immediate `synoshutdown --shutdown` and `synoshutdown --reboot` are granted. No shell, arbitrary root command, forced shutdown or delay.
- Setup depends on DSM's installed native client interfaces. Future DSM versions need regression testing; the current preview is not SynoCommunity-ready.

Nombre visible **WakeLink**; se conservan los identificadores internos y los datos para actualizar. La ventana usa la sesión administradora DSM; el servidor comprueba esa sesión, no se fía de ocultar el icono. El agente no es root. El permiso inicial confirma mediante el diálogo DSM y solo permite apagado/reinicio normales. No guarda la contraseña ni autoriza una consola. Se deben repetir pruebas de compatibilidad tras cambios DSM.

## Beta.13

DSM revision **0024**, based on app **0.2.0-beta.13**, includes the current guided permission and a Package Center catalog. Earlier local revision 0021 was used for the fresh-install test. Installation, session checks, limited command permission and post-boot sensors were checked on a DSM 7.2 VM. The user reported successful fresh installation and power controls. Other DSM versions, controlled restart, physical NAS wake and downgrade remain unvalidated.

La revisión DSM **0024**, app **0.2.0-beta.13**, incluye el asistente actual y catálogo del Centro de paquetes. Se usó la prueba local 0021 para la instalación limpia anterior. Se comprobaron instalación, sesión, permiso limitado y sensores después del arranque en una VM DSM 7.2. El usuario comunicó instalación limpia y controles funcionales. Faltan otras versiones, reinicio controlado, encendido físico y regreso a un paquete anterior.

## Build / Compilar

From the repository root on Windows / Desde la raíz del repositorio en Windows:

```powershell
.\dsm_package\build-dsm-package.ps1 -DsmRevision 24
```

The builder produces `dsm_package/dist/pcpowerfree-dsm-noarch-0.2.0-0024.spk` for beta.13. Always specify a higher numeric DSM revision for later changes; the default beta number would be lower than local test revisions. Python 3 must be available on the target NAS; `ifaddr` and `zeroconf` are bundled. The package includes metadata, lifecycle scripts, desktop assets, and the protected `conf/power_permissions.py` helper.

The 0021 fresh-install build and 0021-to-0022 in-place upgrade were tested; the catalog then exposed/downloaded 0023 successfully. The package source generator is `build_repository.py`; publication steps and the remaining graphical-wizard check are in [the release checklist](../docs/HACS_PUBLISHING.md#dsm-package-source). Keep quick install/upgrade disabled for DSM's third-party warning. Publish the catalog only after its installer exists in Releases.

Se probaron la instalación limpia 0021 y la actualización 0021 a 0022; el catálogo detectó y descargó 0023 correctamente. `build_repository.py` genera la fuente; la [lista de publicación](../docs/HACS_PUBLISHING.md#fuente-de-paquetes-dsm) explica cómo publicarla y qué prueba gráfica falta. No habilites instalación/actualización silenciosa para evitar el aviso DSM. Publica el catálogo después del instalador.

Esta prueba genera ese archivo en `dsm_package/dist/`. Usa una revisión numérica superior para cambios posteriores solo DSM; por defecto corresponde al número beta de la app. El NAS necesita Python 3; se incluyen `ifaddr` y `zeroconf`.

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
