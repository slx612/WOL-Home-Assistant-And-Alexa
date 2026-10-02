# Release and HACS checklist / Publicación y HACS

[Current user guides / Guías de usuario](README.md)

## English

**Maintainers only.** WakeLink is already in HACS's default catalog ([accepted submission #7156](https://github.com/hacs/default/pull/7156)); do not resubmit each release. HACS installs `custom_components/pc_power_free`, not the Windows/Linux/DSM app.

Keep the visible name **WakeLink** and preserve internal IDs/discovery types and data paths. Keep `brand/icon.png` and `brand/logo.png` aligned with the Windows icon. Local brand images follow [Home Assistant](https://developers.home-assistant.io/docs/core/integration/brand_images/) and [HACS requirements](https://hacs.xyz/docs/publish/integration/). The store-icon defect is [tracked separately](KNOWN_ISSUES.md): no unsupported `hacs.json` image field or integration-domain rename fixes the released HACS frontend.

### Before publishing

1. Align app/integration/installer/resource versions for changed components. For DSM-only updates, increase the numeric package revision and state its app version separately.
2. Run `python -m unittest discover -s tests -q`, `node tests/test_dsm_desktop.js`, relevant package checks, HACS validation and hassfest. Source tests are not hardware/upgrade validation.
3. Test in-place upgrades and preserve entry/entity IDs, machine ID, token, certificate/key, options and guard state. Do not uninstall or pair again to hide an upgrade failure.
4. Build/inspect the actual assets. For Windows publish `WakeLink-Windows-x64-Setup.exe` plus identical `pcpowerfree-windows-x64-setup.exe` for existing updaters. Include `WakeLink-Home-Assistant.zip` for manual installs. Publish Ubuntu/DSM installers only with their corresponding current instructions.
5. Create `SHA256SUMS.txt` from the uploaded files and a **GitHub prerelease with assets**, not just a tag. Do not use `/releases/latest` as a guaranteed beta download. Check asset links and the Windows update checker.
6. Update both language versions together: exact filenames, button labels, checkpoints, local-versus-published status and tested limitations. English Home Assistant/DSM screenshots must be English; Spanish ones Spanish. Redact credentials, codes and private addresses.
7. Keep current user guides version-neutral except clearly identified local-preview filenames/revisions. Keep old records in [History](HISTORY.md), with a warning at their own entry point.
8. Keep beta and platform-specific limitations explicit. Alexa requires external Matterbridge/`matterbridge-hass`; discovery alone does not validate both power directions. Unsigned installers/checksums are not publisher signatures or an independent security audit.

### Current release gap

The public beta.12 DSM asset is revision 0012; the current guided DSM test is revision 0021. Ubuntu's desktop `.deb` is local only. Do not tell public users to download those new flows until corresponding installers and release notes are actually published. Never modify already-published historical notes to imply later tests happened in that release.

## Español

**Solo mantenimiento.** WakeLink ya está en el catálogo HACS ([alta aceptada #7156](https://github.com/hacs/default/pull/7156)); no se solicita otra vez por cada versión. HACS instala la integración, no los programas Windows/Linux/DSM.

Conserva nombre visible **WakeLink**, identificadores internos y rutas. Las imágenes `brand/icon.png` y `brand/logo.png` deben coincidir con el símbolo Windows. El fallo de tienda HACS está [documentado aparte](KNOWN_ISSUES.md): no se resuelve inventando campos ni cambiando el dominio.

### Antes de publicar

1. Alinea las versiones de los componentes modificados. Para cambios solo DSM, incrementa la revisión numérica y distingue la versión de la app.
2. Ejecuta las pruebas Python, escritorio DSM, comprobaciones de paquetes, HACS y hassfest. Una prueba de código no valida hardware ni una actualización real.
3. Prueba actualizar encima y conservar identificadores, token, certificado/clave, ajustes y protección. No desinstales ni repitas vinculación para ocultar un fallo.
4. Inspecciona los archivos compilados. Publica el instalador Windows visible y su copia antigua idéntica; el ZIP Home Assistant es para instalaciones manuales. Los instaladores Ubuntu/DSM deben corresponder a sus guías.
5. Genera `SHA256SUMS.txt` de los archivos publicados y una **publicación preliminar con Assets**, no solo etiqueta. No garantices que `/releases/latest` contenga betas. Comprueba enlaces y actualizador Windows.
6. Actualiza ambos idiomas a la vez, con nombres exactos, comprobaciones, estado local/publicado y límites. Capturas inglesas Home Assistant/DSM en inglés; españolas en español. Oculta credenciales, códigos y direcciones privadas.
7. Evita fijar versiones en las guías salvo las pruebas locales claramente identificadas. Las notas antiguas van al [Historial](HISTORY.md), con aviso en cada documento.
8. Conserva el estado beta y límites reales: descubrir en Alexa no prueba apagar/encender; Matterbridge y su complemento son externos. Ni las sumas ni un instalador sin firma equivalen a identificar al autor o auditar la seguridad.

### Diferencia pendiente de publicación

DSM beta.12 público es revisión 0012; la prueba guiada actual es 0021. El `.deb` gráfico Ubuntu solo existe localmente. No anuncies esos recorridos como disponibles hasta publicar sus instaladores y notas. No reescribas notas antiguas como si pruebas posteriores se hubieran realizado en aquella versión.
