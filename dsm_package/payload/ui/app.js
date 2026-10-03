const words = {
  en: {
    eyebrow: "YOUR NAS, ON YOUR TERMS", title: "Connect this NAS.",
    lead: "WakeLink stays on your local network. Authorize NAS power control once, then link Home Assistant.",
    statusTitle: "AGENT STATUS", loading: "Checking WakeLink...", online: "Agent running", offline: "Agent unavailable",
    login: "DSM administrator session required", refresh: "Refresh",
    loginHelp: "Sign in to the DSM desktop with an administrator account and open WakeLink from the application menu. WakeLink uses that session automatically.",
    openDesktop: "Open DSM desktop",
    device: "DEVICE", address: "LOCAL ADDRESS", unknown: "Not detected",
    pairingLabel: "HOME ASSISTANT", pairingTitle: "Link this NAS", pairingHint: "Already linked? No new code is needed. Generate one only to connect another Home Assistant installation.",
    pairButton: "Generate pairing code", working: "Generating...", pairError: "Could not generate a code. Check the agent and your DSM permissions.",
    codeLabel: "YOUR TEMPORARY CODE", codeExpiry: "Valid for 10 minutes. Existing connections stay linked.", copy: "Copy code", copied: "Copied", manualCopy: "Select and copy the code above.",
    next: "NEXT STEPS", stepsTitle: "Finish in Home Assistant", step1: "Install WakeLink from HACS in Home Assistant.", step2: "Open Settings > Devices & services and select this NAS when discovered.", step3: "Enter the six-digit code shown above.",
    powerLabel: "ONE-TIME PERMISSION", powerTitle: "Allow NAS power control", powerButton: "Authorize shutdown and restart",
    powerHint: "DSM will ask you to confirm your password in its own secure dialog. Only normal shutdown and restart are allowed. This setup does not turn off the NAS or change existing connections.",
    powerReady: "Permission enabled. No further setup needed.", powerMissing: "Power control is not authorized yet.", powerWorking: "Waiting for DSM confirmation...",
    powerUnavailable: "Open WakeLink from the HTTPS DSM desktop to authorize power control.",
    powerError: "Could not complete the permission setup. Refresh to check its status. If a disabled WakeLink power setup task remains in DSM's Task Scheduler, remove that task before retrying.",
    footer: "Alexa setup is separate and uses Home Assistant."
  },
  es: {
    eyebrow: "TU NAS, A TU MANERA", title: "Conecta este NAS.",
    lead: "WakeLink funciona en tu red local. Autoriza el control de energía una vez y vincula Home Assistant.",
    statusTitle: "ESTADO DEL AGENTE", loading: "Comprobando WakeLink...", online: "Agente en marcha", offline: "Agente no disponible",
    login: "Se necesita una sesión administradora de DSM", refresh: "Actualizar",
    loginHelp: "Entra en el escritorio de DSM con una cuenta administradora y abre WakeLink desde el menú de aplicaciones. WakeLink utiliza esa sesión automáticamente.",
    openDesktop: "Abrir escritorio DSM",
    device: "DISPOSITIVO", address: "DIRECCIÓN LOCAL", unknown: "No detectada",
    pairingLabel: "HOME ASSISTANT", pairingTitle: "Vincula este NAS", pairingHint: "¿Ya está vinculado? No necesitas otro código. Genéralo solo para conectar otra instalación de Home Assistant.",
    pairButton: "Generar código de vinculación", working: "Generando...", pairError: "No se pudo generar el código. Comprueba el agente y tus permisos en DSM.",
    codeLabel: "TU CÓDIGO TEMPORAL", codeExpiry: "Válido durante 10 minutos. Las conexiones anteriores siguen vinculadas.", copy: "Copiar código", copied: "Copiado", manualCopy: "Selecciona y copia el código de arriba.",
    next: "SIGUIENTES PASOS", stepsTitle: "Termina en Home Assistant", step1: "Instala WakeLink desde HACS en Home Assistant.", step2: "Abre Ajustes > Dispositivos y servicios y selecciona este NAS cuando aparezca.", step3: "Introduce el código de seis cifras mostrado arriba.",
    powerLabel: "PERMISO INICIAL", powerTitle: "Permitir el control del NAS", powerButton: "Autorizar apagado y reinicio",
    powerHint: "DSM pedirá confirmar tu contraseña en su propio diálogo seguro. Solo se permite el apagado y reinicio normales. Este paso no apaga el NAS ni cambia las vinculaciones anteriores.",
    powerReady: "Permiso activado. No necesitas configurarlo de nuevo.", powerMissing: "El control de energía todavía no está autorizado.", powerWorking: "Esperando la confirmación de DSM...",
    powerUnavailable: "Abre WakeLink desde el escritorio HTTPS de DSM para autorizar el control de energía.",
    powerError: "No se pudo completar la autorización. Pulsa Actualizar para comprobar el permiso. Si queda una tarea deshabilitada WakeLink power setup en el Programador de tareas de DSM, elimina esa tarea antes de repetir.",
    footer: "Alexa se configura aparte a través de Home Assistant."
  }
};

