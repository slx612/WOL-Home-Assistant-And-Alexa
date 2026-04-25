# PC Power Free

![PC Power Free](../custom_components/pc_power_free/brand/logo.png)

Idioma:

- [English](../README.md)
- [Espanol](README.es.md)

Solucion local y sin suscripcion para controlar el encendido, apagado y reinicio de equipos Windows y Linux desde Home Assistant y Alexa.

Estado actual: `0.2.0-beta.5 preparado en el repositorio, rutas Windows y Linux con Home Assistant validadas en instalaciones reales, ruta Alexa aun pendiente de validacion real`.

Estado de publicacion:

- El codigo del repositorio apunta ahora a `v0.2.0-beta.5`
- La ultima prerelease publicada en GitHub es `v0.2.0-beta.4`, del 21 de abril de 2026
- La siguiente prerelease prevista es `v0.2.0-beta.5`
- La solicitud para el repositorio `default` de HACS ya esta abierta en `hacs/default#7156`
- Las rutas previstas de distribucion son: instalacion manual, custom repository de HACS, descargas prerelease de GitHub, instalador de Windows e instalacion experimental en Linux desde codigo fuente
- La unica validacion real que sigue pendiente es `Alexa + Home Assistant`

Novedades recientes:

- Runtime experimental para Linux con el mismo protocolo de descubrimiento y vinculacion que Windows
- Flujo de Home Assistant ya validado tanto contra Windows como contra Linux
- Puerto local por defecto movido a `58477`
- La app de Windows mantiene la proteccion desde bandeja y la comprobacion de actualizaciones

## Que es

Este proyecto cubre el flujo local completo:

- Instalar un agente local en Windows o Linux
- Detectar automaticamente ese dispositivo en Home Assistant
- Vincularlo con un codigo temporal
- Encenderlo por Wake-on-LAN si el hardware lo soporta
- Apagarlo o reiniciarlo por red local
- Exponerlo a Alexa a traves de Home Assistant sin pagar una suscripcion de terceros

No depende de la nube. No requiere abrir puertos a Internet.

## Incluye

- Una integracion personalizada para Home Assistant en [`custom_components/pc_power_free`](../custom_components/pc_power_free)
- Un nucleo compartido multiplataforma en [`agent_core`](../agent_core)
- Un agente para Windows en [`windows_agent`](../windows_agent)
- Un agente experimental para Linux en [`linux_agent`](../linux_agent)
- Un instalador completo para Windows en [`windows_agent/dist/pcpowerfree-windows-x64-setup.exe`](../windows_agent/dist/pcpowerfree-windows-x64-setup.exe)
- Un zip empaquetado de la integracion de Home Assistant en [`release_assets/pcpowerfree-home-assistant-integration.zip`](../release_assets/pcpowerfree-home-assistant-integration.zip)
- Un bundle experimental del agente Linux publicado como asset de release en GitHub: `pcpowerfree-linux-agent.tar.gz`
- Ejecutables sueltos de Windows:
  - [`windows_agent/dist/PCPowerAgent.exe`](../windows_agent/dist/PCPowerAgent.exe)
  - [`windows_agent/dist/PCPowerTray.exe`](../windows_agent/dist/PCPowerTray.exe)
  - [`windows_agent/dist/PCPowerSetup.exe`](../windows_agent/dist/PCPowerSetup.exe)

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
- Alexa es opcional y funciona a traves de Home Assistant

## Instalacion en Windows

Ruta recomendada:

1. Ejecuta [`windows_agent/dist/pcpowerfree-windows-x64-setup.exe`](../windows_agent/dist/pcpowerfree-windows-x64-setup.exe)
2. Completa la instalacion
3. Revisa la configuracion detectada
4. Deja activadas estas opciones:
   - `Crear regla de firewall`
   - `Instalar al arranque`
5. Pulsa `Instalar`
6. Comprueba que la app de bandeja queda activada al inicio
7. Usa el icono de bandeja para ignorar temporal o permanentemente las ordenes de Home Assistant cuando te convenga
8. Deja el codigo de vinculacion visible o copiado porque Home Assistant te lo pedira a continuacion
9. Vincula el dispositivo en Home Assistant dentro de los 10 minutos siguientes, o genera un codigo nuevo mas tarde desde el configurador de Windows

El configurador detecta automaticamente:

- Nombre del equipo
- Adaptador de red activo
- IP actual
- MAC principal
- Broadcast de Wake-on-LAN
- Subred de descubrimiento

La interfaz del configurador soporta `espanol` e `ingles`.
Tambien incluye una opcion para `Buscar actualizaciones` en GitHub.
La app de bandeja tambien comprueba actualizaciones automaticamente tras iniciar Windows y puede abrir la pagina de la ultima release.

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
sudo /opt/pc-power-free/.venv/bin/python -m pip install --upgrade pip ifaddr zeroconf
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
curl http://127.0.0.1:58477/v1/discovery
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
4. Anade `PC Power Free`

### HACS

El repositorio esta preparado para HACS con [`hacs.json`](../hacs.json).

1. En HACS, abre `Custom repositories`
2. Anade la URL de este repositorio
3. Tipo: `Integration`
4. Instala `PC Power Free`
5. Reinicia Home Assistant
6. Activa las betas o prereleases para este repositorio si quieres recibir avisos de actualizacion de la rama prerelease actual

Si la tarjeta de la integracion sigue mostrando el icono generico, lo normal es que tu Home Assistant sea anterior a `2026.3`, que es la primera version con soporte para assets `brand/` incluidos dentro de una custom integration.

Para el listado `default` de HACS, la publicacion ya esta en marcha:

1. Ya existe una prerelease en GitHub, y el repositorio ya esta preparado para `v0.2.0-beta.5`
2. La PR de envio ya esta abierta en `hacs/default#7156`
3. Lo unico pendiente ahi es la revision y el merge por parte del equipo de HACS

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
2. `PC Power Free`
3. `Configurar por IP manualmente`
4. Introduce la IP actual del host y el puerto del agente
5. Introduce el codigo de vinculacion

Si el codigo caduca:

- en Windows, abre el configurador y genera uno nuevo
- en Linux, vuelve a ejecutar `linux_agent/setup_cli.py`

## Alexa

La ruta prevista es `Alexa + Home Assistant`.
Todavia no esta validada de extremo a extremo en una instalacion real, asi que ahora mismo debe considerarse `experimental`.

La opcion local mas simple es `emulated_hue`.

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
.\\windows_agent\\build-exe.ps1 -Clean
```

### Instalador de Windows

```powershell
.\\windows_agent\\build-installer.ps1
```

### Assets de release

```powershell
.\\build-release-assets.ps1
```

## Seguridad

- No expongas el puerto `58477` a Internet
- Limita el acceso a la IP de Home Assistant o, como minimo, a tu LAN
- Usa VPN si necesitas acceso remoto
- El codigo de vinculacion es temporal

## Estado de publicacion

Estado actual para el repositorio `default` de HACS:

- PR de envio ya abierta: `hacs/default#7156`
- ultima prerelease ya publicada: `v0.2.0-beta.4`
- siguiente prerelease prevista: `v0.2.0-beta.5`
- pendiente de revision por los maintainers de HACS

Pendiente antes de considerarlo realmente final:

- prueba real con Alexa via `emulated_hue`
- paquete DSM y modelo de privilegios
