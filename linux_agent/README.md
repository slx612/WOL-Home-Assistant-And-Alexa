# WakeLink Linux: advanced installation / Instalación avanzada

For a desktop, use the complete [English](../docs/INSTALL_UBUNTU.en.md) or [Spanish](../docs/INSTALL_UBUNTU.es.md) guide. Do not combine its `.deb` route with the manual route below.

Para un escritorio, sigue la guía completa [inglesa](../docs/INSTALL_UBUNTU.en.md) o [española](../docs/INSTALL_UBUNTU.es.md). No mezcles el `.deb` con la instalación manual siguiente.

## Manual installation for servers

**Advanced, headless Ubuntu/Debian route.** No window is installed. You need administrator access, Python 3.10+, systemd and network access to install dependencies. Home Assistant must run elsewhere. The agent service below runs as **root** to perform system power actions; this is different from DSM's limited package-user grant.

Use the source archive `pcpowerfree-linux-agent.tar.gz` supplied for your version. Start in the directory containing it. **These commands are for a fresh installation only.** Back up existing state before an upgrade; do not rerun first-time setup to repair a working pairing.

## Servidor sin escritorio

**Ruta avanzada para Ubuntu/Debian sin interfaz gráfica.** No instala una ventana. Necesitas administrador, Python 3.10+, systemd y acceso a la red para dependencias. Home Assistant debe funcionar en otro equipo. Este servicio se ejecuta como **root** para gestionar la energía; no es el permiso limitado del paquete DSM.

Usa `pcpowerfree-linux-agent.tar.gz` de tu versión. Empieza en la carpeta que contiene el archivo. **Los comandos siguientes son solo para una instalación nueva.** Antes de actualizar conserva los datos; no repitas la configuración inicial para reparar una vinculación funcional.

## Fresh-install commands / Comandos de instalación nueva

```sh
sudo apt install python3 python3-venv
sudo mkdir -p /opt/pc-power-free /etc/pc-power-free
sudo chmod 700 /etc/pc-power-free
sudo tar -xzf pcpowerfree-linux-agent.tar.gz -C /opt/pc-power-free
sudo python3 -m venv /opt/pc-power-free/.venv
sudo /opt/pc-power-free/.venv/bin/python -m pip install ifaddr zeroconf cryptography
sudo /opt/pc-power-free/.venv/bin/python /opt/pc-power-free/linux_agent/setup_cli.py --config /etc/pc-power-free/config.json
sudo cp /opt/pc-power-free/linux_agent/pcpowerfree-agent.service /etc/systemd/system/pcpowerfree-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now pcpowerfree-agent.service
```

**English:** setup prints a six-digit code and TLS SHA-256 fingerprint. Install WakeLink in HACS, restart Home Assistant, then **Settings > Devices & services > Add integration > WakeLink**. Select the discovered server (or enter its IP and port `58477`), compare the fingerprint and enter the code within ten minutes. If it expired, use the command below. Allow agent traffic only from the trusted LAN; never expose the port to the internet. A firewall may require an explicit rule for that LAN.

**Español:** la configuración muestra un código de seis cifras y la huella TLS SHA-256. Instala WakeLink en HACS, reinicia Home Assistant y abre **Configuración > Dispositivos y servicios > Añadir integración > WakeLink**. Selecciona el servidor descubierto (o su IP y puerto `58477`), compara la huella e introduce el código antes de diez minutos. Si caducó, usa el comando siguiente. Permite el acceso al agente solo desde la red de confianza, nunca Internet. Tu cortafuegos puede necesitar una regla específica para esa red.

Generate a code without changing existing identity/settings / Generar un código sin cambiar identidad ni ajustes existentes:

```sh
sudo /opt/pc-power-free/.venv/bin/python /opt/pc-power-free/linux_agent/setup_cli.py --config /etc/pc-power-free/config.json --pairing-only
```

## Updates and diagnosis / Actualización y diagnóstico

**English:** preserve all of `/etc/pc-power-free/` (config, TLS identity and guard state). Replace source files for your new version without deleting state; restart `pcpowerfree-agent.service` and check its status. Never publish config or private keys. See [Help](../docs/HELP.en.md) for power, networking and rollback. WakeLink does not configure every adapter's persistent Wake-on-LAN settings or start a stopped VM.

**Español:** conserva todo `/etc/pc-power-free/` (configuración, identidad TLS y protección). Sustituye las fuentes de la nueva versión sin borrar datos; reinicia `pcpowerfree-agent.service` y comprueba su estado. No publiques configuración ni claves privadas. Consulta [Ayuda](../docs/HELP.es.md) para energía, red y regreso. WakeLink no configura el encendido persistente de todas las tarjetas ni arranca una VM detenida.

Read-only service checks / Comprobaciones de solo lectura:

```sh
sudo systemctl status pcpowerfree-agent.service --no-pager
sudo journalctl -u pcpowerfree-agent.service -n 50 --no-pager
```

## Build the desktop package / Compilar el paquete gráfico

Maintainers only: on a Linux build machine with `dpkg-deb`, run `sh linux_package/build-deb.sh` from the repository root. The file appears in `release_assets/`; building does not install it. Keep the local preview distinct from published Releases.

Solo mantenimiento: en Linux con `dpkg-deb`, ejecuta `sh linux_package/build-deb.sh` desde la raíz del repositorio. El archivo aparece en `release_assets/`; compilar no lo instala. No presentes una prueba local como descarga publicada.
