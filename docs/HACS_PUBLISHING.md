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

### Ubuntu updates before 1.0

**Included in beta.13.** The app checks GitHub on opening; Ubuntu's system updater does not discover WakeLink without an APT repository. The published `.deb` is `WakeLink-Ubuntu-0.2.0-beta.13.deb`. The earlier local beta.12 update-capable build can detect it.

- [x] Check on opening and through **Check for updates**, without blocking the window.
- [x] Install only an official, size/SHA-256-verified `.deb` with matching package metadata, through authorized Ubuntu APT. Stable installations exclude prereleases.
- [x] Exercise the installer on the VM with a synthetic release: preserve configuration and TLS identity byte-for-byte and restart the service. Network failures are errors.
- [x] Build and publish a newer real `.deb` as part of beta.13.
- [ ] Test the entire graphical GitHub-to-install flow, including cancellation of Ubuntu's authorization prompt. Installer/API tests do not cover this dialog.

### DSM package source

The VM accepted the static JSON catalog, discovered revision 0023 and downloaded it through native Package Center APIs. Installing that downloaded SPK worked. The 0021-to-0022 upgrade retained identity and the power grant. Use the normal unsigned-package wizard: quick upgrade must be disabled. The graphical wizard is still untested end-to-end.

Beta.13 public verification: DSM recognized the published HTTPS source and the downloaded revision 0024 installed with native `synopkg`; Ubuntu's real public update installer upgraded beta.12 to beta.13. Both retained configuration/TLS identity and authenticated with the existing credentials. The public source remains configured on the disposable DSM VM. No power orders were sent. See [release validation](RELEASE_v0.2.0-beta.13.md#validation-and-limits); do not mark the remaining graphical-dialog check complete.

After uploading and verifying the real release asset, run `dsm_package/build_repository.py SPK_PATH EXACT_GITHUB_ASSET_URL dsm_package/repository.json`, commit that generated catalog to the default branch, and verify the public HTTPS URL. Only then publish `https://raw.githubusercontent.com/slx612/WOL-Home-Assistant-And-Alexa/main/dsm_package/repository.json` as the package source. Update this catalog for each release; do not publish an entry for a missing/future asset. No Worker or paid hosting is required for the tested DSM 7.2 GET client.

### Beta.13 coverage

Beta.13 includes Ubuntu's desktop installer and DSM revision 0024; beta.12's old DSM asset remains unchanged at 0012. Guided fresh install was tested at 0021. Keep the graphical-dialog, fresh Ubuntu installation, physical hardware and downgrade checks distinct from installer/API success. Never modify historical release notes to imply later tests happened in that release.

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

### Actualizaciones Ubuntu antes de la 1.0

**Incluido en beta.13.** La ventana consulta GitHub al abrir; el actualizador Ubuntu no descubre WakeLink sin un repositorio APT. El `.deb` publicado es `WakeLink-Ubuntu-0.2.0-beta.13.deb`; la prueba local beta.12 con actualizador puede detectarlo.

- [x] Consultar al abrir y mediante **Buscar actualizaciones**, sin bloquear la ventana.
- [x] Instalar solo el `.deb` oficial con tamaño, SHA-256 e identidad verificados, mediante APT autorizado. Las versiones estables no ofrecen betas.
- [x] Probar el instalador en la VM con una publicación simulada: conservar configuración e identidad TLS exactamente y reiniciar el servicio. Los fallos de red se muestran como errores.
- [x] Compilar y publicar un `.deb` real nuevo en beta.13.
- [ ] Probar el recorrido gráfico completo desde GitHub, incluida la cancelación del permiso Ubuntu. Las pruebas del instalador/API no prueban ese diálogo.

### Fuente de paquetes DSM

La VM aceptó el JSON estático, detectó la revisión 0023 y la descargó mediante las API del Centro de paquetes. La instalación de ese SPK descargado funcionó. Actualizar 0021 a 0022 conservó identidad y permiso de energía. Hay que usar el asistente normal de paquete sin firma: no habilitar actualización rápida/silenciosa. Falta probar el asistente gráfico completo.

Verificación pública beta.13: DSM reconoció la fuente HTTPS publicada y el SPK 0024 descargado se instaló mediante `synopkg`; el actualizador real Ubuntu descargó e instaló beta.13 sobre beta.12. Se conservaron configuración e identidad TLS, y funcionaron las credenciales anteriores. La fuente pública queda configurada en la VM DSM prescindible. No se enviaron órdenes de energía. Consulta las [pruebas de versión](RELEASE_v0.2.0-beta.13.md#pruebas-y-límites); no marques completa la comprobación gráfica pendiente.

Después de subir y verificar el instalador real, ejecuta `dsm_package/build_repository.py RUTA_SPK URL_EXACTA_ASSET_GITHUB dsm_package/repository.json`, publica ese catálogo generado en la rama predeterminada y comprueba su URL HTTPS pública. Solo entonces anuncia `https://raw.githubusercontent.com/slx612/WOL-Home-Assistant-And-Alexa/main/dsm_package/repository.json` como fuente. Actualízalo en cada versión; no anuncies archivos futuros o ausentes. El cliente GET DSM 7.2 probado no necesita Worker ni alojamiento de pago.

### Cobertura beta.13

Beta.13 incluye instalador gráfico Ubuntu y revisión DSM 0024; el DSM antiguo beta.12 conserva su 0012 original. La instalación guiada limpia se probó en 0021. Distingue las pruebas gráficas, Ubuntu limpio, hardware físico y regreso a versiones anteriores del éxito del instalador/API. No reescribas notas antiguas como si pruebas posteriores hubieran ocurrido en aquella versión.
