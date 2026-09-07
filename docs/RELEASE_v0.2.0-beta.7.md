# PC Power Free v0.2.0-beta.7

Security and reliability prerelease. **Ready for testing, not a stable or fully hardware-validated release.**

## Downloads

- [Windows installer](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/download/v0.2.0-beta.7/pcpowerfree-windows-x64-setup.exe)
- [Home Assistant integration ZIP](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/releases/download/v0.2.0-beta.7/pcpowerfree-home-assistant-integration.zip)
- Standalone Windows executables, experimental Linux/DSM packages and `SHA256SUMS.txt` are under Assets.

## Upgrade without re-pairing

Install over beta.6 **without uninstalling**, and update the HA integration too. Both update orders are supported; control may be temporarily unavailable until both components are updated. Existing pairing, devices and automation references are preserved. Do not delete the HA entry or generate a new token/code.

The Windows installer reuses existing settings without repeating setup. The saved secret automatically authenticates the new TLS identity before HA sends credentials. Existing disabled startup settings stay disabled.

Other fixes include guarded/atomic state storage, bounded discovery and HTTP handling, serialized one-use pairing codes, Windows startup-task recovery, correct HA reloads and clearer power-command failures.

**Verification:** 56 local tests pass, including real beta.6 Python client/agent compatibility checks with fake power actions. Release packages and embedded Windows code were checked against source. Real in-place installation, HA/Alexa and hardware power-cycle tests are still pending. The Windows installer is unsigned; DSM power actions remain experimental. The migration binding has not had an independent cryptographic audit.

[Detailed English upgrade guide](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/v0.2.0-beta.7/docs/UPGRADE-beta.7.md#english) | [Validation and limitations](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/v0.2.0-beta.7/docs/VALIDATION-beta.7.md)

## Espanol

Beta de seguridad y fiabilidad: **preparada para probar, no es una version estable ni completamente validada en hardware real**.

Actualiza sobre beta.6 **sin desinstalar**, y actualiza tambien la integracion de HA. Puedes hacerlo en cualquier orden; puede faltar temporalmente el control entre ambos pasos. Se conservan la vinculacion, los dispositivos y las referencias de las automatizaciones. No borres la entrada de HA ni generes otra clave o codigo.

El instalador reutiliza la configuracion sin repetir el asistente. La clave guardada permite verificar la nueva conexion cifrada automaticamente. Si habias desactivado el inicio automatico, seguira desactivado.

Las 56 pruebas locales pasan y los paquetes estan comprobados. Faltan pruebas reales de instalacion, HA/Alexa y ciclos de energia. El instalador Windows no esta firmado y las acciones de energia en DSM siguen siendo experimentales.

[Guia detallada en espanol](https://github.com/slx612/WOL-Home-Assistant-And-Alexa/blob/v0.2.0-beta.7/docs/UPGRADE-beta.7.md#espanol)
