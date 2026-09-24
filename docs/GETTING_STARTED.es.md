# Instalar WakeLink: Windows + Home Assistant

[English](GETTING_STARTED.en.md) | [Espanol](GETTING_STARTED.es.md) | [Inicio](README.es.md)

Este es el recorrido basico. **Alexa es opcional** y tiene [otra guia](ALEXA.es.md). Necesitas un PC Windows x64, Home Assistant y ambos en la misma red local de confianza. Para encender desde un apagado completo, el PC debe admitir Wake-on-LAN en la BIOS/UEFI y en el adaptador de red.

## 1. Instala la aplicacion de Windows

1. Abre las [releases de WakeLink](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases). En la beta mas reciente con instalador de Windows, descarga **`WakeLink-Windows-x64-Setup.exe`**. No descargues `PCPowerAgent.exe`, `PCPowerTray.exe` ni `PCPowerSetup.exe` por separado. El antiguo `pcpowerfree-windows-x64-setup.exe` es una copia identica para los actualizadores ya instalados.
2. Ejecuta el instalador. Elige espanol o ingles y, si quieres, el acceso directo del escritorio. Windows pedira permiso de administrador para instalar el agente y la regla del cortafuegos. Deja marcada la opcion **Abrir WakeLink** en la ultima pantalla.
3. En WakeLink, pulsa **Activar y continuar**. Se configuran el arranque automatico y la red local. No tienes que poner la aplicacion en el inicio de Windows manualmente.
4. Si SmartScreen avisa de que la aplicacion es desconocida, comprueba que el archivo procede de la release de este proyecto y compara su SHA-256 con `SHA256SUMS.txt` de esa release. El instalador no esta firmado; una suma coincidente tampoco acredita al autor. No desactives SmartScreen ni el antivirus.

## 2. Instala la integracion de Home Assistant

1. En Home Assistant, abre **HACS**, busca `WakeLink` y descarga la integracion. Si HACS ofrece elegir version, selecciona la beta mas reciente. Reinicia Home Assistant cuando lo pida.
2. Abre **Configuracion > Dispositivos y servicios**. Selecciona el PC WakeLink detectado. Si no aparece, pulsa **Anadir integracion**, busca `WakeLink` y elige el PC detectado desde ahi.
3. En la aplicacion de Windows, abre la pagina **Vincular** y genera un codigo temporal de seis cifras. Compara la huella del certificado que muestran ambas pantallas y escribe el codigo en Home Assistant antes de diez minutos.
4. Comprueba que el PC y su interruptor aparecen bajo WakeLink en Home Assistant. Eso confirma la vinculacion, pero aun no demuestra que Wake-on-LAN funcione en tu equipo.

**Normalmente no necesitas una IP fija.** WakeLink detecta la direccion en la red local. Si la deteccion no atraviesa tu VLAN o red de invitados, usa la opcion de host manual y considera reservar una IP por DHCP en el router; la MAC por si sola no permite dirigir una orden normal de apagado a una IP desconocida.

## 3. Prueba sin sorpresas

1. Con el PC encendido, comprueba que la app WakeLink indica que el agente local funciona. **No** pulses el interruptor de Home Assistant solo para comprobar su estado: apagarlo pide un apagado real.
2. Guarda tu trabajo. Cuando estes preparado, apaga el interruptor en Home Assistant y comprueba que el PC se apaga.
3. Enciende el interruptor para probar Wake-on-LAN. Si no arranca, revisa la BIOS/UEFI, el adaptador y el trafico broadcast de tu red. La vinculacion no puede activar un hardware que no lo admita.

## Actualizar o volver atras

Instala el nuevo instalador de Windows **encima** del actual; despues actualiza la integracion en HACS y reinicia Home Assistant. No desinstales ni borres el dispositivo: podrias perder la vinculacion. Para volver a la version anterior, reinstalala desde HACS si aparece o sustituye solo los archivos de la integracion con el ZIP publicado de esa version y reinicia Home Assistant. Conserva la entrada del dispositivo y los datos de Windows. Se recomienda crear una copia de seguridad de Home Assistant antes de probar una beta.

El directorio antiguo `PC Power Free`, el identificador `pc_power_free` y el nombre del instalador son detalles de compatibilidad, no un segundo programa.
