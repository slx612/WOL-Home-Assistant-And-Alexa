# WakeLink Matter preview (Home Assistant beta.11)

> **Historical beta.11 note / Nota historica.** For current instructions use [English](ALEXA.en.md) or [Espanol](ALEXA.es.md). Do not install beta.11 just to follow this old preview.

[English](#english) | [Espanol](#espanol)

## English

This is a **Home Assistant-only preview**. Keep the Windows beta.10 agent installed. Do not uninstall it, delete the PC from Home Assistant, reset its certificate or generate another pairing code just to upgrade. Beta.11 adds a read-only Alexa guide to the existing device's Configure dialog; it does not install or configure Matterbridge automatically. Alexa control is not yet hardware-validated.

### Before installing

1. In Home Assistant, open **Settings > System > Backups > Back up now > Manual**. Include Home Assistant configuration and the Matterbridge app if it is installed. Store the backup on **This system**. Wait for it to finish, open its details and confirm that both components are offered under **Select what to restore**. Keep the backup encryption key safe; do not paste it into WakeLink or public support requests.
2. Note the currently downloaded WakeLink/PC Power Free integration version and keep that exact published integration ZIP available as a second rollback route. In the first live test, Home Assistant had beta.7 while Windows had beta.10.
3. Make sure the existing PC power switch works in Home Assistant. Do not use the switch merely to test the guide: switching it off shuts down the PC.

### Install and try the guide

1. Update the existing `pc_power_free` HACS integration to beta.11 or, for a manual preview, replace only the files inside `/config/custom_components/pc_power_free` with the beta.11 integration ZIP contents. **Do not delete the integration entry or the directory first.** Restart Home Assistant.
2. Open **Settings > Devices & services > WakeLink > your existing PC > Configure > Connect with Alexa (Matter preview)**. The guide shows the actual power entity ID, including user renames.
3. Use the guide to install/open Matterbridge and its `matterbridge-hass` plugin. If Matterbridge is already paired to another controller, stop first: the plugin can export all Home Assistant entities on first start. The plugin needs a Home Assistant long-lived access token with broad access; create it only if you trust the plugin. Enter it in Matterbridge itself, never in WakeLink. Use `wss://` with a trusted certificate if Home Assistant serves HTTPS; `ws://` sends the token unencrypted and is appropriate only on a trusted local network. Do not disable certificate validation. Do not pair Alexa yet.
4. Restrict the plugin to the intended power switch. The guide's beta path uses **Domain Whitelist = `switch`**, **Split Entities = your power entity ID** and **Whitelist = the same entity ID**. Split Entities is deprecated upstream; if it has disappeared, stop and consult the plugin's Split By Label instructions. Verify the Matterbridge device preview contains only the intended PC switch before pairing. An empty whitelist is unsafe.
5. If the same PC is exposed through Emulated Hue, remove that exposure before Matter pairing to avoid duplicate Alexa devices. In Matterbridge **Settings**, set the Matter mDNS interface to the network interface shown in **Home Assistant > Settings > System > Network**. Then scan Matterbridge's Matter QR code in the Alexa app. This QR code is different from the WakeLink PC pairing code. A compatible Echo and an always-on Home Assistant host are required.
6. Check the state shown in Alexa. Test shutdown only after saving work and explicitly deciding to shut the PC down. The wizard finishing does not prove Alexa works.

### Roll back

- **Integration only:** Restore the previously installed version from HACS if offered, or replace the `pc_power_free` folder's files from that version's published integration ZIP and restart Home Assistant. For the first live test, that version is beta.7. Keep the existing configuration entry, token and Windows agent. This keeps the PC paired.
- **Home Assistant and Matterbridge together:** Open **Settings > System > Backups**, select the named pre-test backup, select **Home Assistant** and **Matterbridge**, then restore. This also rolls back any other Home Assistant configuration changes made after that backup, so review the selection first. Home Assistant will restart. Do not delete the existing PC entry or reset the Windows agent.
- If you created a long-lived token solely for this preview, revoke it from your Home Assistant profile after removing the plugin. Unpair the Matterbridge device from Alexa if you no longer want it there. Restoring the pre-test backup does not revoke a token from an external service automatically.

## Espanol

Esta es una **prueba solo de la integracion de Home Assistant**. Conserva el agente Windows beta.10. No lo desinstales, no borres el PC de Home Assistant ni restablezcas el certificado o el codigo de vinculacion para actualizar. Beta.11 anade una guia de Alexa en el boton Configurar del dispositivo existente; no instala ni configura Matterbridge automaticamente. El control real con Alexa aun no esta validado.

### Antes de instalar

1. En Home Assistant, abre **Configuracion > Sistema > Copias de seguridad > Realizar copia de seguridad ahora > Manual**. Incluye la configuracion de Home Assistant y Matterbridge si esta instalado. Guardala en **Este sistema**. Espera a que termine, abre el detalle y confirma que ambos aparecen en **Selecciona que restaurar**. Conserva la clave de cifrado en privado.
2. Anota la version descargada de la integracion WakeLink/PC Power Free y ten a mano el ZIP publicado de esa version exacta como segunda via de retorno. En la primera prueba real, Home Assistant tenia beta.7 y Windows beta.10.
3. Comprueba que el interruptor de encendido del PC aparece en Home Assistant. No lo pulses solo para probar la guia: apagarlo apaga el PC.

### Instalar y probar la guia

1. Actualiza la integracion HACS `pc_power_free` a beta.11 o, para una prueba manual, sustituye solo los archivos de `/config/custom_components/pc_power_free` por los del ZIP beta.11. **No borres antes la entrada de integracion ni la carpeta.** Reinicia Home Assistant.
2. Abre **Configuracion > Dispositivos y servicios > WakeLink > tu PC existente > Configurar > Conectar con Alexa (prueba Matter)**. La guia muestra el identificador real del interruptor, aunque lo hayas renombrado.
3. Sigue la guia para instalar o abrir Matterbridge e instalar `matterbridge-hass`. Si Matterbridge ya esta vinculado con otro controlador, detente primero: el complemento puede exportar todas las entidades de Home Assistant al arrancar. Necesita un token de acceso de larga duracion a Home Assistant; crealo solo si confias en el complemento. Introducelo en Matterbridge, nunca en WakeLink. Usa `wss://` con certificado de confianza si Home Assistant sirve HTTPS; `ws://` envia el token sin cifrar y solo corresponde a una red local de confianza. No desactives la verificacion del certificado. No vincules Alexa todavia.
4. Limita el complemento al interruptor previsto: **Domain Whitelist = `switch`**, **Split Entities = ID del interruptor**, **Whitelist = el mismo ID**. Split Entities esta obsoleto; si ya no aparece, detente y consulta Split By Label. Antes de vincular, confirma en la vista previa que solo se muestra el interruptor previsto. Una lista blanca vacia puede exponer otros dispositivos.
5. Si el mismo PC esta expuesto con Emulated Hue, quita esa exposicion antes de vincular Matter para evitar duplicados. En **Settings** de Matterbridge, pon como interfaz Matter mDNS la que muestra **Home Assistant > Configuracion > Sistema > Red**. Escanea el QR Matter de Matterbridge en Alexa. No es el codigo de vinculacion del PC. Se requiere un Echo compatible y Home Assistant encendido permanentemente.
6. Revisa el estado en Alexa. Prueba el apagado solo despues de guardar tu trabajo y decidir expresamente apagar el PC. Terminar la guia no demuestra que Alexa funcione.

### Volver atras

- **Solo integracion:** reinstala la version anterior desde HACS si aparece o sustituye los archivos de `pc_power_free` con el ZIP publicado de esa version y reinicia Home Assistant. En la primera prueba real es beta.7. Conserva la entrada existente, el token y el agente Windows; asi no pierdes la vinculacion.
- **Home Assistant y Matterbridge:** en **Configuracion > Sistema > Copias de seguridad**, selecciona la copia anterior a la prueba, marca **Home Assistant** y **Matterbridge** y restaura. Tambien se perderan los cambios hechos en Home Assistant despues de esa copia; revisa la seleccion antes de confirmar. No borres la entrada del PC ni restablezcas el agente.
- Si creaste un token solo para esta prueba, revocalo desde tu perfil cuando elimines el complemento. Desvincula el dispositivo de Matterbridge en Alexa si ya no lo quieres. La restauracion no revoca por si sola credenciales usadas por otros servicios.
