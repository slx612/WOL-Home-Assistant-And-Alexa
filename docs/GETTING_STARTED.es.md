# Instalar WakeLink: Windows + Home Assistant

[English](GETTING_STARTED.en.md) | [Español](GETTING_STARTED.es.md) | [Elegir otro sistema](README.es.md#empieza-aquí)

**Necesitas:** PC Windows x64, permiso de administrador para instalar, Home Assistant con HACS y una red local de confianza que conecte ambos. Home Assistant debe seguir encendido en otro equipo cuando apagues este PC. Es una beta: guarda antes una copia de Home Assistant. Alexa es opcional y se configura después.

En Home Assistant, **Configuración** puede llamarse **Ajustes** según la versión/idioma.

## 1. Descargar el instalador

1. Abre las [publicaciones de WakeLink](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases).
2. Elige la publicación más reciente **con instalador Windows**, despliega **Assets** y descarga **`WakeLink-Windows-x64-Setup.exe`**.
3. No descargues por separado `PCPowerAgent.exe`, `PCPowerTray.exe`, `PCPowerSetup.exe` ni **Source code**. El antiguo `pcpowerfree-windows-x64-setup.exe` es una copia idéntica compatible con el actualizador, no otra app.

Si Windows avisa de una app desconocida, sigue [la comprobación SmartScreen](HELP.es.md#windows-smartscreen) antes de decidir ejecutarla. El instalador no tiene firma digital: no desactives la protección.

## 2. Instalar y activar WakeLink

1. Ejecuta el instalador y acepta la petición de administrador Windows tras comprobar su origen.
2. Elige español o inglés. Conserva las carpetas propuestas salvo que ya uses una instalación personalizada. Puedes desmarcar el **acceso directo del escritorio**.
3. Deja seleccionada **Abrir WakeLink** al terminar.
4. Para una instalación nueva, pulsa **Activar y continuar** en WakeLink. Si se abre otra ventana con permisos, acepta la petición Windows y repite ahí la acción cuando lo indique.
5. Espera a **El agente está activo**. Abrir el panel no equivale a activar el agente.

WakeLink prepara el agente, el acceso local del cortafuegos y el inicio con Windows. No debes meterlo manualmente en Inicio ni dejar el panel abierto. Después puedes abrir WakeLink desde Inicio o con **clic izquierdo** en la bandeja; el **clic derecho** abre el menú. Cambia el idioma con el selector **Idioma** de la app.

**Comprueba:** la app detecta el agente en marcha. Esto no prueba Alexa ni el encendido físico por Wake-on-LAN.

<a id="2-instala-la-integracion-de-home-assistant"></a>

## 3. Instalar la integración Home Assistant

[![Abrir WakeLink en HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=slx612&repository=WOL-Home-Assistant-And-Alexa&category=integration)

HACS debe estar instalado y configurado. El botón abre la ficha de WakeLink: no lo instala automáticamente. Comprueba la dirección de Home Assistant antes de pulsar **Open link** (abrir enlace). Si pide la dirección de tu instancia, introduce la que usas normalmente para abrir Home Assistant, por ejemplo `http://homeassistant.local:8123`. Inicia sesión en tu Home Assistant si lo solicita.

1. Usa el botón anterior o abre **HACS**, busca `WakeLink` y entra en su ficha. Está en el catálogo predeterminado. Si tu catálogo no lo muestra, abre **... > Repositorios personalizados**, introduce `https://github.com/slx612/WOL-Home-Assistant-And-Alexa`, elige **Integración** y pulsa **Añadir**. Busca de nuevo.
2. Pulsa **Descargar** y selecciona la publicación que quieres probar. Si una beta está oculta, revisa el selector de versiones y la opción HACS para mostrar betas.
3. Reinicia **Home Assistant**, no el PC, cuando lo pida.
4. Abre **Configuración > Dispositivos y servicios**. Si ya tienes WakeLink, no lo instales otra vez: una integración admite varios equipos.

La lista HACS puede mostrar **icon not available**: es un [problema visual HACS conocido](KNOWN_ISSUES.md#espanol), no una instalación fallida. No debes introducir YAML, tokens manuales ni ejecutables Windows en HACS.

## 4. Vincular este PC

1. Vuelve a la app Windows y abre **Home Assistant** en el menú izquierdo.
2. Pulsa **Generar un código** si no hay uno activo. Autoriza el permiso de administrador si lo pide. Son seis cifras válidas durante diez minutos.
3. En **Configuración > Dispositivos y servicios** de Home Assistant, pulsa **Añadir** en el PC descubierto. Si falta, pulsa **Añadir integración > WakeLink** y elige el PC; si no encuentra ninguno, usa el formulario manual con su IP actual y puerto `58477`.
4. Comprueba nombre/IP y compara la **huella del certificado** Home Assistant con la página **Home Assistant** de Windows. Si no coinciden, detente.
5. Introduce las seis cifras y confirma. No pongas la contraseña Windows, un token Home Assistant ni el QR Matter.
6. Abre el dispositivo nuevo de WakeLink. Debes ver el interruptor **Power**, el botón **Restart** y los sensores **Boot time** y **Uptime**; esos nombres pueden aparecer en inglés.

**¿Ya está vinculado? Salta este apartado al actualizar.** Normalmente no necesitas IP fija; WakeLink redescubre los cambios de dirección local. Si una red de invitados/VLAN lo impide, consulta [Ayuda](HELP.es.md#home-assistant-no-encuentra-el-equipo).

## 5. Probar sin sorpresas

1. Con el PC encendido, comprueba su estado en Home Assistant. **No apagues Power para refrescar:** pide un apagado real.
2. Antes de probar el encendido, comprueba que la BIOS/UEFI y tarjeta de red del PC físico admiten y tienen activado Wake-on-LAN. Ethernet es el punto de partida más sencillo. WakeLink no puede configurar el firmware de todos los fabricantes: sigue las instrucciones del fabricante del equipo/tarjeta.
3. Guarda tu trabajo. Cuando quieras apagar de verdad, apaga **Power de este PC** y comprueba que se apaga.
4. Enciende ese interruptor y espera al arranque. Comprueba que el PC arranca físicamente y luego vuelve a aparecer conectado. Si no enciende, consulta [los problemas de encendido](HELP.es.md#apaga-pero-no-enciende), no repitas la vinculación.
5. Pulsa **Restart** solo cuando quieras reiniciar realmente el PC. No sirve para refrescar el estado.

Los sensores pueden aparecer no disponibles mientras el PC está apagado o arrancando. Se recuperan en otra consulta cuando el agente responde. Boot time es la fecha/hora del último arranque, no cuánto tarda en arrancar.

## 6. Actualizar o continuar con Alexa

En Windows abre **Actualizaciones > Buscar actualizaciones**, descarga el instalador ofrecido e instálalo **encima** de WakeLink. Actualiza aparte la integración en HACS y reinicia Home Assistant. No desinstales, no borres el dispositivo/certificados ni generes otro código solo para actualizar.

[Copias, regreso y problemas de actualización](HELP.es.md#actualizar-sin-volver-a-vincular) explican las dos partes. Las carpetas `PC Power Free` conservan la compatibilidad: no las cambies.

**¿Funciona desde Home Assistant?** Has terminado el control local. Solo si quieres voz, continúa con [Alexa y sus capturas](ALEXA.es.md). Matterbridge no es necesario para el control Home Assistant.
