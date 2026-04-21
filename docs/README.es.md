# PC Power Free

![PC Power Free](../custom_components/pc_power_free/brand/logo.png)

Idioma:

- [English](../README.md)
- [Español](README.es.md)

Solución local y sin suscripción para encender, apagar y reiniciar un PC Windows desde Home Assistant y Alexa.

Estado actual: `0.2.0-beta.4 prerelease, ruta Home Assistant validada en instalación real, ruta Alexa aún pendiente de validación real`.

Estado de publicación:

- El código del repositorio apunta ahora a `v0.2.0-beta.4`
- La última prerelease publicada en GitHub es `v0.2.0-beta.4`, del 21 de abril de 2026
- La solicitud para el repositorio `default` de HACS ya está abierta en `hacs/default#7156`
- Las rutas previstas de distribución son: instalación manual, custom repository de HACS, descargas prerelease de GitHub e instalador de Windows
- La única validación real que sigue pendiente es la ruta `Alexa + Home Assistant`

Novedades recientes:

- Icono de bandeja en Windows para bloquear temporal o permanentemente las órdenes de Home Assistant
- Sensores de diagnóstico en Home Assistant para `Uptime` y `Boot time`
- Comprobación de actualizaciones desde GitHub en el configurador de escritorio

## Qué es

Este proyecto cubre el flujo local completo:

- Instalar un programa normal en Windows
- Detectar automáticamente ese PC en Home Assistant
- Vincularlo con un código temporal
- Encenderlo por Wake-on-LAN
- Apagarlo o reiniciarlo por red local
- Exponerlo a Alexa a través de Home Assistant sin pagar una suscripción de terceros

No depende de la nube. No requiere abrir puertos a Internet.

## Incluye

- Una integración personalizada para Home Assistant en [`custom_components/pc_power_free`](../custom_components/pc_power_free)
- Un agente para Windows en [`windows_agent`](../windows_agent)
- Un instalador completo para Windows en [`windows_agent/dist/pcpowerfree-windows-x64-setup.exe`](../windows_agent/dist/pcpowerfree-windows-x64-setup.exe)
- Un zip empaquetado de la integración de Home Assistant en [`release_assets/pcpowerfree-home-assistant-integration.zip`](../release_assets/pcpowerfree-home-assistant-integration.zip)
- Ejecutables sueltos:
  - [`windows_agent/dist/PCPowerAgent.exe`](../windows_agent/dist/PCPowerAgent.exe)
  - [`windows_agent/dist/PCPowerTray.exe`](../windows_agent/dist/PCPowerTray.exe)
  - [`windows_agent/dist/PCPowerSetup.exe`](../windows_agent/dist/PCPowerSetup.exe)

## Cómo funciona

### Encendido

1. Home Assistant envía un paquete Wake-on-LAN.
2. El PC arranca si BIOS/UEFI y Windows están bien configurados.

### Apagado y reinicio

1. Home Assistant llama al agente local de Windows.
2. El agente valida la red de origen y el token interno.
3. Ejecuta `shutdown` o `restart`.

### Descubrimiento y vinculación

1. El agente de Windows anuncia el PC por `zeroconf` en la red local.
2. Home Assistant lo detecta automáticamente.
3. El usuario introduce un código temporal de 6 dígitos generado por el instalador de Windows.
4. Home Assistant intercambia ese código por el token interno y guarda la configuración.

## Requisitos

- Home Assistant en la misma red local
- Un PC Windows con soporte Wake-on-LAN
- BIOS/UEFI con Wake-on-LAN disponible
- Home Assistant `2026.3` o superior si quieres que se vea el logo incluido en `custom_components/.../brand/`
- Alexa es opcional y funciona a través de Home Assistant

## Instalación en Windows

Ruta recomendada:

1. Ejecuta [`windows_agent/dist/pcpowerfree-windows-x64-setup.exe`](../windows_agent/dist/pcpowerfree-windows-x64-setup.exe)
2. Completa la instalación
3. Revisa la configuración detectada
4. Deja activadas estas opciones:
   - `Crear regla de firewall`
   - `Instalar al arranque`
