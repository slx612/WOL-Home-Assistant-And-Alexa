# WakeLink con Alexa: guia paso a paso

[English](ALEXA.en.md) | [Espanol](ALEXA.es.md) | [Instalar WakeLink primero](GETTING_STARTED.es.md)

**Estado: beta; aun no se ha probado de principio a fin con un Echo real.** WakeLink no se conecta directamente con Alexa. El recorrido es **PC con WakeLink -> Home Assistant -> Matterbridge -> Alexa**. Matterbridge y su complemento `matterbridge-hass` son independientes y deben seguir funcionando en Home Assistant cuando el PC este apagado. No hay suscripcion de terceros, pero Alexa puede necesitar Internet para entender la voz.

Necesitas el PC ya vinculado a WakeLink en Home Assistant, Home Assistant OS con el menu **Aplicaciones** (antes **Complementos**), un [Echo compatible con Matter](https://developer.amazon.com/docs/alexaplus/smarthome/matter-support.html) y la app Alexa en el movil. Echo y Home Assistant deben verse en la red local. **No necesitas instalar la integracion Matter de Home Assistant:** sirve para recibir dispositivos Matter, no para publicar este PC en Alexa.

Hay **dos codigos distintos**: el codigo de **seis cifras de WakeLink** vincula el PC con Home Assistant; el **QR Matter de Matterbridge** vincula el puente con Alexa. No escanees el QR hasta el paso 6.

## 1. Comprueba el PC y haz una copia

1. Sigue [la instalacion de WakeLink](GETTING_STARTED.es.md) si todavia no ves el PC en **Configuracion > Dispositivos y servicios > WakeLink**.
2. Abre ese PC y localiza su **interruptor de encendido**. Abre los detalles de la entidad y apunta su **ID**, por ejemplo `switch.mi_pc_power`. Debe empezar por `switch.`. No pulses el interruptor para mirar si funciona: pasarlo a apagado puede apagar el PC.
3. Crea una copia en **Configuracion > Sistema > Copias de seguridad**. Conserva su clave de cifrado en privado.
4. Si ya compartias ese PC con Alexa mediante Emulated Hue, quita primero esa exposicion para evitar duplicados. Si **Matterbridge ya esta vinculado a Alexa**, no sigas esta receta de primera instalacion: un complemento nuevo sin filtrar podria compartir otros dispositivos. Configura un filtro seguro antes de conectarlo o usa una instancia aislada.

**Comprueba antes de seguir:** tienes el ID exacto del `switch.` y la copia de seguridad.

## 2. Instala y abre Matterbridge

1. En Home Assistant abre **Configuracion > Aplicaciones > Tienda de aplicaciones**. En versiones antiguas, **Aplicaciones** se llama **Complementos**.
2. Abre el menu **... > Repositorios**, pega `https://github.com/Luligu/matterbridge-home-assistant-addon` y pulsa **Anadir**. Es el [repositorio oficial](https://github.com/Luligu/matterbridge-home-assistant-addon).
3. Busca **Matterbridge**, pulsa **Instalar** y espera. Activa **Iniciar al arrancar** para que funcione con el PC apagado. Pulsa **Iniciar** y **Abrir interfaz web**. El primer inicio puede tardar varios minutos; si aparece «La aplicacion no esta lista», espera y pulsa **Volver a intentar**.
4. Arriba veras **Home | Devices | Logs | Settings**. **Home** ya muestra un QR. **No lo escanees todavia.**

**Comprueba:** la interfaz abre y en **Home** aparece **Install plugins**. Si no, revisa el registro de la aplicacion en Home Assistant.

## 3. Selecciona la red correcta

1. En otra pestana de Home Assistant abre **Configuracion > Sistema > Red**. Apunta el nombre de la interfaz principal que tiene la direccion de tu red domestica. Puede ser `end0`, `eth0` u otro: no copies un ejemplo a ciegas.
2. Vuelve a Matterbridge, pulsa **Settings** arriba y busca **Matter settings > Mdns interface**. Escribe exactamente ese nombre. Guarda y reinicia Matterbridge si lo pide.

**Comprueba:** en **Home > System info**, **Interface name** corresponde a esa red. Una red de invitados que aisle el Echo puede impedir la deteccion.

## 4. Marca solo el interruptor del PC

1. En Home Assistant abre **Configuracion > Areas, etiquetas y zonas > Etiquetas > Crear etiqueta**. Llamala `WakeLink Alexa`. Importan las mayusculas y los espacios.
2. Ve a **Configuracion > Dispositivos y servicios > Entidades** y busca el ID `switch.` del paso 1. Activa el modo de seleccion de la tabla, marca **solo esa entidad**, pulsa **Anadir etiqueta** y elige `WakeLink Alexa`. Si tu version permite asignarla desde los ajustes de la entidad, tambien vale.
3. **No** apliques esa etiqueta al dispositivo completo, a un area o a otras entidades. Comprueba en la lista que solo el interruptor previsto tiene `WakeLink Alexa`.

**Comprueba:** la etiqueta identifica una sola entidad. Sera el filtro antes de compartir nada con Alexa.

## 5. Instala el complemento y limita lo que exporta

1. En **Matterbridge > Home > Install plugins**, escribe `matterbridge-hass` en **Plugin name or plugin path**, deja **Tag or version** en `latest` y pulsa **Install**. Espera a que aparezca en **Plugins**. **No escanees el QR.**
2. En Home Assistant pulsa tu usuario, abajo a la izquierda, y entra en **Seguridad > Tokens de acceso de larga duracion > Crear token**. Llamalo, por ejemplo, `Matterbridge WakeLink`. Copialo al crearlo. Es una clave con acceso amplio a Home Assistant: no la pongas en WakeLink, GitHub, capturas ni chats.
3. En la fila **Plugins > matterbridge-hass** abre su configuracion. En **Host** pon la direccion WebSocket de Home Assistant, normalmente `ws://homeassistant.local:8123` en una red privada de confianza. Si usas HTTPS con certificado valido, usa `wss://` y tu nombre de host real. `ws://` no cifra el token: no lo uses en redes no confiables. No desactives la validacion de certificados para ocultar un error.
4. Pega el token en **Token**. En **Filter By Label** elige/escribe exactamente `WakeLink Alexa`. En **Domain Whitelist** deja solo `switch`. Guarda y reinicia el complemento si lo pide. **No uses Split Entities:** esta obsoleto y no hace falta en esta ruta. Una **Whitelist** vacia no es un filtro; aqui el filtro es **Filter By Label**.
5. Abre **Matterbridge > Devices**. Debe aparecer **exactamente un dispositivo** de `matterbridge-hass`: el interruptor del PC. Si hay cero, revisa Host, Token y etiqueta. Si hay mas de uno, **no vincules Alexa**: revisa la etiqueta y el filtro.

**Comprobacion obligatoria:** no vayas al QR hasta ver solo el PC previsto en **Devices**. El complemento puede mostrar muchos dispositivos si no se filtra bien.

## 6. Vincula Matterbridge con Alexa

1. En Matterbridge abre **Home** y deja visible **QR pairing code**. No es el codigo de seis cifras de WakeLink. No publiques el QR ni el codigo manual: alguien en tu red podria intentar vincular el puente.
2. En el movil abre **Alexa > Dispositivos > + > Anadir dispositivo > Otro > Matter**. Confirma las preguntas y pulsa **Escanear codigo QR**. Escanea el QR de Matterbridge. Los textos pueden variar segun la version de Alexa; busca la opcion **Matter**.
3. Espera a que Alexa encuentre el puente y el interruptor. Dale al PC un nombre claro, como **PC del despacho**. Si aparecen otros dispositivos de Home Assistant, elimina el puente de Alexa, corrige el filtro del paso 5 y no pruebes ordenes de voz.
4. Primero comprueba que el PC **aparece** en Alexa. Para probar el apagado, guarda tu trabajo y di «Alexa, apaga PC del despacho». Solo si Wake-on-LAN ya funciona desde Home Assistant, prueba «Alexa, enciende PC del despacho» con el PC apagado.

**Resultado esperado:** un solo PC en Alexa que responda a ambas ordenes. Acabar la guia no demuestra que esto funcione: hay que probarlo en un Echo real.

## Si falla o quieres deshacerlo

- **Matterbridge no esta lista:** espera, pulsa **Volver a intentar** y, si persiste, revisa los registros de la aplicacion en Home Assistant.
- **Devices muestra cero:** comprueba que WakeLink funciona, que la etiqueta esta en la *entidad* `switch.`, y que Host/Token conectan `matterbridge-hass`.
- **Devices muestra mas de uno:** no escanees el QR. Quita etiquetas sobrantes o corrige **Filter By Label**, reinicia el complemento y vuelve a contar.
- **Alexa no lo encuentra:** revisa **Mdns interface**, la compatibilidad Matter del Echo y que Echo, movil y Home Assistant puedan comunicarse localmente.
- **Alexa no enciende el PC:** prueba primero Wake-on-LAN desde Home Assistant. Matterbridge no puede cambiar la BIOS/UEFI ni el adaptador de red.
- **Deshacer:** elimina el puente Matterbridge de Alexa, desactiva/elimina `matterbridge-hass` y **revoca su token** en **Home Assistant > tu perfil > Seguridad**. Puedes quitar la etiqueta. Conserva el PC y la vinculacion WakeLink. Restaurar una copia no revoca por si solo el token ni borra el dispositivo de Alexa.

Fuentes: [aplicacion Matterbridge](https://github.com/Luligu/matterbridge-home-assistant-addon/blob/main/DOCS.md), [filtros de `matterbridge-hass`](https://github.com/Luligu/matterbridge-hass/discussions/186), [etiquetas en Home Assistant](https://www.home-assistant.io/docs/organizing/labels/), [Matter en Amazon](https://developer.amazon.com/docs/alexaplus/smarthome/matter-support.html).
