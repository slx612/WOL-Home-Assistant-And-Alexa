> Historical record / Registro de esta publicación. For installation use [English](../README.md) or [Español](README.es.md).

# WakeLink v0.2.0-beta.13

[English](#english) | [Español](#español)

## English

### Choose your download

Open **Assets** below this release and download only your system's installer:

| System | File | Instructions |
| --- | --- | --- |
| Windows x64 | `WakeLink-Windows-x64-Setup.exe` | [Windows](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/GETTING_STARTED.en.md) |
| Ubuntu 24.04 Desktop | `WakeLink-Ubuntu-0.2.0-beta.13.deb` | [Ubuntu](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/INSTALL_UBUNTU.en.md) |
| Synology DSM 7 | `pcpowerfree-dsm-noarch-0.2.0-0024.spk` | [DSM](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/INSTALL_DSM.en.md) |
| Home Assistant | HACS, or `WakeLink-Home-Assistant.zip` for manual installs | [Start here](https://github.com/slx612/WOL-Home-Assistant-And-Alexa#start-here) |

The identical Windows legacy filename is included for existing updaters. The Linux `.tar.gz` is source for manual/server use, not the desktop installer. Do not choose GitHub's **Source code** files for a normal installation.

### Changes

- Ubuntu's graphical app checks for updates on opening and through **Check for updates**. **Install update** requires confirmation and Ubuntu administrator authorization. The installer verifies GitHub's SHA-256, size and package identity before APT installs it. No background checking while the window is closed, silent installation or APT repository.
- DSM has an integrated desktop window, guided one-time limited power authorization, boot/uptime reporting and a native Package Center catalog. Package revision **0024** is deliberately higher than the earlier local tests (0021-0023).
- English and Spanish installation/update guides now identify the correct files and the single path for each system. Alexa still uses external Matterbridge and `matterbridge-hass`.
- Updates retain configuration, token, certificate/key and Home Assistant pairing. Install over the existing app; **do not uninstall, delete the HA device or pair again**.

### DSM updates: add this source once

Open **Package Center > Settings > Package Sources > Add**. Name it **WakeLink** and paste:

```text
https://raw.githubusercontent.com/slx612/WOL-Home-Assistant-And-Alexa/main/dsm_package/repository.json
```

Package Center checks its catalog; select **Update** when offered and follow DSM's normal third-party-package wizard. The package is unsigned: do not disable protections or assume unattended installation. This static catalog only links downloads; it does not relay control commands or require paid hosting.

### Validation and limits

Source tests and local VM upgrades passed before release. Ubuntu's native update installer and DSM catalog/download/native installation were tested with identity preservation; existing tokens and certificates still authenticated. English/Spanish Ubuntu windows were checked at 1024x768. The full graphical Ubuntu administrator dialog and DSM unsigned update wizard remain separate user-interface checks, not implied by the API/installer tests. A fresh Ubuntu desktop installation, other DSM models/versions, physical NAS Wake-on-LAN and downgrade remain unvalidated.

This is a **beta, not v1.0**. Windows SmartScreen may still warn about the unsigned installer. The missing HACS store icon is an upstream display issue. Alexa discovery has been reported working; full real-Echo shutdown/wake validation is still pending. `SHA256SUMS.txt` verifies bytes, not publisher identity or an independent security audit.

## Español

### Qué descargar

Abre **Assets** debajo de esta publicación y descarga solo el instalador de tu sistema:

| Sistema | Archivo | Guía |
| --- | --- | --- |
| Windows x64 | `WakeLink-Windows-x64-Setup.exe` | [Windows](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/GETTING_STARTED.es.md) |
| Ubuntu 24.04 Desktop | `WakeLink-Ubuntu-0.2.0-beta.13.deb` | [Ubuntu](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/INSTALL_UBUNTU.es.md) |
| Synology DSM 7 | `pcpowerfree-dsm-noarch-0.2.0-0024.spk` | [DSM](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/INSTALL_DSM.es.md) |
| Home Assistant | HACS o `WakeLink-Home-Assistant.zip` para instalación manual | [Empieza aquí](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/main/docs/README.es.md) |

El instalador Windows con nombre antiguo es una copia idéntica para actualizadores existentes. El `.tar.gz` Linux es código para instalación manual/servidores, no el instalador gráfico. No elijas los archivos **Source code** para una instalación normal.

### Cambios

- Ubuntu busca al abrir la ventana y mediante **Buscar actualizaciones**. **Instalar actualización** pide confirmación y autorización administradora de Ubuntu. Comprueba SHA-256 de GitHub, tamaño e identidad antes de instalar mediante APT. No busca con la ventana cerrada, no instala en silencio ni configura un repositorio APT.
- DSM incluye ventana integrada, autorización inicial guiada y limitada, sensores de arranque/tiempo encendido y catálogo del Centro de paquetes. La revisión **0024** supera las pruebas locales 0021-0023 para actualizar encima.
- Guías inglesas y españolas actualizadas con el archivo correcto y un recorrido por sistema. Alexa sigue usando Matterbridge y `matterbridge-hass`, externos.
- Actualizar conserva configuración, token, certificado/clave y vinculación Home Assistant. Instala encima: **no desinstales, no borres el dispositivo ni vuelvas a vincularlo**.

### Actualizaciones DSM: añade la fuente una vez

Abre **Centro de paquetes > Configuración > Fuentes del paquete > Agregar**. Nombre **WakeLink** y dirección:

```text
https://raw.githubusercontent.com/slx612/WOL-Home-Assistant-And-Alexa/main/dsm_package/repository.json
```

Cuando se ofrezca, pulsa **Actualizar** y sigue el asistente normal de terceros. El paquete no tiene firma: no desactives protecciones ni des por hecha una instalación desatendida. El catálogo estático solo enlaza descargas; no retransmite órdenes de control ni exige alojamiento de pago.

### Pruebas y límites

Antes de publicar pasaron las pruebas de código y actualizaciones locales en VM. Se comprobaron el instalador de actualización Ubuntu y el catálogo/descarga/instalación nativa DSM, conservando identidad; token y certificados existentes siguieron funcionando. Se revisaron las ventanas Ubuntu en ambos idiomas a 1024x768. El diálogo gráfico administrador Ubuntu y el asistente gráfico DSM sin firma siguen siendo pruebas de interfaz separadas, no demostradas por las API o instaladores. Faltan instalación Ubuntu limpia, otros modelos/versiones DSM, encendido de un NAS físico y regreso a versiones anteriores.

Es una **beta, no v1.0**. Windows puede seguir avisando por el instalador sin firma. El icono ausente en la tienda HACS es un problema visual externo. Se ha comunicado descubrimiento Alexa funcional; falta validar apagado/encendido completos con un Echo real. `SHA256SUMS.txt` verifica los archivos, no la identidad del autor ni una auditoría independiente.
