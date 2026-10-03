# Release and HACS checklist / Publicación y HACS

[Current user guides / Guías de usuario](README.md)

## English

**Maintainers only.** WakeLink is already in HACS's [default catalog](https://github.com/hacs/default/pull/7156); do not resubmit each release. HACS installs the integration, not the desktop/NAS app.

1. Align the shared agent, integration, Windows installer and resource versions. Use a stable tag such as `v1.0.0`, with GitHub's prerelease flag **off**. For DSM, increase the complete package version; v1.0.0 uses `1.0.0-0001`.
2. Run `python -m unittest discover -s tests -q`, `node tests/test_dsm_desktop.js`, package inspection, HACS validation and hassfest. Windows-only and POSIX-only tests run on their respective systems.
3. Test actual in-place upgrades without uninstalling or pairing again. Preserve machine ID, token, certificate/key, guard state, options and Home Assistant identifiers. Test a fresh install separately; never substitute a fresh setup for migration validation.
4. Build and inspect the actual Windows, Ubuntu and DSM installers. Run `python tests/verify_packages.py --dsm-package dsm_package/dist/pcpowerfree-dsm-noarch-1.0.0-0001.spk` from a Windows build environment.
5. Publish both `WakeLink-Windows-x64-Setup.exe` and its byte-identical `pcpowerfree-windows-x64-setup.exe` alias, plus the Ubuntu `.deb`, DSM `.spk`, Home Assistant ZIP, optional server source and `SHA256SUMS.txt`. Do not upload probes, private configurations or credentials.
6. Check uploaded sizes/digests and links before publishing the draft. Stable releases can be marked latest; betas cannot rely on `/releases/latest`. Verify the old clients select the new installer and stable clients exclude future betas.
7. Update both language guides and release notes together. Keep exact filenames, UI labels, tested scope and limitations honest. English/Spanish Home Assistant and DSM screenshots must match their guide's language.
8. After publication, repeat public download/updater checks and publish the DSM catalog as described below. Record results in the release notes.

Preserve internal IDs, discovery types and state paths. Keep local `brand/icon.png` and `brand/logo.png` aligned with the Windows symbol. The [HACS store icon issue](KNOWN_ISSUES.md) is separate; do not rename the integration domain or invent a `hacs.json` image setting.

### DSM package source

Only after the SPK asset is public and verified, run `dsm_package/build_repository.py SPK_PATH EXACT_GITHUB_ASSET_URL dsm_package/repository.json`, commit the generated catalog to the default branch and verify its public URL. Users add this source once:

```text
https://raw.githubusercontent.com/slx612/WOL-Home-Assistant-And-Alexa/main/dsm_package/repository.json
```

The tested DSM 7.2 client accepts this static HTTPS catalog. Keep quick install/upgrade disabled: unsigned packages require the normal wizard. Package Center controls refresh times; this is not silent installation or a cloud control relay. Verify catalog size/MD5 against the uploaded SPK and preserve other configured sources.

### Validation boundaries

See [v1.0.0](RELEASE_v1.0.0.md) for release-specific evidence, and [history](HISTORY.md) for older records. Code, native installer/API, graphical dialogs and physical hardware are separate tests. Full native dialogs, other DSM/Echo models and downgrade are not implied by unit-test success. Alexa uses external Matterbridge and `matterbridge-hass`; the tester has confirmed real Echo shutdown and wake. Unsigned installers/checksums do not provide publisher identity or an independent security audit.

## Español

**Solo mantenimiento.** WakeLink ya está en el [catálogo HACS](https://github.com/hacs/default/pull/7156); no se solicita otra vez por versión. HACS instala la integración, no los programas de los equipos.

1. Alinea versiones del agente compartido, integración, instalador Windows y recursos. Publica la etiqueta estable `v1.0.0` sin marcarla como preliminar. DSM usa `1.0.0-0001`; incrementa su versión completa.
2. Ejecuta pruebas Python, escritorio DSM, inspección de paquetes, HACS y hassfest. Las pruebas exclusivas Windows/POSIX deben ejecutarse en su sistema.
3. Prueba actualizar encima sin desinstalar ni vincular otra vez: conserva identidad, token, certificado/clave, protección, opciones e identificadores Home Assistant. Comprueba la instalación limpia por separado, no como sustituto de la migración.
4. Compila e inspecciona los instaladores reales de los tres sistemas. Desde Windows ejecuta `python tests/verify_packages.py --dsm-package dsm_package/dist/pcpowerfree-dsm-noarch-1.0.0-0001.spk`.
5. Publica el instalador Windows y su alias antiguo idéntico, el `.deb`, el `.spk`, ZIP Home Assistant, fuente de servidor opcional y `SHA256SUMS.txt`. Nunca subas sondas, configuraciones privadas o credenciales.
6. Comprueba tamaños, sumas y enlaces antes de publicar el borrador. Una estable puede ser latest; no lo garantices para betas. Comprueba que los clientes anteriores detectan el instalador y los estables no ofrecen betas futuras.
7. Actualiza ambos idiomas a la vez: archivos exactos, botones, pruebas y límites reales. Capturas Home Assistant/DSM en el idioma de la guía.
8. Después de publicar, repite las pruebas de descargas/actualizador públicos y publica el catálogo DSM indicado abajo. Registra los resultados en las notas de versión.

Conserva IDs, descubrimiento y rutas internas. Usa el mismo símbolo Windows en las imágenes locales. El [icono HACS ausente](KNOWN_ISSUES.md) no se arregla cambiando el dominio ni inventando campos.

### Fuente de paquetes DSM

Después de publicar y verificar el SPK, ejecuta `dsm_package/build_repository.py RUTA_SPK URL_EXACTA_ASSET_GITHUB dsm_package/repository.json`, publica ese catálogo en la rama predeterminada y comprueba su URL pública indicada en inglés arriba. No anuncies archivos ausentes.

El DSM 7.2 probado admite ese catálogo estático HTTPS. Mantén desactivada la instalación/actualización rápida: un paquete sin firma usa el asistente normal. DSM controla las consultas; no es instalación silenciosa ni servidor de control. Comprueba tamaño/MD5 y conserva las otras fuentes.

### Límites de validación

Consulta [v1.0.0](RELEASE_v1.0.0.md) y el [historial](HISTORY.md). Distingue código, instalador/API, diálogos gráficos y hardware. Las pruebas automáticas no certifican diálogos completos, otros DSM/Echo ni vuelta atrás. Alexa usa Matterbridge y `matterbridge-hass` externos; el usuario confirmó apagado y encendido con un Echo real. Un instalador sin firma y sus sumas no identifican al autor ni equivalen a una auditoría independiente.
