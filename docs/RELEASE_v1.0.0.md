> Historical record / Registro de esta publicación. For installation use [English](../README.md) or [Español](README.es.md).

# WakeLink v1.0.0

[English](#english) | [Español](#español)

## English

First stable WakeLink release: local Home Assistant power control for Windows x64, Ubuntu 24.04 Desktop and Synology DSM 7.2. Alexa is optional through external Matterbridge and `matterbridge-hass`; Home Assistant and the bridge must stay running on another device when the controlled machine is off.

### Downloads

Open **Assets**, not **Source code**, and choose your system:

| System | File | Guide |
| --- | --- | --- |
| Windows x64 | `WakeLink-Windows-x64-Setup.exe` | [Windows](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/GETTING_STARTED.en.md) |
| Ubuntu Desktop | `WakeLink-Ubuntu-1.0.0.deb` | [Ubuntu](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/INSTALL_UBUNTU.en.md) |
| DSM | `pcpowerfree-dsm-noarch-1.0.0-0001.spk` | [DSM](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/INSTALL_DSM.en.md) |
| Home Assistant | HACS, or `WakeLink-Home-Assistant.zip` for manual installation | [Start here](https://github.com/slx612/WOL-Home-Assistant-And-Alexa#start-here) |

The second Windows filename is an identical compatibility copy for old updaters. The Linux `.tar.gz` is server source, not the desktop installer. `SHA256SUMS.txt` verifies file bytes, not publisher identity.

### Updating from a beta

**Install over the existing app. Do not uninstall, delete the Home Assistant device or pair again.** Update WakeLink in HACS and restart Home Assistant. DSM `1.0.0-0001` is newer than `0.2.0-0024`; compare the complete version.

- Windows: check from the app/tray, download the installer, then close the dashboard. The installer now checks for an open dashboard **before** stopping the agent or replacing files, and offers Retry/Cancel. Versions shown by the window, tray and agent now agree. Stable installations no longer offer future betas.
- Ubuntu: checks on opening, or **Check for updates > Install update**. Installation requires confirmation and native authorization; the verified official `.deb` is installed through APT. No silent installs, closed-window polling or APT repository.
- DSM: add the package source once and use Package Center's normal update wizard. The static catalog points to GitHub assets; it does not relay control requests. See the DSM guide for the source address and initial limited power permission.

### Validation and limits

Local Python suite: **177 tests, OK, two POSIX-only skips on Windows**; five native Ubuntu package/lifecycle checks, DSM desktop JavaScript and inspection of the compiled files passed. Native beta.13-to-1.0 upgrades on both disposable VMs preserved configuration, token, TLS certificate/key and guard state byte-for-byte; DSM's existing limited power grant survived. The original credentials still authenticated and uptime returned. Ubuntu's clean native package install and service activation passed; the VM's original identity was restored and checked afterwards, separately from the upgrade test.

The user confirmed Alexa discovery, shutdown and wake on a real Echo, and previously confirmed Windows/DSM control. These are user-reported hardware tests, not certification of every model. No new power orders were sent during this release pass.

Full graphical Ubuntu administrator approval and DSM unsigned-package update dialogs are not independently validated end-to-end. An Ubuntu permission prompt was observed and its timeout recovered without resetting pairing. The complete v1 Windows installer wizard has not been run on the user's working PC; its preflight was exercised with a real Windows process. Other OS/DSM/Echo models, physical NAS wake and DSM downgrade remain unvalidated. These limits are not changed by the stable label.

Windows SmartScreen can still warn because the installer is unsigned. The missing HACS store icon remains a known upstream display issue. Wake-on-LAN depends on firmware, Ethernet/network settings and hardware support; it cannot start a stopped VM through its hypervisor. Use a trusted LAN; never expose the agent to the Internet. Synology High Availability clusters are unsupported.

## Español

Primera versión estable de WakeLink: control local desde Home Assistant para Windows x64, Ubuntu 24.04 Desktop y Synology DSM 7.2. Alexa es opcional mediante Matterbridge y `matterbridge-hass` externos; Home Assistant y el puente deben seguir encendidos en otro equipo cuando apagues el dispositivo controlado.

### Descargas

Abre **Assets**, no **Source code**, y elige tu sistema:

| Sistema | Archivo | Guía |
| --- | --- | --- |
| Windows x64 | `WakeLink-Windows-x64-Setup.exe` | [Windows](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/GETTING_STARTED.es.md) |
| Ubuntu Desktop | `WakeLink-Ubuntu-1.0.0.deb` | [Ubuntu](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/INSTALL_UBUNTU.es.md) |
| DSM | `pcpowerfree-dsm-noarch-1.0.0-0001.spk` | [DSM](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/INSTALL_DSM.es.md) |
| Home Assistant | HACS o `WakeLink-Home-Assistant.zip` para instalar manualmente | [Empieza aquí](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/README.es.md) |

El segundo nombre Windows es una copia idéntica para actualizadores antiguos. El `.tar.gz` Linux es código de servidor, no el instalador gráfico. `SHA256SUMS.txt` verifica los archivos, no identifica al autor.

### Actualizar desde una beta

**Instala encima. No desinstales, no borres el dispositivo de Home Assistant ni vuelvas a vincular.** Actualiza WakeLink en HACS y reinicia Home Assistant. DSM `1.0.0-0001` supera `0.2.0-0024`: cuenta la versión completa.

- Windows: busca desde la app/bandeja, descarga el instalador y cierra el panel. El instalador comprueba que el panel está cerrado **antes** de detener el agente o sustituir archivos, con Reintentar/Cancelar. Ventana, bandeja y agente muestran la misma versión. Una estable ya no ofrece betas futuras.
- Ubuntu: busca al abrir o con **Buscar actualizaciones > Instalar actualización**. Pide confirmación y autorización nativa; instala el `.deb` oficial verificado mediante APT. No instala en silencio, no consulta con la ventana cerrada ni crea un repositorio APT.
- DSM: añade la fuente una vez y usa el asistente normal del Centro de paquetes. El catálogo estático enlaza instaladores GitHub, no retransmite órdenes. La guía DSM explica la dirección y el permiso inicial limitado.

### Pruebas y límites

Pruebas Python locales: **177, OK, dos exclusivas POSIX omitidas en Windows**; pasaron cinco comprobaciones nativas de paquetes/ciclo de vida en Ubuntu, el escritorio DSM JavaScript y la inspección de los archivos compilados. Actualizar ambas VMs de beta.13 a 1.0 conservó exactamente configuración, token, certificado/clave y protección; DSM mantuvo su permiso limitado. Las credenciales anteriores siguieron autenticando y se obtuvo el tiempo encendido. También pasó instalar el paquete Ubuntu limpio y activar el servicio; después se restauró y comprobó la identidad original de la VM, por separado de la prueba de actualización.

El usuario confirmó descubrimiento, apagado y encendido Alexa con un Echo real, y antes confirmó controles Windows/DSM. Son pruebas de hardware comunicadas por el usuario, no certificación de todos los modelos. No se enviaron nuevas órdenes de energía durante esta revisión.

Los diálogos completos de aprobación Ubuntu y actualización DSM sin firma no están validados de principio a fin de forma independiente. Se observó el permiso Ubuntu y su expiración se recuperó sin restablecer la vinculación. No se ejecutó el asistente completo del instalador Windows v1 en el PC de trabajo; su comprobación previa se probó con un proceso Windows real. Otros sistemas/modelos DSM/Echo, encendido de NAS físico y regreso a versiones DSM anteriores no están validados. La etiqueta estable no cambia esos límites.

SmartScreen puede seguir avisando porque Windows no tiene firma digital. El icono de tienda HACS ausente sigue siendo un fallo visual externo conocido. Wake-on-LAN depende del firmware, Ethernet/red y hardware; no arranca VMs detenidas mediante el hipervisor. Usa una red de confianza, nunca publiques el agente en Internet. No se admiten clústeres Synology High Availability.