5. Pulsa `Instalar`
6. Comprueba que la app de bandeja queda activada al inicio
7. Usa el icono de bandeja para ignorar temporal o permanentemente las órdenes de Home Assistant cuando te convenga
8. Guarda el código de vinculación

El configurador detecta automáticamente:

- Nombre del equipo
- Adaptador de red activo
- IP actual
- MAC principal
- Broadcast de Wake-on-LAN
- Subred de descubrimiento

La interfaz del configurador ya soporta `español` e `inglés`.
También incluye una opción para `Buscar actualizaciones` en GitHub.

## Instalación en Home Assistant

### Manual

1. Copia `custom_components/pc_power_free` dentro de `/config/custom_components/`
2. Reinicia Home Assistant
3. Ve a `Ajustes > Dispositivos y servicios`
4. Añade `PC Power Free`

### HACS

El repositorio está preparado para HACS con [`hacs.json`](../hacs.json).

1. En HACS, abre `Custom repositories`
2. Añade la URL de este repositorio
3. Tipo: `Integration`
4. Instala `PC Power Free`
5. Reinicia Home Assistant
6. Activa las betas o prereleases para este repositorio si quieres recibir avisos de actualización de la rama prerelease actual

Si la tarjeta de la integración sigue mostrando el icono genérico, lo normal es que tu Home Assistant sea anterior a `2026.3`, que es la primera versión con soporte para assets `brand/` incluidos dentro de una custom integration.

Para el listado `default` de HACS, la publicación ya está en marcha:

1. La prerelease de GitHub ya está publicada
2. La PR de envío ya está abierta en `hacs/default#7156`
3. Lo único pendiente ahí es la revisión y el merge por parte del equipo de HACS

## Vinculación con Home Assistant

### Flujo recomendado

1. Instala el programa en Windows
2. Instala la integración en Home Assistant
3. Espera a que el PC aparezca automáticamente
4. Selecciona el PC detectado
5. Introduce el código temporal mostrado por el configurador
6. Confirma el nombre del dispositivo

### Si falla el descubrimiento automático

También hay un flujo manual por IP:

1. `Añadir integración`
2. `PC Power Free`
3. `Configurar por IP manualmente`
4. Introduce la IP del PC y el puerto del agente
5. Introduce el código de vinculación

## Alexa

La ruta prevista es `Alexa + Home Assistant`.
Todavía no está validada de extremo a extremo en una instalación real, así que ahora mismo debe considerarse `experimental`.

La opción local más simple es `emulated_hue`.

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
custom_components/pc_power_free/
windows_agent/
hacs.json
README.md
docs/README.es.md
LICENSE
```

## Archivos principales

- [`custom_components/pc_power_free/config_flow.py`](../custom_components/pc_power_free/config_flow.py)
- [`custom_components/pc_power_free/api.py`](../custom_components/pc_power_free/api.py)
- [`windows_agent/pc_power_agent.py`](../windows_agent/pc_power_agent.py)
- [`windows_agent/setup_wizard_gui.py`](../windows_agent/setup_wizard_gui.py)
- [`windows_agent/build-exe.ps1`](../windows_agent/build-exe.ps1)
- [`windows_agent/build-installer.ps1`](../windows_agent/build-installer.ps1)

## Compilar de nuevo

### Ejecutables

```powershell
.\windows_agent\build-exe.ps1 -Clean
```

### Instalador final

```powershell
.\windows_agent\build-installer.ps1
```

## Seguridad

- No expongas el puerto `8777` a Internet
- Limita el acceso a la IP de Home Assistant o, como mínimo, a tu LAN
- Usa VPN si necesitas acceso remoto
- El código de vinculación es temporal

## Estado de publicación

El repositorio queda preparado para:

- instalación manual
- instalación como custom repository de HACS
- distribución de prereleases en GitHub
- distribución del instalador de Windows

Estado actual para el repositorio `default` de HACS:

- PR de envío ya abierta: `hacs/default#7156`
- última prerelease ya publicada: `v0.2.0-beta.4`
- pendiente de revisión por los maintainers de HACS

Pendiente antes de considerarlo realmente final:

- prueba real con Alexa via `emulated_hue`
