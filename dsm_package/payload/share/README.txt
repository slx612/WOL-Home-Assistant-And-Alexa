WakeLink for Synology DSM - test version

English

Open WakeLink from the DSM desktop using an administrator session. Generate
a pairing code only to connect a new Home Assistant installation. Updating
does not require a new code or deleting the existing device.

For the one-time power grant, open WakeLink from the HTTPS DSM desktop and
select Authorize shutdown and restart. Confirm your password in DSM's native
dialog, not a WakeLink form. Wait for Permission enabled. No SSH is needed.
Only normal DSM shutdown and restart are granted; setup executes neither.
It runs a temporary disabled WakeLink power setup task, then removes it.
Advanced revocation before uninstalling still uses an administrator SSH session:
  sudo /usr/bin/python3 -I /var/packages/pcpowerfree/conf/power_permissions.py --remove

State lives under /var/packages/pcpowerfree/var/. Protect this directory:
it contains credentials. The internal package ID remains pcpowerfree to
preserve existing pairing. Python 3 is required; ifaddr and zeroconf are bundled.
The user reported working controls on the DSM 7.2 VM; uptime and boot time
recovered after startup. When the NAS is off or starting, these sensors can
be unavailable. They recover on a later Home Assistant poll; do not pair again.
Controlled restart, physical NAS Wake-on-LAN and package downgrade remain untested.

Espanol

Abre WakeLink desde el escritorio DSM con una sesion administradora. Genera
un codigo solo para vincular un Home Assistant nuevo. Al actualizar, no
borres el dispositivo ni generes otro codigo.

Para autorizar la energia, abre WakeLink desde el escritorio HTTPS de DSM,
pulsa Autorizar apagado y reinicio y confirma en el dialogo del propio DSM.
Espera a Permiso activado. No necesitas SSH ni se apaga o reinicia nada.
Solo se permiten las dos ordenes normales de DSM. La tarea temporal se elimina.
Para retirar el permiso antes de desinstalar, ejecuta el comando anterior
por SSH como administrador. No uses una copia del auxiliar bajo target/app.

Protege /var/packages/pcpowerfree/var/: contiene credenciales. El nombre interno
pcpowerfree conserva la vinculacion. El usuario comunico que los controles
funcionan en la VM DSM 7.2; los sensores se recuperaron tras el arranque.
Apagado o arrancando pueden salir como No disponible: espera a que el agente
responda. No hace falta volver a vincular. Faltan pruebas controladas de reinicio,
Wake-on-LAN en un NAS fisico y vuelta a un paquete anterior.
