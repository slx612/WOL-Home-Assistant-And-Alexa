# Beta.7: upgrade and verification

[English](#english) | [Espanol](#espanol)

## English

Status: [beta.7 prerelease](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.7). This is a beta, not a claim of complete hardware validation.

### What changed

The agent now uses HTTPS. Home Assistant pins the PC's SHA-256 certificate identity before sending its token, including after an IP change. There is no HTTP fallback. The certificate and private key stay beside `config.json`; keep them when updating. The MAC is used for waking and discovery, never authentication.

**Updating from the published beta.6 does not require pairing again.** The existing long-lived secret authenticates the PC's new certificate through a fresh challenge. The secret is not sent until that verification succeeds. HA saves the verified identity in the existing entry; entry IDs, device IDs, names and automation references are retained. See the [migration protocol and limits](TLS-MIGRATION.md).

Pairing is still a temporary six-digit code, valid for ten minutes and consumed once. First enrollment is trust-on-first-use: compare the TLS fingerprint in the PC setup summary with the one displayed by Home Assistant before entering the code. A code alone does not prevent an active attacker on the network from impersonating a device during first enrollment. Do not pair over guest/public Wi-Fi. Subsequent connections use the saved fingerprint, not discovery announcements.

Guard/configuration files are saved atomically. Damaged protection state blocks commands rather than allowing them. Pairing checks are serialized. Requests have a 4 KiB body limit, five-second socket timeout and at most 32 workers. HA fallback scans have 32 workers, a 4,096-address budget and a 12-second deadline. On very large networks, use mDNS or enter the current address manually.

Windows tasks now have no run-time limit, allow battery operation and restart after failures. Reconfiguration stops the old task; installation verifies the new endpoint. Unchecking automatic startup removes the task and tray startup. Uninstall stops the agent before deleting it. Opening Setup from the tray requests administrator permission. Windows uptime uses 64 bits.

HA upgrades preserve the entry and entity identifiers. Options no longer override new discovery addresses; reloads go through HA's lifecycle manager. Reauthentication is available without removing devices. Power commands use the agent's configured defaults; OS errors are displayed as command errors. A lost command response is not automatically retried.

### Update an existing Windows installation

1. Keep a Home Assistant backup and save open work. Do not test shutdown while editing documents.
2. Install the beta.7 Windows installer over the old version. Do not uninstall first: uninstall removes configuration and the TLS identity.
3. The installer detects existing settings and upgrades without repeating the configurator. It preserves the token, machine ID, allowed networks, port, shutdown preferences and guard. It creates the TLS identity only if absent, updates/restarts an existing enabled startup task and checks that the agent responds. Disabled/absent automatic startup remains disabled. Leave the PC awake; if startup was disabled, start the agent by your existing manual method.
4. In HACS, open PC Power Free, use the three-dot menu > Redownload > Need a different version?, and select `v0.2.0-beta.7`. If it is not listed yet, use Update information or download the integration ZIP from the release: its `custom_components/pc_power_free` directory replaces the old one inside HA's `config/custom_components`. Restart Home Assistant. See the [official HACS version-selection instructions](https://hacs.xyz/docs/use/repositories/dashboard/#downloading-a-specific-version-of-a-repository).
5. Leave the existing PC entry in Settings > Devices & services. Do not add it again, reset its token or request a pairing code. The next successful check or discovery authenticates and saves the new certificate automatically.
6. Confirm the existing entities, names and automations are still present. Alexa continues to use those same exposed entities; it does not need device discovery again solely because of this upgrade.

**Either update order works**, but control/status can be temporarily unavailable between the two updates. With new HA and the old agent (or a powered-off PC), the existing entities remain loaded, the switch exposes `upgrade_pending: true`, and Wake-on-LAN remains usable. Status/shutdown/restart recover after the agent is updated and reachable. With the new agent and old HA, encrypted control waits for the HA update. No passwords are sent over the old HTTP protocol to hide this temporary incompatibility.

The Windows update uses the same data-location rules as the published configurator, including custom locations and `PC_POWER_FREE_DATA_DIR`. Normal installed data is in `C:\ProgramData\PC Power Free`. Keep the same installation/data location when updating. If an update fails, it reports an error and preserves the settings; inspect `upgrade.log` beside `config.json`, correct the problem and rerun the installer, rather than uninstalling.

Reauthentication is for lost/changed credentials or deliberate identity replacement, not normal upgrades. A missing/damaged existing certificate is not silently replaced. Restore the data backup if it was accidentally removed. Migration cannot recover a secret deleted from both sides or make a previously stolen beta.6 token safe.

The normal Windows installer should create and run the task for you. No manual Startup-folder shortcut or fixed PC IP is required. Home Assistant must remain powered on to send Wake-on-LAN. Alexa still depends on the previously configured Home Assistant connection; this is not an Echo-only implementation.

### Linux and DSM

Stop the old agent before replacing sources; keep the data directory and configuration. Linux needs Python and the documented dependencies, including `cryptography` or OpenSSL 1.1.1+. Restart the service without rerunning pairing setup: TLS files are created on first start when absent, and the existing HA entry upgrades automatically. See [Linux instructions](../linux_agent/README.md).

DSM initialization now propagates generation errors and validates existing configuration/TLS identity. Its package-account privileges still do not establish supported shutdown/restart access. Treat DSM power actions as experimental and unvalidated; no broad root privileges have been added to hide that limitation.

### Checks before calling this stable

1. Start with an already-paired beta.6 Windows/HA installation. Upgrade both in either order without opening pairing; repeat with the PC initially off. Reload options and restart HA. Check that entity IDs, device IDs, names, automations and Alexa exposure remain intact.
2. Restart Windows and confirm the agent is reachable before login and that the tray opens Setup after normal login. Inspect the task's unlimited duration and battery conditions.
3. Renew the PC's DHCP address and verify discovery recovers without accepting a different certificate. Temporarily disconnect networking at boot and reconnect it.
4. Enable the tray's protection and request shutdown/restart from HA: both must be rejected. Test timed protection expiry and then disable it deliberately.
5. Save all work, then test one real shutdown, Wake-on-LAN and restart. Finally test the Alexa route. BIOS, NIC, Ethernet/Wi-Fi and sleep/shutdown support remain hardware-dependent.
6. On a disposable/test installation, change port, disable automatic startup and uninstall. Check that the old process/port/task are gone. Do not use the working PC for destructive installer tests without a backup.

### Automated verification and limits

Run `python -m pip install -r tests/requirements.txt`, then `python -m unittest discover -s tests -v` from the repository root. Tests use fake power adapters, temporary files and loopback endpoints. HA lifecycle/flow tests use contract doubles, not a running HA instance. Windows task, elevation and uninstall checks do not install or remove a real task. GitHub CI is configured for Windows and Linux; current results are on the repository's Actions page.

Known follow-up work outside the sixteen main findings: Windows multi-user ACL hardening, tray status polling/language preference persistence, deterministic transitive build dependencies and DSM's supported privileged power-action design. Local source/portable installs must keep their config and private key inaccessible to untrusted local users. The old `setup-wizard.ps1` console wizard is not a validated beta.7 setup path; use `PCPowerSetup.exe`. Do not expose the agent to the Internet.

## Espanol

Estado: [version preliminar beta.7](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.7). Sigue siendo una beta pendiente de pruebas reales.

### Actualizacion paso a paso

1. Haz una copia de seguridad de Home Assistant y guarda los documentos abiertos.
2. Ejecuta el instalador de Windows beta.7 sobre la instalacion anterior. No desinstales antes: la desinstalacion borra configuracion y certificados.
3. El instalador detecta la configuracion anterior y la reutiliza sin repetir el asistente. Conserva la clave, identidad, puerto, redes permitidas, preferencias de apagado y proteccion. Actualiza y arranca la tarea de inicio si estaba habilitada; no habilita una tarea desactivada o inexistente. Manten el PC encendido; si lo arrancabas manualmente, inicia el agente como antes.
4. En HACS, abre PC Power Free y usa el menu de tres puntos > Volver a descargar > Necesitas otra version, seleccionando `v0.2.0-beta.7`. Si aun no aparece, actualiza la informacion o descarga el ZIP de la release: su carpeta `custom_components/pc_power_free` sustituye a la anterior dentro de `config/custom_components` de HA. Reinicia Home Assistant. Consulta la [guia oficial de seleccion de versiones de HACS](https://hacs.xyz/docs/use/repositories/dashboard/#downloading-a-specific-version-of-a-repository).
5. Conserva la entrada existente de PC Power Free en Ajustes > Dispositivos y servicios. No la borres, no vuelvas a anadir el PC y no generes otro codigo o token. Home Assistant verifica y guarda automaticamente la nueva identidad en cuanto contacta con el agente actualizado.
6. Comprueba que siguen tus entidades y automatizaciones. No necesitas fijar la IP del PC ni colocar accesos directos en la carpeta de Inicio.

**La actualizacion desde la beta.6 publicada no exige volver a vincular.** La clave que PC y HA ya comparten permite verificar el nuevo certificado sin enviarla antes de autenticarlo. Se conservan dispositivos, entidades, nombres y referencias de las automatizaciones. Alexa mantiene las mismas entidades expuestas, sin tener que descubrirlas otra vez por esta actualizacion.

Puedes actualizar en cualquiera de los dos ordenes. Entre una actualizacion y otra puede faltar temporalmente el control: con HA nuevo y agente antiguo (o PC apagado), las entidades se conservan y puedes enviar WOL; el atributo `upgrade_pending` indica que falta completar la conexion segura. Apagar, reiniciar y consultar el estado se recuperan cuando ambos estan actualizados y el PC es accesible. No se vuelve al HTTP antiguo para evitar esta espera.

No cambies la carpeta de instalacion ni borres los datos. El actualizador usa la misma ubicacion que el configurador anterior, normalmente `C:\ProgramData\PC Power Free`, y respeta las ubicaciones personalizadas. Si falla, consulta `upgrade.log` junto a `config.json` y reintenta despues de corregirlo: no desinstales. Si antes desactivaste el inicio automatico, seguira desactivado.

Solo hace falta reparar la autenticacion si se han perdido/cambiado las claves o se sustituye deliberadamente la identidad del equipo. Si borraste datos, restaura la copia de seguridad. La migracion no puede recuperar una clave eliminada de ambos lados ni proteger retroactivamente una clave que ya hubiera sido robada en beta.6. Detalles tecnicos: [migracion de confianza](TLS-MIGRATION.md).

El primer emparejamiento sigue necesitando una red de confianza. Compara las huellas antes de introducir el codigo; el codigo por si solo no protege frente a un atacante activo durante esa primera vinculacion. Conserva `agent-cert.pem` y `agent-key.pem` junto a la configuracion al actualizar. No compartas el archivo de clave privada ni el token.

### Que hay que probar

1. Parte de una beta.6 ya vinculada. Actualiza ambos componentes sin abrir el emparejamiento, prueba los dos ordenes y repite empezando con el PC apagado. Reinicia HA y cambia opciones: deben mantenerse las entidades, dispositivos, nombres, automatizaciones y exposicion a Alexa.
2. Reinicia Windows: el agente debe funcionar sin iniciar sesion. Tras iniciar sesion, abre el configurador desde la bandeja y acepta la solicitud de administrador.
3. Cambia la direccion del PC mediante DHCP y comprueba que HA lo recupera. El descubrimiento tambien reintenta cuando la red tarda en estar disponible.
4. Activa la proteccion de la bandeja y solicita apagar/reiniciar: ambas ordenes deben rechazarse. Comprueba tambien que una proteccion temporal caduca.
5. Solo despues de guardar todo, prueba un apagado, un encendido WOL y un reinicio reales. Luego prueba Alexa. El soporte de BIOS, tarjeta de red, Wi-Fi/Ethernet y estados de energia depende del equipo.
6. En una instalacion de prueba, cambia el puerto, desactiva el inicio automatico y desinstala. Comprueba que no queda el proceso anterior funcionando.

Home Assistant tiene que permanecer encendido para enviar WOL. Alexa sigue usando la conexion con Home Assistant; no se ha convertido en una solucion solo Echo + PC.

Linux: detiene el agente, sustituye los archivos, conserva los datos y reinicia el servicio, sin repetir el configurador ni generar otro codigo. Necesita las dependencias indicadas en la [guia Linux](../linux_agent/README.md). DSM ya informa si falla la inicializacion, pero sus permisos de apagado y reinicio siguen pendientes: no doy esas funciones por validadas.

Las pruebas automaticas no apagan ordenadores y no sustituyen estas comprobaciones. Quedan mejoras fuera de los dieciseis hallazgos principales: permisos Windows multiusuario, refresco periodico e idioma persistente de la bandeja, dependencias de compilacion totalmente reproducibles y permisos de energia compatibles con DSM. Manten los archivos de configuracion y claves fuera del alcance de usuarios locales no fiables. El antiguo asistente de consola `setup-wizard.ps1` no es una ruta validada para beta.7: usa `PCPowerSetup.exe`.
