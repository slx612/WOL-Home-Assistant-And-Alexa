# WakeLink

[English](../README.md) | [Espanol](README.es.md)

Enciende y apaga un PC desde Home Assistant sin suscripcion. WakeLink instala una pequena aplicacion en el PC y una integracion independiente en Home Assistant. Alexa es una **opcion experimental** a traves de Matterbridge; no viene incorporada en WakeLink.

## Empieza aqui

1. [Instala WakeLink en Windows y vincula el PC con Home Assistant](GETTING_STARTED.es.md).
2. Si tambien quieres usar la voz, [conecta el PC vinculado con Alexa](ALEXA.es.md).

Descarga **`WakeLink-Windows-x64-Setup.exe`** de la beta mas reciente en [GitHub Releases](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases). **No descargues los tres `.exe` individuales** para una instalacion normal. El archivo antiguo `pcpowerfree-windows-x64-setup.exe` es una copia identica para los actualizadores instalados. En HACS, busca `WakeLink` para instalar la parte de Home Assistant. Normalmente no necesitas una IP fija: WakeLink detecta el PC en la red local.

## Que hace cada parte

- **Encender:** Home Assistant envia un paquete Wake-on-LAN. El PC y la red deben permitir el encendido desde apagado; WakeLink no puede cambiar la BIOS/UEFI.
- **Apagar/reiniciar:** Home Assistant contacta con el agente local del PC. Guarda el trabajo antes de probar el apagado.
- **Alexa:** El recorrido es Home Assistant -> Matterbridge + `matterbridge-hass` -> Echo/Alexa compatible. Matterbridge es una aplicacion aparte y necesita un token de Home Assistant con acceso amplio. **No es una instalacion de un clic y aun no hemos validado el recorrido completo con un Echo.** No hay suscripcion de terceros, pero el reconocimiento de voz de Alexa puede necesitar Internet.
- **Privacidad:** Las ordenes al PC quedan en tu red local. No abras el puerto del agente de WakeLink a Internet.

## Actualizaciones y compatibilidad

Instala el nuevo instalador de Windows encima del actual. Actualiza WakeLink en HACS y reinicia Home Assistant. **No desinstales, no borres el dispositivo de Home Assistant, no restablezcas las credenciales ni generes otro codigo solo para actualizar.** Se conservan los directorios antiguos `PC Power Free`, el identificador interno `pc_power_free` y el nombre historico del instalador para mantener las vinculaciones. El nombre visible es WakeLink.

Esto sigue siendo una **beta**. Windows SmartScreen puede advertir sobre el instalador sin firma: comprueba el origen y la suma SHA-256 de la release antes de decidir si ejecutarlo. No desactives SmartScreen ni el antivirus. La aplicacion comprueba si hay actualizaciones en GitHub, pero no ejecuta el instalador automaticamente.

Para paquetes manuales, experimentos Linux/DSM, restauracion y notas de betas antiguas, consulta el [indice de documentacion](README.md). Puedes informar de problemas en [GitHub Issues](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/issues).
