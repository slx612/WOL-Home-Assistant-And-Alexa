# WakeLink Windows beta.9: local test build

[English](#english) | [Espanol](#espanol)

## English

Beta.9 repairs the Windows certificate permissions that prevented a standard user from opening beta.8's dashboard and tray. It also replaces the two automatic desktop shortcuts with one optional shortcut, off by default. This build is not yet published and remains unsigned. The public GitHub download is beta.7.

### Upgrade an installed beta.8 (or beta.5/6/7)

1. Save your work. Back up `C:\ProgramData\PC Power Free` securely, including `config.json` and any TLS files. Keep the backup private.
2. Close WakeLink and run **WakeLink-Setup-beta.9.exe**. Approve the Windows administrator prompt. **Do not uninstall beta.8 first.** Keep the existing installation folder.
3. On the components page, select **Create a desktop shortcut** only if you want one. Unchecked removes WakeLink's old desktop shortcuts. A Start menu entry remains either way.
4. On Finish, open WakeLink. It should show the existing PC, not onboarding. Open **Home Assistant** inside WakeLink to view the certificate fingerprint. Your existing Home Assistant device and pairing should stay in place.
5. Open WakeLink again from Start. Check local agent status and the tray icon. If the agent is unavailable, record the exact message and preserve your backup. Do not delete the Home Assistant device or regenerate a pairing code to fix an opening error.

The installer grants standard users read access to the **public certificate only**. It keeps the existing certificate bytes, private key, token and machine ID. If a certificate is damaged rather than merely unreadable, repair still needs investigation; do not delete it casually.

### New installation

Run the same installer once, choose English or Spanish, and optionally select the desktop shortcut. On Finish, open WakeLink, select **Enable and continue**, then pair the discovered PC in Home Assistant using the temporary code. Read the fingerprint on the Home Assistant page in WakeLink. A code is only needed for a new pairing.

### Check before a public release

- [ ] Upgrade the affected beta.8 with the shortcut unchecked: the two old desktop icons disappear, the Start menu opens WakeLink without a certificate error, and Home Assistant pairing remains.
- [ ] Upgrade with the shortcut checked: exactly one WakeLink desktop icon opens it.
- [ ] Confirm the tray opens and local status works after closing and reopening the dashboard as a normal user.
- [ ] Test a new installation and upgrades from beta.5/6/7 separately; compare identity, port and certificate fingerprint before and after.
- [ ] Test actual wake, shutdown and restart only after saving work and approving those power tests.

Windows may still show a security or unknown-publisher warning for an unsigned build. One installation without a warning does not mean signing is complete. Alexa/Matter pairing is separate and unverified by this Windows fix.

## Espanol

Beta.9 corrige los permisos del certificado de Windows que impedian a un usuario normal abrir el panel y la bandeja de beta.8. Sustituye los dos accesos de escritorio automaticos por uno opcional, desmarcado por defecto. Esta version no esta publicada y sigue sin firma digital. La descarga publica de GitHub es beta.7.

### Actualizar beta.8 instalada (o beta.5/6/7)

1. Guarda tu trabajo. Haz una copia privada de `C:\ProgramData\PC Power Free`, incluyendo `config.json` y los archivos TLS si existen.
2. Cierra WakeLink y ejecuta **WakeLink-Setup-beta.9.exe**. Acepta el permiso de administrador de Windows. **No desinstales beta.8 antes.** Usa la misma carpeta de instalacion.
3. En la pantalla de componentes, marca **Crear un acceso directo en el escritorio** solo si quieres uno. Si no lo marcas, se quitan los accesos antiguos de WakeLink del escritorio. Siempre queda la entrada en Inicio.
4. Al terminar, abre WakeLink. Debe mostrar el PC ya configurado, no el asistente inicial. En **Home Assistant** dentro de WakeLink puedes ver la huella del certificado. La vinculacion anterior debe mantenerse.
5. Cierra y vuelve a abrir WakeLink desde Inicio. Comprueba el estado del agente y el icono de la bandeja. Si el agente no responde, apunta el mensaje exacto y conserva la copia. No borres el dispositivo de Home Assistant ni generes otro codigo por un error de apertura.

El instalador permite a los usuarios normales leer **solo el certificado publico**. Conserva los bytes del certificado existente, la clave privada, el token y el identificador del equipo. Si el certificado esta danado y no simplemente bloqueado, habra que investigarlo; no lo borres sin comprobarlo.

### Instalacion nueva

Ejecuta el mismo instalador, elige espanol o ingles y decide si quieres el acceso directo. Al terminar, abre WakeLink, pulsa **Activar y continuar** y vincula el PC descubierto en Home Assistant con el codigo temporal. La huella aparece en la pagina Home Assistant de WakeLink. Solo necesitas un codigo para una vinculacion nueva.

### Comprobaciones antes de publicarla

- [ ] Actualizar la beta.8 afectada sin marcar el acceso: desaparecen los dos iconos antiguos, Inicio abre WakeLink sin error y Home Assistant sigue vinculado.
- [ ] Repetir marcando la casilla: aparece exactamente un icono WakeLink y se abre.
- [ ] Comprobar bandeja y estado local tras cerrar y reabrir el panel como usuario normal.
- [ ] Probar instalacion nueva y actualizaciones desde beta.5/6/7 por separado; comparar identidad, puerto y huella antes y despues.
- [ ] Probar encendido, apagado y reinicio reales solo tras guardar el trabajo y autorizar esas pruebas.

Windows todavia puede mostrar un aviso de seguridad o de editor desconocido porque el instalador no tiene firma digital. Que una instalacion no avise no significa que el problema de la firma este resuelto. Alexa/Matter requiere pruebas aparte.
