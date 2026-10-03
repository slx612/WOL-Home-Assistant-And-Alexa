# Ayuda y actualizaciones de WakeLink

[English](HELP.en.md) | [Español](HELP.es.md) | [Elegir guía de instalación](README.es.md#empieza-aquí)

Busca tu problema abajo. **No desinstales, no borres el dispositivo de Home Assistant ni restablezcas las credenciales como primera solución.**

## Qué archivo descargo

Abre [Publicaciones](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases), elige una con instalador para tu sistema y despliega **Assets**. No todas incluyen todos los sistemas. Una etiqueta o un archivo de código fuente no es un instalador.

| Sistema | Archivo para una instalación normal |
| --- | --- |
| Windows x64 | `WakeLink-Windows-x64-Setup.exe` |
| Ubuntu Desktop | `WakeLink-Ubuntu-<version>.deb` (disponible desde beta.13) |
| DSM | `pcpowerfree-dsm-noarch-<version>.spk` (beta.13 usa revisión 0024) |
| Home Assistant | HACS: busca **WakeLink**; `WakeLink-Home-Assistant.zip` solo es para instalación manual |

Las rutas `PC Power Free` y los identificadores `pc_power_free` / `pcpowerfree` conservan la compatibilidad: no los renombres. El instalador Windows con nombre antiguo es una copia idéntica compatible con el actualizador, no otra app.

## Home Assistant no encuentra el equipo

1. Mantén el equipo encendido. Abre WakeLink y comprueba que el agente funciona. En DSM comprueba también el Centro de paquetes; en Ubuntu completa **Activar WakeLink**.
2. Comprueba que Home Assistant y el equipo pueden comunicarse en una red local de confianza. Una red de invitados, VPN, VLAN o cortafuegos puede bloquear la detección.
3. Genera un código nuevo de seis cifras en WakeLink. Abre **Configuración > Dispositivos y servicios > Añadir integración > WakeLink** en Home Assistant; algunas versiones llaman **Ajustes** a **Configuración**. Si aparece el formulario manual, usa la IP actual del equipo y el puerto `58477`, no el puerto del escritorio DSM.
4. Introduce el código antes de diez minutos. Es temporal y de un solo uso; no pongas la contraseña del sistema ni el QR Matter. Comprueba el nombre/IP. En Windows, compara la huella del certificado de ambas pantallas antes de confirmar.

WakeLink normalmente redescubre los cambios de dirección, sin IP fija. Si la detección no funciona en tu red, una reserva DHCP del router es una alternativa práctica. Si restringes el agente a una sola IP de Home Assistant, esa IP debe mantenerse o debes actualizar la restricción. Una MAC identifica una tarjeta de red, no un administrador de confianza.

## Está encendido, pero aparece Apagado o No disponible

Comprueba primero el agente. El interruptor refleja si se puede contactar con él, no mide directamente la corriente eléctrica. Un agente bloqueado o desconectado puede hacer que un equipo encendido parezca apagado. **No pulses Apagar para refrescar:** envía una orden real de apagado.

El intervalo de consulta predeterminado es de 30 segundos, ajustable en las opciones de WakeLink en Home Assistant. Espera a que termine el arranque y se inicie el agente, y después a la siguiente consulta. **Boot time** es la fecha/hora del último arranque; **Uptime** es el tiempo desde ese arranque, no desde que abriste la app. No están disponibles mientras no se pueda contactar con el equipo/agente.

## Falla el apagado o reinicio

| Mensaje o síntoma | Primera comprobación |
| --- | --- |
| DSM power permission is not enabled | En el escritorio HTTPS de DSM, abre WakeLink y completa [el permiso inicial](INSTALL_DSM.es.md#3-permitir-apagado-y-reinicio-una-sola-vez). |
| Linux power command failed | Revisa el paquete instalado y los permisos del servicio. DSM necesita el paquete DSM actual, no instrucciones Linux genéricas. No concedas acceso root arbitrario. |
| Windows rechaza la orden | Comprueba la protección de WakeLink. Pulsa **Permitir órdenes** solo cuando quieras aceptar órdenes remotas de energía. |
| Error de certificado o autenticación | Comprueba que sea el equipo correcto y conserva los datos existentes. No desactives TLS ni borres certificados para ocultar el error. |
| Aplicaciones que impiden apagar | Guarda/cierra las aplicaciones y repite cuando estés preparado. Forzar puede perder trabajo; DSM no admite apagado forzado/retrasado. |

## Apaga, pero no enciende

Wake-on-LAN es independiente del agente. En un ordenador físico, revisa la opción Wake-on-LAN de BIOS/UEFI y la compatibilidad de su tarjeta de red. Ethernet es el punto de partida más sencillo. Que cambie el interruptor no demuestra que el hardware haya arrancado. Inicio rápido Windows y los estados de suspensión/apagado admitidos por el firmware pueden influir; cambiar una opción no garantiza compatibilidad. Consulta [la explicación Microsoft](https://learn.microsoft.com/en-us/troubleshoot/windows-client/setup-upgrade-and-drivers/wake-on-lan-feature) y las instrucciones del fabricante.

En un Synology compatible, activa Wake-on-LAN en **Panel de control > Hardware y alimentación > General**, para la interfaz LAN correcta. Los menús y compatibilidad dependen del modelo: consulta [las instrucciones de Synology](https://kb.synology.com/es-mx/DSM/help/DSM/AdminCenter/system_hardware_general?version=7).

Home Assistant debe seguir encendido y su paquete de encendido debe llegar a la red correcta. No abras puertos WakeLink a Internet. WakeLink no arranca una VM VirtualBox/u otro hipervisor que esté detenida.

## Actualizar sin volver a vincular

Hay **dos actualizaciones**: la aplicación del equipo y la integración Home Assistant. Una no actualiza la otra. Matterbridge y su complemento Alexa también son independientes.

1. Crea una copia en **Configuración > Sistema > Copias de seguridad**; espera a que termine y conserva la clave de cifrado. Conserva una copia protegida del estado WakeLink del equipo y el instalador anterior.
2. **Windows:** abre WakeLink **Actualizaciones > Buscar actualizaciones** y descarga/ejecuta el instalador ofrecido. El clic izquierdo en la bandeja abre la app; el derecho abre su menú. La búsqueda necesita acceso a GitHub y una publicación nueva con instalador Windows; no encuentra pruebas locales sin publicar ni betas solo de la integración.
3. **Ubuntu:** abre WakeLink, pulsa **Buscar actualizaciones > Instalar actualización** y autoriza Ubuntu. El actualizador se incluye en beta.13 y en la prueba local beta.12 que ya lo tenía. **DSM:** añade una vez la [fuente WakeLink](INSTALL_DSM.es.md#actualizaciones-en-el-centro-de-paquetes), pulsa **Actualizar** en el Centro de paquetes y sigue el asistente. También puedes instalar el `.spk` oficial encima mediante **Instalación manual**. Ninguna ruta requiere volver a vincular.
4. En **HACS > WakeLink**, instala la versión nueva y reinicia Home Assistant. Si no aparece una beta, revisa el selector de versiones y la opción HACS de mostrar betas. No elijas un cambio sin probar de la rama predeterminada solo para obtener un número más alto.
5. Comprueba el equipo existente y los sensores. No debería pedir otro código. Si inesperadamente aparece la configuración inicial, detente y conserva la copia y el error.

Una copia Home Assistant respalda Home Assistant, no un Windows/Ubuntu independiente. El estado del equipo contiene credenciales: no lo compartas. Rutas predeterminadas: Windows `C:\ProgramData\PC Power Free` (salvo personalización), Ubuntu `/etc/pc-power-free/`, DSM `/var/packages/pcpowerfree/var/`.

## Volver atrás

Conserva la entrada Home Assistant y los datos de la app. Reinstala la versión anterior de la integración desde HACS si aparece, o restaura la copia verificada anterior a actualizar. Una restauración puede eliminar otros cambios posteriores: revisa qué contiene.

Para la aplicación del equipo, sigue su guía y utiliza una copia probada que conserve el estado. **El instalador antiguo por sí solo no garantiza poder volver atrás**, especialmente DSM, que puede rechazar una revisión inferior. No desinstales para forzar un regreso. Dispositivos Alexa/tokens pueden necesitar retirada aparte: restaurar Home Assistant no deshace la vinculación externa.

## Windows SmartScreen

El instalador actualmente **no tiene firma digital**. Microsoft puede advertir de una app desconocida; recompilarla o cambiarle el nombre no garantiza eliminar ese aviso.

1. Comprueba que el instalador procede de los **Assets** de este proyecto.
2. Descarga `SHA256SUMS.txt` de la **misma publicación**.
3. En PowerShell ejecuta esta comprobación de solo lectura, sustituyendo la ruta de ejemplo por la de tu archivo:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath "$env:USERPROFILE\Downloads\WakeLink-Windows-x64-Setup.exe"
```

4. Compara la suma completa con la línea de ese archivo. Si no coincide, **no lo ejecutes**. Si coincide, confirma los bytes descargados, no la identidad del autor ni una auditoría independiente.
5. Si confías en el origen comprobado, tú decides si usas **Más información > Ejecutar de todas formas**. Si no aparece o tu organización lo bloquea, detente: no desactives SmartScreen/antivirus ni eludas la política.

Firma y reputación son diferentes: [explicación de Microsoft](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

## Problema de icono HACS o Alexa

La ausencia del icono en la tienda HACS es un [problema externo conocido](KNOWN_ISSUES.md#espanol), no una instalación fallida. Reinstalar o volver a vincular WakeLink no lo soluciona.

Para Alexa sigue [la guía con capturas](ALEXA.es.md), incluida la asignación y **guardado** de la etiqueta de entidad antes de configurar **Filter By Label**. No retires el filtro porque no aparezca ningún dispositivo.

## Informar de un problema sin exponer datos

Usa [GitHub Issues](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/issues). Incluye sistema/versión, versión de app/paquete WakeLink, integración, paso de la guía, error exacto y captura sin datos privados. En DSM incluye la revisión numérica del paquete. No compartas copias de configuración, contraseñas, tokens, códigos de vinculación ni QR Matter.
