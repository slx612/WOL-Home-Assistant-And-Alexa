# WakeLink

![Logo de WakeLink](https://raw.githubusercontent.com/slx612/WOL-Home-Assistant-And-Alexa/main/custom_components/pc_power_free/brand/logo.png)

[English](../README.md) | [Español](README.es.md)

Enciende, apaga o reinicia tu ordenador o NAS desde Home Assistant sin una suscripción de WakeLink. Instala la aplicación WakeLink en ese equipo y su integración en Home Assistant. Vincúlalos una vez mediante un código temporal.

**Home Assistant es obligatorio y debe seguir encendido en otro equipo cuando apagues el ordenador/NAS controlado.** Alexa es opcional y necesita la aplicación independiente Matterbridge; un Echo y un PC apagado no bastan.

## Empieza aquí

Elige **una** guía para tu equipo. Incluye Home Assistant, vinculación, primera prueba y actualización. No necesitas las guías de los otros sistemas.

| Tu equipo | Sigue esta guía | Archivo que se instala |
| --- | --- | --- |
| PC Windows x64 | [Windows + Home Assistant](GETTING_STARTED.es.md) | `WakeLink-Windows-x64-Setup.exe` |
| PC Ubuntu 24.04 Desktop | [Ubuntu + Home Assistant](INSTALL_UBUNTU.es.md) | `WakeLink-Ubuntu-<version>.deb` |
| NAS Synology, DSM 7 | [DSM + Home Assistant](INSTALL_DSM.es.md) | `pcpowerfree-dsm-noarch-<version>.spk` |

<a id="descarga"></a>

**Descargas:** abre la [beta.13](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.13), despliega **Assets** y elige el archivo de tu sistema. Incluye instaladores Windows, Ubuntu Desktop y DSM, además del ZIP de Home Assistant. Los paquetes DSM antiguos no incluyen el asistente actual. Sigue la guía de tu sistema; actualizar conserva la vinculación existente.

En HACS, busca `WakeLink`. Instala la integración **una sola vez** y vincula cada equipo por separado. Para una instalación normal no descargues los ejecutables individuales Windows ni los archivos **Source code** de GitHub.

[![Abrir WakeLink en HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=slx612&repository=WOL-Home-Assistant-And-Alexa&category=integration)

**¿Ya tienes HACS instalado y configurado?** Pulsa el botón, comprueba la dirección de Home Assistant y pulsa **Open link** (abrir enlace); después, **Descargar** en HACS. Si pide la dirección de tu instancia, introduce la que usas normalmente para abrir Home Assistant. Inicia sesión en tu Home Assistant si lo solicita. Reinicia Home Assistant y continúa con la vinculación de la guía de tu sistema. El botón abre la ficha: no instala HACS ni vincula equipos automáticamente.

## Después de instalar

| Quieres... | Abre |
| --- | --- |
| Conectar el equipo vinculado con Alexa | [Alexa: guía con capturas](ALEXA.es.md) |
| Resolver detección, energía, actualizaciones o SmartScreen | [Ayuda y actualizaciones](HELP.es.md) |
| Entender por qué falta el icono en la lista de HACS | [Problema conocido de HACS](KNOWN_ISSUES.md#espanol) |
| Cambiar de idioma o encontrar otra guía | [Documentación](README.md) |

**¿Vas a actualizar? Instala encima de la aplicación/paquete existente, actualiza WakeLink en HACS y reinicia Home Assistant. No desinstales, no borres el dispositivo ni lo vincules de nuevo solo para actualizar.** Los identificadores, directorios y archivos internos antiguos conservan las conexiones; el nombre visible es WakeLink.

## Qué esperar

- **Encender:** Home Assistant envía Wake-on-LAN. El hardware, firmware y red deben admitirlo. Vincular no demuestra que pueda encenderse. WakeLink no arranca una VM apagada mediante su hipervisor.
- **Apagar/reiniciar:** el agente en marcha recibe una petición local autenticada. Guarda antes el trabajo. DSM necesita el permiso inicial explicado en su guía.
- **Alexa:** Home Assistant -> Matterbridge + `matterbridge-hass` -> Echo/Alexa compatible con Matter. Se ha comunicado que el descubrimiento funciona; falta una prueba completa de apagado y encendido con un Echo real. Matterbridge necesita un token con acceso amplio a Home Assistant y debe seguir encendido. No hay suscripción de terceros, pero la voz de Alexa puede necesitar Internet.
- **Beta:** se comprobó la actualización del escritorio Ubuntu en una VM; falta la instalación limpia. Se ha comunicado que la instalación limpia y los controles DSM funcionan en la VM DSM 7.2; faltan otras versiones DSM, el encendido de un NAS físico y la vuelta a un paquete anterior.

Normalmente no necesitas IP fija en el equipo. Usa una red de confianza y nunca expongas el puerto del agente a Internet. Windows puede avisar porque el instalador no tiene firma digital: [compruébalo sin desactivar protecciones](HELP.es.md#windows-smartscreen).

## Desarrollo

La instalación de usuario termina en las guías anteriores. Para código y compilación: [Windows](../windows_agent), [Linux y servidores manuales](../linux_agent/README.md), [paquetes DSM](../dsm_package/README.md) y [lista de publicación/HACS](HACS_PUBLISHING.md). Las [notas históricas](HISTORY.md) no son pasos de instalación.

Informa de problemas en [GitHub Issues](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/issues) indicando sistema, versiones, paso que falla y error sin datos privados. No incluyas contraseñas, tokens ni códigos de vinculación.
