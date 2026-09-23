# WakeLink

[English](../README.md) | [Espanol](README.es.md)

Control local y sin suscripcion del encendido, apagado y reinicio de equipos Windows y Linux desde Home Assistant. WakeLink es el nombre visible de la app de Windows y de la integracion de Home Assistant. Se conservan las rutas `PC Power Free` y el identificador `pc_power_free` para no perder los dispositivos vinculados.

## Descarga

**[Descargar para Windows x64: instalador beta.10](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/download/v0.2.0-beta.10/pcpowerfree-windows-x64-setup.exe)**

Usa un unico instalador, no los ejecutables por separado. Instala juntos el panel WakeLink, el agente y la bandeja.

**Home Assistant va por separado:** instala o actualiza WakeLink mediante [HACS](#hacs). La guia Matter esta en la prueba beta.11 para Home Assistant; Windows sigue en beta.10. [Instalacion y vuelta atras](MATTER-PREVIEW-beta.11.md#espanol). Las otras plataformas y el ZIP manual beta.10 estan en la [publicacion beta.10](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/tag/v0.2.0-beta.10).

### Actualizacion beta.10

`0.2.0-beta.10` es una **version preliminar publica**. Incluye el panel WakeLink, las correcciones del certificado y los accesos directos de beta.8, y abre el panel con clic izquierdo en la bandeja. El derecho mantiene el menu. El buscador de actualizaciones ofrece la descarga directa del instalador.

La actualizacion desde beta.5 hasta beta.9 reutiliza la instalacion: **no desinstales, no restablezcas las credenciales ni vuelvas a vincular**. Conserva puerto, token, identificador de equipo y certificado/clave TLS existentes. Consulta la [guia beta.10](WINDOWS-beta.10.md#espanol).

Siguen pendientes las pruebas manuales y los ciclos de energia de beta.10. Beta.11 solo cambia la integracion de Home Assistant y no da por validado el control desde Alexa.

## Que es

Este proyecto cubre el flujo local completo:

- Instalar un agente local en Windows o Linux
- Detectar automaticamente ese dispositivo en Home Assistant
- Vincularlo con un codigo temporal
- Encenderlo por Wake-on-LAN si el hardware lo soporta
- Apagarlo o reiniciarlo por red local
- Exponerlo a Alexa a traves de Home Assistant sin pagar una suscripcion de terceros

El control desde Home Assistant es local, sin suscripcion ni puertos abiertos a Internet. El reconocimiento de voz de Alexa puede requerir conexion con Amazon.

## Incluye

- Una integracion personalizada para Home Assistant en [`custom_components/pc_power_free`](../custom_components/pc_power_free)
- Un nucleo compartido multiplataforma en [`agent_core`](../agent_core)
- Un agente para Windows en [`windows_agent`](../windows_agent)
- Un agente experimental para Linux en [`linux_agent`](../linux_agent)
- Un unico instalador para Windows, enlazado arriba
- Un ZIP de la integracion de Home Assistant en la publicacion, como alternativa a HACS
- Un bundle experimental del agente Linux publicado como asset de release en GitHub: `pcpowerfree-linux-agent.tar.gz`

## Como funciona

### Encendido

1. Home Assistant envia un paquete Wake-on-LAN.
2. El equipo arranca si BIOS o UEFI y el sistema operativo estan bien configurados.

### Apagado y reinicio

1. Home Assistant llama al agente local de Windows o Linux.
2. El agente valida la red de origen y el token interno.
3. Ejecuta el comando local de apagado o reinicio.

### Descubrimiento y vinculacion

1. El agente local anuncia el dispositivo por `zeroconf` en la red.
2. Home Assistant lo detecta automaticamente.
3. El usuario introduce un codigo temporal de 6 digitos mostrado por la herramienta local de setup.
4. Home Assistant intercambia ese codigo por el token interno y guarda la configuracion.

## Requisitos

- Home Assistant en la misma red local
- Un equipo Windows o Linux
- Soporte Wake-on-LAN si quieres encender desde apagado completo
- Home Assistant `2026.3` o superior si quieres que se vea el logo incluido en `custom_components/.../brand/`
- Alexa es opcional; su ruta mediante Home Assistant sigue siendo experimental

## Instalacion en Windows

La descarga anterior instala beta.10. El siguiente flujo requiere Windows x64.

### Primera configuracion (beta.10)

1. Ejecuta el instalador beta.10 una sola vez, elige espanol o ingles y decide si quieres crear un acceso directo en el escritorio. La casilla viene desmarcada. Windows pedira permiso de administrador para instalar.
2. Deja marcada la opcion **Abrir WakeLink** al finalizar. El panel abre la configuracion inicial: revisa los datos del PC y la red, el acceso del firewall y las opciones de inicio. Esto configura la app ya instalada; no es una segunda instalacion.
3. Pulsa **Activar y continuar**: se detecta la red, se configura el acceso local y se activa el inicio automatico. Vincula con Home Assistant en una red de confianza: compara la huella del certificado mostrada en WakeLink e introduce el codigo antes de diez minutos. El estado del agente no demuestra por si solo que WOL o Alexa funcionen.

### Actualizar desde beta.5 hasta beta.9

**No desinstales.** Guarda una copia de la carpeta de datos, cierra el panel y ejecuta el instalador beta.10 sobre la instalacion existente. Conserva las ubicaciones de instalacion y datos, normalmente `C:\Program Files\PC Power Free` y `C:\ProgramData\PC Power Free`.

La pantalla final informa de que se han conservado los ajustes y la vinculacion. Su opcion marcada abre la bandeja **y** el panel, no el asistente inicial; no necesitas otro codigo ni repetir la configuracion. Se mantienen puerto, token, identificador del equipo, certificado/clave TLS existentes, proteccion y opciones de inicio. Si una version antigua no tiene archivos TLS, se crean durante la migracion; los certificados existentes no deben sustituirse. Un inicio automatico desactivado sigue desactivado. El instalador no solicita reiniciar Windows.

Antes de probar, consulta la [guia beta.10](WINDOWS-beta.10.md#espanol). Si Home Assistant sigue en beta.5/6, sigue por separado la [guia beta.7 de la integracion](UPGRADE-beta.7.md#espanol) para compatibilidad HTTPS; no borres el dispositivo existente.

El panel admite ingles y espanol. La primera apertura usa el idioma del instalador; las actualizaciones no cambian el idioma guardado en la app. El acceso directo de escritorio es opcional y se llama `WakeLink`; se eliminan los enlaces antiguos que apuntan a esta instalacion. `PCPowerSetup.exe` es el nombre interno del panel, no otro instalador. El inicio del agente y la bandeja mantienen sus funciones; abrir el panel mas tarde no deberia pedir permiso de administrador solo para consultarlo.

### SmartScreen y actualizaciones

La vista previa no tiene firma digital. SmartScreen puede mostrar una advertencia de app desconocida o editor desconocido. Verifica el origen y la suma SHA-256 proporcionada antes de decidir continuar; una suma coincidente no es una firma del editor. No desactives antivirus, SmartScreen ni las politicas de tu organizacion. La firma gratuita para el proyecto de codigo abierto sigue pendiente y tampoco garantiza que desaparezcan todas las advertencias. Consulta la [explicacion de Microsoft sobre SmartScreen](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

Buscar actualizaciones requiere Internet; usar el panel local no depende de GitHub. Una comprobacion sin conexion no debe mostrarse como "actualizado". La bandeja pide confirmacion antes de abrir la descarga y nunca ejecuta el instalador automaticamente.

### Avanzado: ejecutables separados

`PCPowerAgent.exe`, `PCPowerTray.exe` y `PCPowerSetup.exe` son solo para desarrollo o diagnostico avanzado. El instalador incluye los tres; no necesitas descargarlos ni abrirlos por separado para instalar o actualizar normalmente.

## Instalacion en Linux

El empaquetado para Linux sigue siendo `experimental` y basado en codigo fuente, pero la ruta con Home Assistant ya se ha validado en una Ubuntu real.

Ruta recomendada:

1. Descarga el bundle Linux `pcpowerfree-linux-agent.tar.gz` desde la ultima prerelease de GitHub, o copia `agent_core` y `linux_agent` desde este repositorio
2. Extraelo bajo `/opt/pc-power-free`
3. Crea alli un entorno virtual de Python
4. Instala las dependencias de runtime: `ifaddr` y `zeroconf`
5. Ejecuta el CLI de setup y deja que genere `/etc/pc-power-free/config.json`
6. Instala `linux_agent/pcpowerfree-agent.service` como unidad `systemd`
7. Arranca y habilita el servicio
8. Vincula el dispositivo en Home Assistant con el codigo temporal que muestra el CLI

Ejemplo para Ubuntu o Debian:

```bash
sudo mkdir -p /opt/pc-power-free /etc/pc-power-free
sudo tar -xzf pcpowerfree-linux-agent.tar.gz -C /opt/pc-power-free
sudo python3 -m venv /opt/pc-power-free/.venv
sudo /opt/pc-power-free/.venv/bin/python -m pip install ifaddr zeroconf cryptography
sudo /opt/pc-power-free/.venv/bin/python /opt/pc-power-free/linux_agent/setup_cli.py --config /etc/pc-power-free/config.json
sudo cp /opt/pc-power-free/linux_agent/pcpowerfree-agent.service /etc/systemd/system/pcpowerfree-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now pcpowerfree-agent.service
sudo systemctl status pcpowerfree-agent.service --no-pager
```

Despues de arrancar el servicio:

- abre Home Assistant y anade `PC Power Free`
- espera a que el host Linux aparezca automaticamente, o anadelo por IP
- introduce el codigo temporal que te ha mostrado `setup_cli.py`

Comprobaciones utiles en Linux:

```bash
curl --cacert /etc/pc-power-free/agent-cert.pem https://127.0.0.1:58477/v1/discovery
sudo journalctl -u pcpowerfree-agent.service -n 50 --no-pager
```

Notas:

- el puerto local por defecto es `58477`
- vuelve a ejecutar `linux_agent/setup_cli.py` cuando necesites un codigo de vinculacion nuevo
- si usas `ufw`, abre `58477/tcp`
- el servicio de ejemplo espera que el runtime este bajo `/opt/pc-power-free`

## Instalacion en Home Assistant

### Manual

1. Copia `custom_components/pc_power_free` dentro de `/config/custom_components/`
2. Reinicia Home Assistant
3. Ve a `Ajustes > Dispositivos y servicios`
4. Anade `WakeLink`

### HACS

El repositorio esta preparado para HACS con [`hacs.json`](../hacs.json).

1. En HACS, busca `WakeLink` en la lista de integraciones.
2. Instala la ultima version preliminar de Home Assistant (beta.11 para la guia Matter). Si actualizas desde una beta anterior, conserva el dispositivo y la vinculacion; la [guia beta.7](UPGRADE-beta.7.md#espanol) explica la migracion HTTPS desde beta.5/6.
3. Reinicia Home Assistant. Si ya estaba instalada, se conserva la vinculacion.

Si la tarjeta de la integracion sigue mostrando el icono generico, lo normal es que tu Home Assistant sea anterior a `2026.3`, que es la primera version con soporte para assets `brand/` incluidos dentro de una custom integration.

El repositorio ya figura en la lista predeterminada de HACS: [la solicitud #7156 fue aceptada](https://github.com/hacs/default/pull/7156). Anadir un repositorio personalizado es una alternativa, no un requisito.

Checklist: [`docs/HACS_PUBLISHING.md`](HACS_PUBLISHING.md)

## Vinculacion con Home Assistant

### Flujo recomendado

1. Instala primero el agente local en Windows o Linux
2. Termina la instalacion local y deja visible el codigo temporal
3. Instala o abre el flujo de la integracion en Home Assistant
4. Espera a que el dispositivo aparezca automaticamente
5. Selecciona el dispositivo detectado
6. Introduce el codigo temporal mientras siga activo
7. Confirma el nombre del dispositivo

### Si falla el descubrimiento automatico

Tambien hay un flujo manual por IP:

1. `Anadir integracion`
2. `WakeLink`
3. `Configurar por IP manualmente`
4. Introduce la IP actual del host y el puerto del agente
5. Introduce el codigo de vinculacion

Si el codigo caduca:

- en Windows, abre WakeLink y genera un codigo nuevo en su pagina Home Assistant para una primera vinculacion, no para una actualizacion normal
- en Linux, vuelve a ejecutar `linux_agent/setup_cli.py`

## Alexa

La ruta experimental de beta.11 es `Alexa + Matterbridge + Home Assistant`. Abre **Configurar > Conectar con Alexa (prueba Matter)** en el PC ya vinculado. La guia no instala Matterbridge automaticamente; consulta [los pasos detallados y la vuelta atras](MATTER-PREVIEW-beta.11.md#espanol). No expongas por error otras entidades de Home Assistant. Aun no se ha validado el control completo con Alexa.
Todavia no esta validada de extremo a extremo en una instalacion real, asi que ahora mismo debe considerarse `experimental`.

La antigua opcion manual `emulated_hue` queda como alternativa experimental. No expongas el mismo PC por los dos puentes a la vez.

Ejemplo:

```yaml
emulated_hue:
  listen_port: 80
  entities:
    switch.pc_despacho_power:
      name: "PC Despacho"
      hidden: false
```

## Estructura del repositorio

```text
agent_core/
custom_components/pc_power_free/
linux_agent/
windows_agent/
release_assets/
hacs.json
README.md
docs/README.es.md
LICENSE
```

## Archivos principales

- [`agent_core/common.py`](../agent_core/common.py)
- [`custom_components/pc_power_free/config_flow.py`](../custom_components/pc_power_free/config_flow.py)
- [`custom_components/pc_power_free/api.py`](../custom_components/pc_power_free/api.py)
- [`linux_agent/pc_power_agent.py`](../linux_agent/pc_power_agent.py)
- [`linux_agent/setup_cli.py`](../linux_agent/setup_cli.py)
- [`windows_agent/pc_power_agent.py`](../windows_agent/pc_power_agent.py)
- [`windows_agent/setup_wizard_gui.py`](../windows_agent/setup_wizard_gui.py)
- [`windows_agent/build-exe.ps1`](../windows_agent/build-exe.ps1)
- [`windows_agent/build-installer.ps1`](../windows_agent/build-installer.ps1)
- [`build-release-assets.ps1`](../build-release-assets.ps1)

## Compilar de nuevo

### Ejecutables de Windows

```powershell
.\windows_agent\build-exe.ps1 -Clean
```

### Instalador de Windows

```powershell
.\windows_agent\build-installer.ps1
```

### Assets de release

```powershell
.\build-release-assets.ps1
```

## Seguridad

- No expongas el puerto `58477` a Internet
- Limita el acceso a la IP de Home Assistant o, como minimo, a tu LAN
- Usa VPN si necesitas acceso remoto
- El codigo de vinculacion es temporal

## Estado de publicacion

Estado actual para el repositorio `default` de HACS:

- Incluido en HACS default tras [aceptarse la solicitud #7156](https://github.com/hacs/default/pull/7156).
- Instalador Windows: `v0.2.0-beta.10`. Prueba de la guia Matter en Home Assistant: `v0.2.0-beta.11`. Siguen pendientes las [pruebas manuales de Windows](WINDOWS-beta.10.md#espanol).

Pendiente antes de considerarlo realmente final:

- Pruebas reales de instalacion/actualizacion beta.10, HA/Alexa y ciclos de energia.
- modelo de privilegios para acciones de energia DSM
