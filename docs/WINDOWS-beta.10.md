# WakeLink beta.10: install and update

> **Historical beta.10 note / Nota historica.** For current installation use [English](GETTING_STARTED.en.md) or [Espanol](GETTING_STARTED.es.md).

[English](#english) | [Espanol](#espanol)

## English

Beta.10 is a prerelease for testing. It opens the dashboard on a **left-click** of the Windows tray icon; a **right-click** still opens the protection and update menu. Update prompts open the validated Windows installer download in your browser. Downloading does not install or run it automatically.

### Update from beta.9

1. Save your work and keep a private backup of `C:\ProgramData\PC Power Free`, including `config.json` and the TLS files. Do not publish the token or private key.
2. Right-click the WakeLink tray icon and choose **Check for updates**. The dialog should show installed `0.2.0-beta.9` and available `0.2.0-beta.10`. In beta.9, **Yes** opens the release page; select its **Windows installer** download. Alternatively, use **Updates > Check for updates > Download Windows installer** in the beta.9 dashboard for the direct download. Beta.10's tray uses the direct download for future updates.
3. Close the dashboard. Run the downloaded `pcpowerfree-windows-x64-setup.exe` over the existing installation. **Do not uninstall first.** The installer may ask for administrator permission and may show an unsigned-app warning.
4. Leave the desktop-shortcut option unchecked unless you want one. At Finish, the existing PC should open without first-time onboarding or a new pairing code.
5. Close the dashboard. Left-click the tray icon to reopen it; right-click to confirm the menu still works. Check for updates again: beta.10 should say no newer Windows installer is available.

The installer keeps your port, token, machine ID, guard state and TLS identity. Your Home Assistant device and automations should continue to use the existing pairing. HACS may offer beta.10 of the integration; its protocol is unchanged, and updating it should not require re-pairing.

If the update check fails, record its exact message and confirm Internet access. If opening WakeLink or Home Assistant control fails after installation, keep the backup and report the error instead of removing the device. Actual wake, shutdown, restart and Alexa/Matter behavior require separate testing.

## Espanol

Beta.10 es una version preliminar para pruebas. Un **clic izquierdo** en el icono de WakeLink de la bandeja abre el panel; el **clic derecho** conserva el menu de proteccion y actualizaciones. El aviso de actualizacion abre la descarga del instalador de Windows en el navegador. Descargarlo no lo instala ni lo ejecuta automaticamente.

### Actualizar desde beta.9

1. Guarda tu trabajo y haz una copia privada de `C:\ProgramData\PC Power Free`, incluido `config.json` y los archivos TLS. No publiques el token ni la clave privada.
2. Haz clic derecho en el icono WakeLink de la bandeja y elige **Buscar actualizaciones**. Debe indicar instalada `0.2.0-beta.9` y disponible `0.2.0-beta.10`. En beta.9, **Si** abre la pagina de la version: pulsa alli **Windows installer** para descargarlo. Como alternativa, usa **Actualizaciones > Buscar actualizaciones > Descargar instalador para Windows** en el panel beta.9 para ir directamente a la descarga. La bandeja de beta.10 ya usa la descarga directa para futuras actualizaciones.
3. Cierra el panel. Ejecuta el `pcpowerfree-windows-x64-setup.exe` descargado sobre la instalacion actual. **No desinstales antes.** El instalador puede pedir permiso de administrador y Windows puede advertir que no tiene firma digital.
4. Deja desmarcada la casilla del acceso directo si no quieres uno. Al terminar debe abrirse tu PC ya configurado, sin asistente inicial ni codigo de vinculacion nuevo.
5. Cierra el panel. Haz clic izquierdo en el icono para volver a abrirlo y derecho para confirmar que el menu sigue funcionando. Busca actualizaciones otra vez: beta.10 debe indicar que no hay un instalador mas nuevo.

El instalador conserva el puerto, token, identificador del equipo, proteccion e identidad TLS. El dispositivo y las automatizaciones de Home Assistant deben seguir usando la vinculacion existente. HACS puede ofrecer beta.10 de la integracion; el protocolo no cambia y actualizarla no debe requerir una nueva vinculacion.

Si falla la busqueda, apunta el mensaje exacto y comprueba la conexion a Internet. Si tras instalar falla WakeLink o Home Assistant, conserva la copia y comunica el error en vez de borrar el dispositivo. Las pruebas reales de encendido, apagado, reinicio y Alexa/Matter siguen siendo independientes.
