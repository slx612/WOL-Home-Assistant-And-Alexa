# WakeLink 0.2.0-beta.12

[English](#english) | [Espanol](#espanol)

## English

This beta brings consistent WakeLink icons to the Windows tray, Home Assistant integration and DSM package. The Windows app's pairing instructions and Start menu use the WakeLink name. The Home Assistant Alexa preview now links to the correct language's step-by-step guide. Current installation and Alexa guides are available in English and Spanish; older beta notes are clearly archived.

**Downloads:** `WakeLink-Windows-x64-Setup.exe` is the complete Windows installer. `WakeLink-Home-Assistant.zip` is the manual Home Assistant package; HACS users should update WakeLink in HACS instead. `pcpowerfree-windows-x64-setup.exe` is a byte-identical compatibility copy for the update checker in older Windows versions. Linux source and DSM packages remain experimental. Check `SHA256SUMS.txt` before installing. The Windows installer is still unsigned, so SmartScreen may warn.

**Update without pairing again:** Install the new Windows installer over the old one, update the existing HACS integration, and restart Home Assistant. Do not uninstall the Windows app, delete the Home Assistant device or reset its credentials. The internal `pc_power_free` ID and old data path remain unchanged.

Start with the [Windows + Home Assistant guide](GETTING_STARTED.en.md); Alexa is covered separately in the [Matterbridge guide](ALEXA.en.md). Matterbridge and `matterbridge-hass` are **not bundled**. The Alexa route is still experimental and has **not** been validated end to end on an Echo. No shutdown or wake test has been performed by publishing this beta.

## Espanol

Esta beta unifica los iconos de WakeLink en la bandeja de Windows, la integracion de Home Assistant y el paquete DSM. Las instrucciones de vinculacion de Windows y el menu Inicio usan el nombre WakeLink. La prueba de Alexa en Home Assistant enlaza la guia paso a paso del idioma correcto. Hay guias actuales en ingles y espanol; las notas de betas antiguas quedan marcadas como historicas.

**Descargas:** `WakeLink-Windows-x64-Setup.exe` es el instalador completo de Windows. `WakeLink-Home-Assistant.zip` es el paquete manual; si usas HACS, actualiza WakeLink desde HACS. `pcpowerfree-windows-x64-setup.exe` es una copia identica para el actualizador de versiones anteriores de Windows. Linux y DSM siguen siendo experimentales. Comprueba `SHA256SUMS.txt` antes de instalar. El instalador de Windows sigue sin firma, por lo que SmartScreen puede avisar.

**Actualiza sin volver a vincular:** Instala el nuevo instalador de Windows encima del anterior, actualiza la integracion existente en HACS y reinicia Home Assistant. No desinstales la app de Windows, no borres el dispositivo de Home Assistant ni restablezcas sus credenciales. Se conservan el identificador interno `pc_power_free` y el directorio antiguo de datos.

Empieza con la [guia de Windows + Home Assistant](GETTING_STARTED.es.md); Alexa tiene su propia [guia de Matterbridge](ALEXA.es.md). Matterbridge y `matterbridge-hass` **no vienen incluidos**. El recorrido con Alexa sigue siendo experimental y **no se ha validado** de principio a fin con un Echo. Publicar esta beta no supone haber probado el apagado ni el encendido real.
