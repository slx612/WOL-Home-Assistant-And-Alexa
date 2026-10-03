# HACS icon: known issue / Icono HACS: problema conocido

[Documentation / Documentación](README.md) | [English](#english) | [Español](#espanol)

## English

**Status checked on 2026-10-02: unresolved in released HACS; not fixed by this WakeLink documentation update.**

The HACS **store/downloads list** and its **Update entity** are different from Home Assistant's integration page. The installed WakeLink image works in Home Assistant, but the HACS list can still show **icon not available**.

The live list was inspected: it requests `https://brands.home-assistant.io/_/pc_power_free/dark_icon.png`. That old service returns a placeholder for WakeLink, not the image bundled with the integration. WakeLink already includes `custom_components/pc_power_free/brand/icon.png` and `logo.png`, matching the Windows symbol. Home Assistant 2026.3+ uses local brand images; [HA documents this mechanism](https://developers.home-assistant.io/docs/core/integration/brand_images/).

There is **no supported image-URL setting in hacs.json**. Current [HACS integration requirements](https://hacs.xyz/docs/publish/integration/) require the local brand directory; adding root images, renaming the domain or uploading new custom icons to the old brands repository is not the supported fix.

HACS's newer proposed solution has two parts: [repository icon endpoint #5388](https://github.com/hacs/integration/pull/5388) and [dashboard use of that endpoint #945](https://github.com/hacs/frontend/pull/945). It also addresses previews **before** an integration is installed. Both remained open/unmerged when checked. Earlier proposals are [frontend #937](https://github.com/hacs/frontend/pull/937) and [Update entity #5228](https://github.com/hacs/integration/pull/5228). The latest published HACS release checked was [2.0.5](https://github.com/hacs/integration/releases/tag/2.0.5).

**What to do:** keep WakeLink installed. Update HACS through its normal update route when a release includes the fix, then reload the browser and check both views. Reinstalling WakeLink, re-pairing or clearing its state will not change the legacy URL. No unofficial HACS patch has been installed. This cosmetic issue does not block device control, installation or updates.

## Espanol

**Estado comprobado el 02/10/2026: sin resolver en HACS publicado; esta revisión de documentación no lo arregla.**

La **lista de tienda/descargas** de HACS y su **entidad Update** son distintas de la ficha de integración Home Assistant. Home Assistant muestra el icono instalado de WakeLink, pero HACS puede seguir mostrando **icon not available**.

Se inspeccionó la lista real: pide `https://brands.home-assistant.io/_/pc_power_free/dark_icon.png`. Ese servicio antiguo devuelve un marcador, no la imagen incluida. WakeLink ya incorpora `custom_components/pc_power_free/brand/icon.png` y `logo.png`, con el símbolo Windows. Home Assistant 2026.3+ usa las imágenes locales; así lo explica [su documentación](https://developers.home-assistant.io/docs/core/integration/brand_images/).

**hacs.json no tiene una opción admitida para la URL del icono.** Los [requisitos actuales de HACS](https://hacs.xyz/docs/publish/integration/) piden la carpeta local de imágenes. Añadir imágenes en la raíz, cambiar el identificador o enviar iconos nuevos al repositorio antiguo no es la solución admitida.

La propuesta nueva HACS tiene dos partes: [servir el icono del repositorio #5388](https://github.com/hacs/integration/pull/5388) y [usarlo en la lista #945](https://github.com/hacs/frontend/pull/945). También contempla la vista previa **antes de instalar** la integración. Ambas seguían abiertas/sin integrar al comprobarlo. Las propuestas anteriores son [interfaz #937](https://github.com/hacs/frontend/pull/937) y [entidad Update #5228](https://github.com/hacs/integration/pull/5228). La última publicación HACS comprobada era [2.0.5](https://github.com/hacs/integration/releases/tag/2.0.5).

**Qué hacer:** conserva WakeLink instalado. Cuando HACS publique una versión con la corrección, actualízalo por su vía normal, recarga el navegador y comprueba ambas vistas. Reinstalar WakeLink, volver a vincular o borrar sus datos no cambia esa URL antigua. No se ha instalado ningún parche HACS no oficial. Es un fallo visual: no impide controlar equipos, instalar ni actualizar.
