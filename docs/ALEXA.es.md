# Conectar un PC WakeLink con Alexa (prueba Matter)

[English](ALEXA.en.md) | [Espanol](ALEXA.es.md) | [Antes: Windows + Home Assistant](GETTING_STARTED.es.md)

**Estado: experimental; aun no se ha probado de principio a fin con un Echo.** WakeLink no habla Matter por si mismo. El recorrido actual es **PC WakeLink -> Home Assistant -> Matterbridge + `matterbridge-hass` -> Alexa**. Matterbridge es otra aplicacion/complemento y debe seguir funcionando cuando el PC este apagado. Necesitas un [Echo compatible con Matter](https://developer.amazon.com/docs/alexaplus/smarthome/matter-support.html), la app movil de Alexa y una red local de confianza. No hace falta una suscripcion de terceros. Estas pantallas pueden cambiar si Matterbridge o Alexa se actualizan.

## Antes de empezar

1. [Instala y vincula WakeLink con Home Assistant](GETTING_STARTED.es.md). En **Configuracion > Dispositivos y servicios > WakeLink > tu PC > Configurar > Conectar con Alexa**, apunta el ID del interruptor que muestra la primera pantalla, por ejemplo `switch.mi_pc_power`. No pulses todavia el interruptor: apagarlo apaga el PC.
2. Crea una copia de seguridad en **Configuracion > Sistema > Copias de seguridad**. Incluye la configuracion de Home Assistant y Matterbridge si ya esta instalado. Conserva su clave de cifrado en privado.
3. Si habias expuesto el mismo PC con Emulated Hue, quita esa exposicion antes de vincularlo por Matter o Alexa mostrara dos copias. Si Matterbridge *ya esta vinculado* a Alexa u otro controlador, detente: un complemento de Home Assistant sin filtrar podria exponer otros dispositivos. Usa una instancia nueva y aislada o configura un filtro seguro antes de conectarlo.

## Prepara Matterbridge

4. En Home Assistant abre **Configuracion > Aplicaciones > Tienda de aplicaciones > menu de tres puntos > Repositorios**. Anade el [repositorio oficial de Matterbridge](https://github.com/Luligu/matterbridge-home-assistant-addon): `https://github.com/Luligu/matterbridge-home-assistant-addon`. Instala **Matterbridge**, inicialo y abre **Interfaz web**. En versiones antiguas de Home Assistant puede llamarse **Complementos**.
5. En Matterbridge, busca **Settings > Matter mDNS interface** y elige la misma interfaz de red que aparece en **Home Assistant > Configuracion > Sistema > Red**. No adivines el nombre: depende de tu equipo. Matterbridge y el Echo deben poder descubrirse en la red local.
6. En la pagina de complementos de Matterbridge, instala **`matterbridge-hass`**. Es un complemento independiente; WakeLink no lo instala. **No** escanees aun el QR de Matterbridge con Alexa.
7. Crea un **token de acceso de larga duracion** en tu perfil de Home Assistant (**tu nombre > Seguridad**). Da acceso amplio a Home Assistant. Pegalo solo en el campo **Token** del complemento `matterbridge-hass`, nunca en WakeLink ni en un mensaje de soporte. En **Host** usa la direccion WebSocket de Home Assistant, normalmente `ws://homeassistant.local:8123` dentro de una red de confianza. Si Home Assistant usa HTTPS con certificado de confianza, usa `wss://`. `ws://` envia el token sin cifrar; no lo uses en una red que no sea de confianza. No desactives la verificacion del certificado para evitar un error HTTPS.

## Comparte solo este PC

8. En los ajustes del complemento, pon **Domain Whitelist** en `switch`. Pon en **Split Entities** el ID exacto del paso 1 y en **Whitelist** ese mismo ID. Guarda y reinicia el complemento. **Una Whitelist vacia puede exponer otros dispositivos.** `Split Entities` esta obsoleto en el proyecto original; si ya no aparece, detente y sigue las [instrucciones actuales de Split By Label](https://github.com/Luligu/matterbridge-hass#readme) en vez de improvisar.
9. Revisa la lista de dispositivos de Matterbridge **antes de vincular**. El complemento de Home Assistant debe exportar solo el interruptor de tu PC, no otras entidades. Si aparecen mas dispositivos, corrige los filtros y reinicia. No pases al QR hasta comprobarlo.

## Vincula Alexa

10. Abre la app Alexa en el movil: **Dispositivos > + > Anadir dispositivo > Otro > Matter > Si > Escanear codigo QR**. Escanea el **QR Matter de Matterbridge** que aparece en Matterbridge. *No* es el codigo de seis cifras de WakeLink para vincular el PC. El movil, Echo y Matterbridge deben estar en la misma red local detectable. Los textos pueden variar segun la version de Alexa.
11. Dale al interruptor un nombre claro, por ejemplo **PC del despacho**. Primero comprueba si Alexa lo muestra. Prueba "apaga PC del despacho" solo despues de guardar tu trabajo y decidir apagar el PC. Luego prueba a encenderlo desde apagado si Wake-on-LAN ya funciona desde Home Assistant. Terminar la guia de WakeLink no verifica estas acciones.

## Si falla o quieres deshacerlo

- **No aparece el QR/dispositivo:** revisa la interfaz mDNS, la compatibilidad Matter del Echo, multicast en la red y que Matterbridge siga funcionando.
- **Aparece pero no enciende:** primero haz que Wake-on-LAN funcione desde Home Assistant; Matterbridge no arregla la BIOS ni la red.
- **Aparecen otros dispositivos:** desvincula Matterbridge de Alexa, corrige los filtros y vincula de nuevo solo cuando la lista sea la prevista.
- **Deshacer:** elimina Matterbridge de Alexa, desactiva/elimina `matterbridge-hass` y revoca el token en tu perfil de Home Assistant. Conserva WakeLink y el PC vinculado. Una copia de Home Assistant puede restaurar sus ajustes, pero debes comprobar por separado la revocacion del token y la eliminacion del dispositivo en Alexa.

Referencias oficiales: [aplicacion Matterbridge para Home Assistant](https://github.com/Luligu/matterbridge-home-assistant-addon/blob/main/DOCS.md), [filtros de `matterbridge-hass`](https://github.com/Luligu/matterbridge-hass#readme), [Matter en Amazon](https://developer.amazon.com/docs/alexaplus/smarthome/matter-support.html).
