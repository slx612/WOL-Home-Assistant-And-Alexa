# WakeLink Windows beta.8: local preview

**Superseded:** beta.8 produced desktop shortcuts that could not open the dashboard for a standard user because the TLS certificate was unreadable. Use the [beta.9 test instructions](WINDOWS-beta.9.md) for the correction. Do not distribute beta.8 as a working preview.

[English](#english) | [Espanol](#espanol)

## English

**Status: `0.2.0-beta.8` is unpublished and unsigned.** These are manual test instructions for a locally built installer, not release validation. The public Windows download in the [README](../README.md#download) remains beta.7. Real-hardware results for fresh installation and beta.5/6/7 upgrades are pending; earlier beta tests do not establish beta.8 compatibility.

### What changes, what stays

WakeLink is the public Windows name. `PCPowerSetup.exe` now opens the dashboard; only a PC without configuration enters onboarding. It is not a second installer. Normal dashboard launch is intended to run without a UAC prompt; installing or changing protected system settings still needs administrator permission. The agent still handles local requests and the tray retains its existing startup role.

Compatibility names intentionally remain: `C:\Program Files\PC Power Free`, `C:\ProgramData\PC Power Free`, uninstall key `Software\Microsoft\Windows\CurrentVersion\Uninstall\PC Power Free`, task/firewall name `PC Power Agent`, tray startup value `PC Power Free Tray`, and all `PCPower*.exe` filenames. Keep custom installation/data paths and `PC_POWER_FREE_DATA_DIR` unchanged. WakeLink shortcuts are added; legacy shortcuts are kept as aliases to the same dashboard. The Home Assistant integration remains `PC Power Free`.

The installer has English and Spanish presentation, a WakeLink icon and no restart request on Finish. First configuration and preserved upgrade settings have different finish messages. First-time launch receives `--lang en` or `--lang es`; an upgrade launches the dashboard without `--lang` so a saved preference can win. The installer does not change Alexa or Matter configuration, and neither route is claimed working or validated here.

### Upgrade beta.5 / beta.6 / beta.7 to beta.8

1. **Do not uninstall.** Save your work, back up Home Assistant and securely copy the whole existing data folder, normally `C:\ProgramData\PC Power Free`. Include `config.json`, guard/preferences and any `agent-cert.pem` / `agent-key.pem`. Do not publish the token or private key.
2. Close the dashboard. Manually run the local `pcpowerfree-windows-x64-setup.exe` supplied for beta.8, keeping the existing installation and data paths. Approve the installer's Windows elevation prompt only after checking the file's source.
3. The upgrade must keep the configured port, token, `machine_id`, allowed networks, power/guard settings and existing certificate/key. Older versions without TLS files create an identity during migration; an existing identity must not be rotated. Damaged identity files require investigation or backup restoration, not deletion and re-pairing.
4. Leave **Open WakeLink and the tray app** selected on Finish. Both open; the dashboard shows the existing installation, not first-time onboarding. No second setup, new pairing code or Windows restart is required. Previously disabled automatic startup stays disabled; if you ran the agent manually before, use that same method.
5. Keep the existing Home Assistant entry and entity IDs. If its integration is still beta.5/6, update that component separately using the [beta.7 guide](UPGRADE-beta.7.md) for HTTPS compatibility. Do not delete the device, reset its token, redo pairing or change Alexa/Matter configuration as part of this Windows preview.
6. Compare the saved settings and certificate fingerprint with your backup, then check local status and existing Home Assistant entities. If installation fails or onboarding appears unexpectedly, stop: inspect `upgrade.log` beside `config.json`, preserve the backup and report the failure. Do not uninstall to retry.

### Fresh installation

Run the local installer once, choose English or Spanish, and leave **Open WakeLink** selected. Choose **Enable and continue** in the dashboard: it detects the network, allows that local subnet and enables agent/tray startup. Pair with Home Assistant on a trusted LAN after comparing the fingerprint displayed on the Home Assistant page. The code lasts ten minutes. This first pairing is not part of an ordinary upgrade. **Settings > Repair local setup** is an explicit recovery action which enables startup again without changing credentials; it is not required during a normal upgrade.

The saved UI language is in `%LOCALAPPDATA%\WakeLink\preferences.json`, separate from the agent data. The updater cache is also per-user; a failure to write it does not hide update results. Agent protocol compatibility remains the same as beta.7; only Windows preview artifacts are rebuilt in this task, not the Linux/DSM or Home Assistant packages.

### SmartScreen and signing

Unsigned preview files may trigger SmartScreen or unknown-publisher warnings. Verify the source and any supplied checksum; do not disable antivirus, SmartScreen or policy protections. Free signing for this open-source project is pending. Future signing does not guarantee the absence of reputation warnings. See [Microsoft's explanation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

### Manual smoke checklist

All boxes are **pending**, not pass results. Use a disposable Windows x64 VM for fresh-install cases and backed-up test machines/snapshots for each upgrade baseline. Record the starting version, installer SHA-256, Windows version, language, display scale and result. Do not overwrite a working installation merely to perform a fresh-install test.

- [ ] Fresh EN and fresh ES: one installer, correct welcome/finish text, matching onboarding language, no blank README checkbox, no reboot prompt, no second installer step.
- [ ] First configuration: agent/tray automatic startup is enabled, dashboard reopens without onboarding or an elevation prompt just to view it. An existing installation's startup setting is not changed by an ordinary upgrade.
- [ ] Upgrade separately from beta.5, beta.6 and beta.7: same installation/data paths and uninstall registration; port, token, machine ID and existing TLS certificate/key preserved; no new pairing. Compare locally without exposing secrets.
- [ ] Upgrade Finish: tray and dashboard both open, preserved-settings message replaces first-configuration text, saved startup/guard choices remain. Repeat with automatic startup disabled and with a non-default port/data location.
- [ ] Languages: fresh EN/ES matches installer choice; save ES then upgrade using EN, and save EN then upgrade using ES. The dashboard must retain the saved choice across launch and upgrade.
- [ ] Shortcuts: WakeLink and existing English/Spanish PC Power Free aliases open the same dashboard; no legacy shortcut is removed during upgrade. Windows installed-apps display is WakeLink `0.2.0-beta.8` with the existing uninstall key.
- [ ] High DPI: inspect installer and dashboard at 100%, 150% and 200%, including moving between differently scaled monitors; text, fields and Finish buttons remain visible and usable by keyboard in both languages.
- [ ] Updates online: opening the public release page does not claim beta.8 is published or recommend downgrading this local preview. No automatic installer execution.
- [ ] Updates offline: disconnect Internet while retaining LAN if possible, request an update check, and verify a bounded failure/unavailable result rather than "up to date"; dashboard remains responsive and settings/status still work. Reconnect and retry.
- [ ] Real hardware, only with explicit tester approval and saved work: verify startup after a separate manual reboot, guard behavior and Home Assistant status; shutdown/restart/Wake-on-LAN checks remain pending until actually performed. The installer itself must never request or initiate a reboot.

### Maintainer verification

Run `python -m unittest discover -s tests -v` for source-level regression checks; these do not exercise native installation or hardware. Compile NSIS only after the matching beta.8 agent, tray, dashboard and support files are available in `windows_agent/dist`, with `windows_agent/assets/wakelink.ico` supplied by the app build. Do not package old beta.7 binaries under a beta.8 label. Building or reviewing NSIS is not permission to run the installer or modify an installed configuration.

## Espanol

**Estado: `0.2.0-beta.8` no esta publicada y no tiene firma digital.** Esta guia es para probar manualmente un instalador local, no un informe de validacion. La descarga publica del [README](README.es.md#descarga) sigue siendo beta.7. Estan pendientes las pruebas reales de instalacion nueva y actualizacion desde beta.5/6/7; las pruebas anteriores no validan beta.8.

### Nombres y comportamiento

WakeLink es el nombre visible de Windows. `PCPowerSetup.exe` abre el panel; solo muestra la configuracion inicial cuando no hay configuracion previa. No es otro instalador. Abrir el panel normalmente no debe pedir UAC; instalar o cambiar ajustes protegidos del sistema sigue requiriendo administrador. Se mantienen las funciones del agente y la bandeja al inicio.

Se conservan las carpetas `C:\Program Files\PC Power Free` y `C:\ProgramData\PC Power Free`, la clave de desinstalacion terminada en `PC Power Free`, tarea y regla `PC Power Agent`, valor de inicio `PC Power Free Tray` y nombres `PCPower*.exe`. No cambies rutas personalizadas ni `PC_POWER_FREE_DATA_DIR`. Los accesos WakeLink se anaden sin borrar los alias antiguos. En Home Assistant la integracion sigue llamandose `PC Power Free`. Alexa y Matter no se modifican ni se dan por validados.

La primera apertura recibe `--lang en` o `--lang es` segun el idioma del instalador. Una actualizacion no pasa `--lang`: debe prevalecer la preferencia guardada. La pantalla final diferencia configuracion inicial de actualizacion con ajustes conservados y no solicita reiniciar Windows.

### Actualizar beta.5 / beta.6 / beta.7 a beta.8

1. **No desinstales.** Guarda tu trabajo, respalda Home Assistant y copia de forma segura toda la carpeta de datos existente, normalmente `C:\ProgramData\PC Power Free`. Conserva `config.json`, proteccion/preferencias y los archivos `agent-cert.pem` / `agent-key.pem` si existen. No compartas token ni clave privada.
2. Cierra el panel y ejecuta manualmente el `pcpowerfree-windows-x64-setup.exe` local de beta.8. Mantiene las mismas rutas de instalacion y datos. Acepta el permiso de administrador del instalador solo tras verificar su origen.
3. La actualizacion debe conservar puerto, token, `machine_id`, redes permitidas, ajustes de energia/proteccion y certificado/clave existentes. Si una version antigua no tiene archivos TLS, la migracion los crea; no debe sustituir una identidad existente. Si estan danados, investiga o restaura la copia, no los borres para volver a vincular.
4. Deja marcada **Abrir WakeLink y la bandeja** al finalizar. Deben abrirse ambos y mostrar la instalacion existente, no la configuracion inicial. No hace falta otro codigo, repetir el setup ni reiniciar Windows. El inicio automatico desactivado sigue desactivado; si arrancabas el agente manualmente, hazlo como antes.
5. Conserva la entrada y entidades de Home Assistant. Si su integracion sigue en beta.5/6, actualiza ese componente por separado siguiendo la [guia beta.7](UPGRADE-beta.7.md#espanol) para HTTPS. No borres el dispositivo, no restablezcas el token, no vuelvas a vincular ni cambies Alexa/Matter para esta prueba.
6. Compara los ajustes y la huella del certificado con la copia, y comprueba el estado local y las entidades existentes. Si falla o aparece una configuracion inicial inesperada, detente y consulta `upgrade.log` junto a `config.json`. Conserva la copia y comunica el fallo; no desinstales para reintentar.

### Primera instalacion

Ejecuta el instalador local una sola vez, elige espanol o ingles y deja **Abrir WakeLink** marcado. Pulsa **Activar y continuar**: detecta la red, permite esa subred local y activa el inicio del agente y la bandeja. Compara la huella mostrada en la pagina Home Assistant y vincula en una red de confianza. El codigo dura diez minutos; no se repite para actualizar. **Ajustes > Reparar configuracion local** es una recuperacion explicita que reactiva el inicio sin cambiar credenciales; no es necesaria al actualizar normalmente.

El idioma se guarda en `%LOCALAPPDATA%\WakeLink\preferences.json`, separado del agente. El historial del buscador tambien se guarda por usuario; un fallo al guardarlo no oculta el resultado. Esta tarea solo recompila la vista previa de Windows, no los paquetes Linux/DSM ni la integracion de Home Assistant. El protocolo es compatible con beta.7.

### Seguridad y comprobaciones

La vista previa sin firma puede mostrar advertencias de SmartScreen o editor desconocido. Verifica origen y suma de comprobacion; no desactives antivirus, SmartScreen ni politicas. La firma gratuita del proyecto de codigo abierto esta pendiente y no garantiza que desaparezcan todas las advertencias. La [documentacion de Microsoft](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation) explica la reputacion de las descargas.

Todas las casillas siguen **pendientes**. Usa una VM desechable para instalaciones nuevas y copias/snapshots para cada version anterior. Anota version inicial, SHA-256 del instalador, Windows, idioma, escala y resultado, sin publicar secretos.

- [ ] Instalacion nueva en EN y ES: idioma correcto, configuracion inicial una sola vez, sin casilla README vacia, segundo instalador ni solicitud de reinicio.
- [ ] Primera configuracion: guarda ajustes, respeta inicio del agente/bandeja y reabre el panel sin onboarding ni UAC solo para consultarlo.
- [ ] Actualizacion desde cada beta.5, beta.6 y beta.7: conserva rutas, registro, puerto, token, identidad y certificado/clave existentes; no pide nueva vinculacion.
- [ ] Final de actualizacion: abre bandeja y panel con mensaje de ajustes conservados; mantiene proteccion e inicio, tambien desactivado. Repite con puerto y datos personalizados.
- [ ] Idiomas: instalacion nueva sigue EN/ES; una preferencia guardada ES sobrevive a un instalador EN y viceversa, incluso al reabrir.
- [ ] Accesos: WakeLink y alias antiguos EN/ES abren el mismo panel, sin borrar los anteriores. Aplicaciones instaladas muestra WakeLink `0.2.0-beta.8` con la misma clave de desinstalacion.
- [ ] DPI alto: 100%, 150% y 200%, tambien entre monitores distintos; textos, campos y botones no se cortan y admiten teclado en ambos idiomas.
- [ ] Actualizaciones con Internet: no anuncia beta.8 publicada ni recomienda bajar de version; no ejecuta un instalador automaticamente.
- [ ] Sin Internet, manteniendo LAN si es posible: buscar actualizaciones termina con error/no disponible, nunca con "actualizado"; panel y ajustes siguen respondiendo. Reconecta y reintenta.
- [ ] Hardware real, solo con autorizacion y trabajo guardado: inicio tras reinicio manual separado, proteccion y estado en Home Assistant; apagado, reinicio y WOL siguen pendientes hasta probarlos. El instalador no debe solicitar ni provocar reinicios.

Las pruebas de codigo (`python -m unittest discover -s tests -v`) no sustituyen estas comprobaciones. Compila NSIS solo con los binarios beta.8 correspondientes, archivos auxiliares e icono `windows_agent/assets/wakelink.ico`; no etiquetes binarios beta.7 como beta.8. Compilar o revisar no autoriza ejecutar el instalador ni tocar la configuracion instalada.