const $ = (id) => document.getElementById(id);
let language = navigator.language.toLowerCase().startsWith("es") ? "es" : "en";
let status = "loading";
let powerEnabled = false;
let powerWorking = false;
try { language = localStorage.getItem("wakelink-language") || language; } catch (_) { /* Storage can be disabled in DSM. */ }
if (!words[language]) language = "en";

function translate() {
  document.documentElement.lang = language;
  for (const element of document.querySelectorAll("[data-i18n]")) {
    element.textContent = words[language][element.dataset.i18n];
  }
  for (const button of document.querySelectorAll("[data-lang]")) {
    button.setAttribute("aria-pressed", String(button.dataset.lang === language));
  }
  $("status-line").textContent = words[language][status];
  renderPower();
}

function renderPower() {
  $("power-panel").hidden = status !== "online";
  $("power-status").textContent = words[language][powerWorking ? "powerWorking" : powerEnabled ? "powerReady" : "powerMissing"];
  $("authorize-power").disabled = status !== "online" || powerEnabled || powerWorking;
  $("authorize-power").hidden = powerEnabled;
}

function setStatus(next) {
  status = next;
  $("status-line").className = "status-line " + next;
  $("status-line").textContent = words[language][next];
  $("pair").disabled = next !== "online";
  $("network").hidden = next !== "online";
  $("dsm-login").hidden = next !== "login";
  renderPower();
}

async function setupHeaders() {
  const headers = {};
  if (window.parent !== window) {
    const api = window.parent.synowebapi;
    if (api?.env?.getRequestHeaders) {
      await api.env.getCredential?.()?.WaitForReady?.();
      const native = api.env.getRequestHeaders();
      for (const name of ["X-SYNO-TOKEN", "X-SYNO-HASH"]) {
        if (native[name]) headers[name] = native[name];
      }
    } else {
      const token = window.parent.SYNO?.SDS?.Session?.SynoToken;
      if (token) headers["X-SYNO-TOKEN"] = token;
    }
  }
  return headers;
}

async function loadStatus() {
  setStatus("loading");
  try {
    const response = await fetch("setup.cgi?action=status", {
      credentials: "same-origin", cache: "no-store", headers: await setupHeaders()
    });
    if (response.status === 403) { setStatus("login"); return; }
    if (!response.ok) throw new Error("Agent unavailable");
    const info = await response.json();
    if (!info.online) throw new Error("Agent unavailable");
    $("hostname").textContent = info.hostname || words[language].unknown;
    $("address").textContent = info.ip_address || words[language].unknown;
    $("mac").textContent = info.mac_address || words[language].unknown;
    powerEnabled = info.power_permission_enabled === true;
    setStatus("online");
  } catch (_) {
    setStatus("offline");
  }
}

async function authorizePower() {
  $("power-error").hidden = true;
  const dsmWindow = window.parent !== window ? window.parent.SYNO?.SDS?.WakeLink?.activeWindow : null;
  if (location.protocol !== "https:" || !dsmWindow?.authorizePowerPermission) {
    $("power-error").textContent = words[language].powerUnavailable;
    $("power-error").hidden = false;
    return;
  }
  powerWorking = true;
  renderPower();
  try {
    await dsmWindow.authorizePowerPermission();
    await loadStatus();
  } catch (error) {
    $("power-error").textContent = words[language].powerError;
    if (["create", "get", "run", "get_history_status_list", "delete", "verify", "helper"].includes(error?.setupStage)) {
      $("power-error").textContent += ` DSM: ${error.setupStage} (${Number.isInteger(error.dsmCode) ? error.dsmCode : "unknown"}).`;
    }
    $("power-error").hidden = false;
    await loadStatus();
  } finally {
    powerWorking = false;
    renderPower();
  }
}

async function generateCode() {
  $("pair").disabled = true;
  $("pair").textContent = words[language].working;
  $("pair-error").hidden = true;
  $("code-card").hidden = true;
  try {
    const response = await fetch("setup.cgi?action=pair", {
      method: "POST", credentials: "same-origin", cache: "no-store",
      headers: { ...await setupHeaders(), "X-WakeLink-Action": "pair" }
    });
    if (!response.ok) throw new Error("Pairing unavailable");
    const result = await response.json();
    if (!/^[0-9]{6}$/.test(result.pairing_code)) throw new Error("Invalid code");
    $("pairing-code").textContent = result.pairing_code;
    $("code-card").hidden = false;
  } catch (_) {
    $("pair-error").textContent = words[language].pairError;
    $("pair-error").hidden = false;
  } finally {
    $("pair").disabled = status !== "online";
    $("pair").textContent = words[language].pairButton;
  }
}

async function copyCode() {
  const code = $("pairing-code").textContent;
  try {
    await navigator.clipboard.writeText(code);
    $("copy").textContent = words[language].copied;
  } catch (_) {
    $("copy").textContent = words[language].manualCopy;
  }
}

for (const button of document.querySelectorAll("[data-lang]")) {
  button.addEventListener("click", () => {
    language = button.dataset.lang;
    try { localStorage.setItem("wakelink-language", language); } catch (_) { /* Optional preference. */ }
    translate();
  });
}
$("refresh").addEventListener("click", loadStatus);
$("pair").addEventListener("click", generateCode);
$("authorize-power").addEventListener("click", authorizePower);
$("copy").addEventListener("click", copyCode);
$("desktop-link").href = `${location.origin}/`;
translate();
loadStatus();
