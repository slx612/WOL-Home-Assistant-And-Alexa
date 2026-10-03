# Instalar WakeLink en Ubuntu

[English](INSTALL_UBUNTU.en.md) | [Español](INSTALL_UBUNTU.es.md) | [Elegir otro sistema](README.es.md#empieza-aquí)

Esta guía es para **Ubuntu 24.04 Desktop**, con escritorio gráfico. Para un servidor sin escritorio, consulta la [instalación manual](../linux_agent/README.md#manual-installation-for-servers). Necesitas HACS en Home Assistant y ambos equipos en la misma red local de confianza. Home Assistant debe seguir encendido en otro equipo cuando apagues este PC. Alexa se configura después. En Home Assistant, **Configuración** puede llamarse **Ajustes** en algunas versiones.

**Estado:** el instalador gráfico está disponible en la **beta.13**. Se ha probado una actualización sobre una instalación manual en la VM de Ubuntu; falta probar una instalación limpia completa. La vinculación no demuestra por sí sola que el hardware admita Wake-on-LAN.

## 1. Qué archivo necesitas

Descarga **[WakeLink-Ubuntu-0.2.0-beta.13.deb](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/download/v0.2.0-beta.13/WakeLink-Ubuntu-0.2.0-beta.13.deb)** desde los [Assets de beta.13](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.13). Los siguientes tendrán el formato `WakeLink-Ubuntu-<version>.deb`. No uses el paquete fuente Linux, un `.exe` Windows, un `.spk` DSM ni los archivos **Source code**. No necesitas compilar nada.

Guarda una copia de seguridad de Home Assistant antes de probar la beta. El ordenador necesita Internet durante la instalación para descargar las dependencias de Ubuntu.

## 2. Instalar y abrir la aplicación

1. Abre **Archivos** y entra en la carpeta donde está el `.deb`.
2. Ábrelo con un instalador de paquetes y pulsa **Instalar**. Introduce la contraseña cuando Ubuntu pida autorización. Si no tienes una aplicación que instale ese archivo, usa la alternativa de terminal que aparece abajo.
3. Abre el menú de aplicaciones de Ubuntu y busca **WakeLink**.
4. En la ventana WakeLink, elige **ES** para español o **EN** para inglés.
5. Pulsa **Activar WakeLink** y autoriza la petición de Ubuntu. Esta autorización configura el servicio; no apaga el ordenador.
6. Espera a que aparezca **Agente en marcha**. El servicio arrancará con Ubuntu; no añadas la ventana al inicio del sistema ni necesitas dejarla abierta.

Si el archivo no se abre con un instalador, abre un terminal **en la carpeta que contiene el `.deb`** y ejecuta lo siguiente, sustituyendo `NOMBRE_DEL_ARCHIVO.deb` por su nombre real:

```sh
sudo apt install ./NOMBRE_DEL_ARCHIVO.deb
```

## 3. Vincular con Home Assistant

[![Abrir WakeLink en HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=slx612&repository=WOL-Home-Assistant-And-Alexa&category=integration)

HACS debe estar instalado y configurado. El botón abre la ficha de WakeLink: no lo instala automáticamente. Comprueba la dirección de Home Assistant antes de pulsar **Open link** (abrir enlace). Si pide la dirección de tu instancia, introduce la que usas normalmente para abrir Home Assistant, por ejemplo `http://homeassistant.local:8123`. Inicia sesión en tu Home Assistant si lo solicita.

1. Usa el botón anterior o en Home Assistant abre **HACS**, busca `WakeLink`, entra en su ficha y pulsa **Descargar**. Elige la publicación que quieres probar; activa la opción HACS de mostrar betas si hace falta. Reinicia Home Assistant cuando lo pida. Si la búsqueda no lo encuentra, usa **... > Repositorios personalizados**, introduce `https://github.com/slx612/WOL-Home-Assistant-And-Alexa`, elige **Integración**, pulsa **Añadir** y busca de nuevo. La integración se instala una sola vez, aunque tengas varios equipos.
2. En WakeLink, usa el código de seis cifras que se muestra tras activar el agente. Si no aparece o ha caducado, pulsa **Generar código de vinculación** y autoriza la petición de Ubuntu.
3. En Home Assistant, abre **Configuración > Dispositivos y servicios** y selecciona el ordenador descubierto. Si no aparece, pulsa **Añadir integración > WakeLink**. Comprueba que es tu ordenador, no otro dispositivo de la red.
4. Introduce el código antes de diez minutos. Si el formulario pide IP porque no hay descubrimiento, usa la del ordenador y el puerto `58477`, salvo que lo hayas cambiado.
5. Comprueba que el ordenador aparece con **Power**, **Restart**, **Boot time** y **Uptime** (pueden conservar nombres ingleses). **No lo apagues solo para comprobar el estado.**

**Comprueba:** el ordenador aparece en Home Assistant. El formulario de vinculación muestra su huella TLS; verifica nombre/IP y vincula solo en la red de confianza. La ventana Ubuntu de esta prueba todavía no muestra la huella para compararla lado a lado.

El código vincula Home Assistant; no es la contraseña de Ubuntu. Una actualización no necesita otro código. Normalmente no necesitas IP fija, pero las redes de invitados y las VLAN pueden impedir el descubrimiento.

## 4. Probar el apagado y el encendido

1. Guarda el trabajo y detén tareas que no quieras interrumpir.
2. Cuando quieras realizar un apagado real, apaga el interruptor del ordenador en Home Assistant.
3. Después, enciende ese interruptor para probar Wake-on-LAN.

Pulsa **Restart** solo si quieres reiniciar de verdad. Durante el arranque los sensores pueden aparecer no disponibles y se recuperan en otra consulta (30 segundos por defecto). **Boot time** es la fecha/hora del último arranque; **Uptime**, el tiempo desde ese arranque.

Si el apagado funciona pero no se enciende, revisa Wake-on-LAN en BIOS/UEFI y en la tarjeta de red, preferiblemente Ethernet. WakeLink no configura automáticamente el firmware ni los ajustes persistentes de encendido de la tarjeta Ubuntu. Una VM no equivale a un PC físico: WakeLink no arranca máquinas virtuales a través de su hipervisor.

## 5. Actualizar y resolver problemas

1. Abre **WakeLink** desde el menú de aplicaciones Ubuntu. Busca publicaciones oficiales automáticamente al abrir la ventana; no busca cuando está cerrada.
2. Para repetir la consulta, pulsa **Buscar actualizaciones** en la parte superior.
3. Si hay una nueva, pulsa **Instalar actualización**, confirma y acepta la autorización de administrador de Ubuntu. WakeLink descarga el instalador Ubuntu, verifica su suma SHA-256 de GitHub y la identidad del paquete, y lo instala mediante el gestor de paquetes Ubuntu.
4. Espera el mensaje de finalización y abre WakeLink de nuevo. El servicio se reinicia automáticamente. **No generes otro código de vinculación.**

Este actualizador se incluye en la **beta.13**. Si tienes el escritorio local beta.12 anterior, puede ofrecerte beta.13. Las instalaciones sin actualizador necesitan instalar este `.deb` encima una vez. La ausencia de un instalador publicado adecuado se muestra como error, no como «estás actualizado». Los fallos de red y la cancelación del permiso no sustituyen la instalación actual. Las betas pueden ofrecer betas; las versiones estables solo ofrecen versiones estables. El actualizador del sistema Ubuntu no descubre WakeLink por su cuenta: no se ha configurado un repositorio APT. La instalación siempre necesita tu aprobación.

También puedes instalar un `.deb` oficial nuevo **encima** del anterior, sin desinstalar ni borrar el dispositivo de Home Assistant. Se conservan la configuración, los certificados y la vinculación de `/etc/pc-power-free/`. La prueba de actualización en la VM conservó los tres archivos exactamente. Ese nombre antiguo es interno, no otra aplicación. Consulta las [notas de versión](RELEASE_v0.2.0-beta.13.md) para conocer las pruebas realizadas y las pendientes.

| Lo que ves | Qué hacer |
| --- | --- |
| No hay código | Pulsa **Generar código de vinculación**, autoriza Ubuntu y vuelve a Home Assistant. |
| El agente no arranca | Revisa el resultado del instalador y si aceptaste **Activar WakeLink**. No borres la configuración. |
| Home Assistant no descubre el ordenador | Comprueba que el agente está en marcha y ambos equipos están en la misma red; usa la IP manual si hace falta. |
| Error de autorización de Ubuntu | Usa una sesión de escritorio capaz de mostrar la petición de administrador. Para un servidor sin escritorio, usa la guía manual. |

Conserva el `.deb` anterior y una copia protegida de `/etc/pc-power-free/` si quieres poder volver atrás. No publiques ese directorio: contiene credenciales. La restauración de una versión anterior aún debe probarse antes de considerarla garantizada.

Para actualizar HACS, copias, vuelta atrás y errores de red, consulta [Ayuda y actualizaciones](HELP.es.md). Si falta el icono en la lista HACS, es un [problema visual conocido](KNOWN_ISSUES.md#espanol), no una instalación fallida.

Cuando esto funcione, continúa con la [guía de Alexa](ALEXA.es.md). Matterbridge no es necesario para controlar el ordenador desde Home Assistant.
