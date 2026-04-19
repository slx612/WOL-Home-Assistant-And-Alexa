# PC Power Free

Solucion local y sin suscripcion para encender, apagar y reiniciar un PC Windows desde Home Assistant y Alexa.

Estado actual: `terminado a falta de probar en una instalacion real`.

## Que es

Este proyecto resuelve el caso de uso de:

- Instalar un programa normal en Windows
- Detectar automaticamente ese PC en Home Assistant
- Vincularlo con un codigo temporal
- Encenderlo por Wake-on-LAN
- Apagarlo o reiniciarlo por red local
- Usarlo con Alexa a traves de Home Assistant, sin suscripcion adicional

No depende de nube ni de puertos abiertos a Internet.

## Incluye

- Integracion personalizada para Home Assistant en [`custom_components/pc_power_free`](custom_components/pc_power_free)
- Agente para Windows en [`windows_agent`](windows_agent)
- Instalador final para Windows en [`windows_agent/dist/pcpowerfree-windows-x64-setup.exe`](windows_agent/dist/pcpowerfree-windows-x64-setup.exe)
- Ejecutables sueltos:
  - [`windows_agent/dist/PCPowerAgent.exe`](windows_agent/dist/PCPowerAgent.exe)
  - [`windows_agent/dist/PCPowerSetup.exe`](windows_agent/dist/PCPowerSetup.exe)

## Como funciona

### Encendido

1. Home Assistant envia un paquete Wake-on-LAN.
2. El PC arranca si BIOS/UEFI y Windows lo permiten.

### Apagado y reinicio

1. Home Assistant llama al agente local del PC.
2. El agente valida la red de origen y el token interno.
3. Ejecuta `shutdown` o `restart`.

### Descubrimiento y vinculacion

1. El agente de Windows anuncia el PC por `zeroconf` en la red local.
2. Home Assistant lo detecta automaticamente.
3. El usuario introduce un codigo temporal de 6 digitos generado por el instalador.
4. Home Assistant intercambia ese codigo por el token interno y guarda la configuracion.

## Requisitos

- Home Assistant en la misma red local
- Un PC Windows con Wake-on-LAN disponible
- BIOS/UEFI con Wake-on-LAN activable
- Alexa opcional, usando Home Assistant como intermediario

## Instalacion en Windows

Ruta recomendada:

1. Ejecutar [`windows_agent/dist/pcpowerfree-windows-x64-setup.exe`](windows_agent/dist/pcpowerfree-windows-x64-setup.exe)
2. Completar la instalacion
3. Revisar los datos detectados
4. Dejar activadas:
   - `Crear regla de firewall`
   - `Instalar al arranque`
5. Pulsar `Instalar`
6. Apuntar el codigo de vinculacion

El configurador detecta automaticamente:

- Nombre del equipo
- Adaptador de red activo
- IP actual
- MAC principal
- Broadcast de Wake-on-LAN
- Subred de descubrimiento

## Instalacion en Home Assistant

### Manual

1. Copia `custom_components/pc_power_free` dentro de `/config/custom_components/`
2. Reinicia Home Assistant
3. Ve a `Ajustes > Dispositivos y servicios`
4. Anade `PC Power Free`

### HACS

El repo esta preparado para HACS con [`hacs.json`](hacs.json).

1. En HACS, abre `Custom repositories`
2. Anade la URL de este repo
3. Tipo: `Integration`
4. Instala `PC Power Free`
5. Reinicia Home Assistant

## Vinculacion con Home Assistant

### Flujo recomendado

1. Instala el programa en Windows
2. Instala la integracion en Home Assistant
3. Espera a que el PC aparezca automaticamente
4. Selecciona el PC detectado
5. Introduce el codigo temporal mostrado por el instalador
6. Confirma el nombre

### Si el descubrimiento automatico falla

Tambien hay ruta manual por IP:

1. `Anadir integracion`
2. `PC Power Free`
3. `Configurar por IP manualmente`
4. Introducir IP del PC y puerto del agente
5. Introducir codigo de vinculacion

## Alexa

La ruta soportada es `Alexa + Home Assistant`.

Se recomienda exponer la entidad mediante `emulated_hue`.

Ejemplo:

```yaml
emulated_hue:
  listen_port: 80
  entities:
    switch.pc_despacho_power:
      name: "PC Despacho"
      hidden: false
```

## Estructura del repo

```text
custom_components/pc_power_free/
windows_agent/
hacs.json
README.md
LICENSE
```

## Archivos principales

- [`custom_components/pc_power_free/config_flow.py`](custom_components/pc_power_free/config_flow.py)
- [`custom_components/pc_power_free/api.py`](custom_components/pc_power_free/api.py)
- [`windows_agent/pc_power_agent.py`](windows_agent/pc_power_agent.py)
- [`windows_agent/setup_wizard_gui.py`](windows_agent/setup_wizard_gui.py)
- [`windows_agent/build-exe.ps1`](windows_agent/build-exe.ps1)
- [`windows_agent/build-installer.ps1`](windows_agent/build-installer.ps1)

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
- Limita el acceso a la IP de Home Assistant o a tu LAN
- Usa VPN si necesitas acceso remoto
- El codigo de vinculacion es temporal

## Publicacion

El repo queda preparado para:

- instalacion manual
- instalacion por HACS
- distribucion del instalador de Windows

Pendiente antes de considerarlo realmente final:

- prueba real en una instancia Home Assistant
- prueba real de descubrimiento `zeroconf`
- prueba real de vinculado por codigo
- prueba real con Alexa via `emulated_hue`
