const words = {
  en: {
    eyebrow: "YOUR NAS, ON YOUR TERMS", title: "Connect this NAS.",
    lead: "WakeLink stays on your local network. No subscription, fixed IP or terminal commands.",
    statusTitle: "AGENT STATUS", loading: "Checking WakeLink...", online: "Agent running", offline: "Agent unavailable",
    login: "Sign in to DSM with an administrator account, then try again.", refresh: "Refresh",
    device: "DEVICE", address: "LOCAL ADDRESS", unknown: "Not detected",
    pairingLabel: "HOME ASSISTANT", pairingTitle: "Link this NAS", pairingHint: "Already linked? No new code is needed. Generate one only to connect another Home Assistant installation.",
    pairButton: "Generate pairing code", working: "Generating...", pairError: "Could not generate a code. Check the agent and your DSM permissions.",
    codeLabel: "YOUR TEMPORARY CODE", codeExpiry: "Valid for 10 minutes. Existing connections stay linked.", copy: "Copy code", copied: "Copied", manualCopy: "Select and copy the code above.",
    next: "NEXT STEPS", stepsTitle: "Finish in Home Assistant", step1: "Install WakeLink from HACS in Home Assistant.", step2: "Open Settings > Devices & services and select this NAS when discovered.", step3: "Enter the six-digit code shown above.",
    footer: "Alexa setup is separate and uses Home Assistant."
  },
  es: {
    eyebrow: "TU NAS, A TU MANERA", title: "Conecta este NAS.",
    lead: "WakeLink funciona en tu red local. Sin suscripción, IP fija ni comandos de terminal.",
    statusTitle: "ESTADO DEL AGENTE", loading: "Comprobando WakeLink...", online: "Agente en marcha", offline: "Agente no disponible",
    login: "Inicia sesión en DSM con una cuenta administradora y vuelve a intentarlo.", refresh: "Actualizar",
    device: "DISPOSITIVO", address: "DIRECCIÓN LOCAL", unknown: "No detectada",
    pairingLabel: "HOME ASSISTANT", pairingTitle: "Vincula este NAS", pairingHint: "¿Ya está vinculado? No necesitas otro código. Genéralo solo para conectar otra instalación de Home Assistant.",
    pairButton: "Generar código de vinculación", working: "Generando...", pairError: "No se pudo generar el código. Comprueba el agente y tus permisos en DSM.",
    codeLabel: "TU CÓDIGO TEMPORAL", codeExpiry: "Válido durante 10 minutos. Las conexiones anteriores siguen vinculadas.", copy: "Copiar código", copied: "Copiado", manualCopy: "Selecciona y copia el código de arriba.",
    next: "SIGUIENTES PASOS", stepsTitle: "Termina en Home Assistant", step1: "Instala WakeLink desde HACS en Home Assistant.", step2: "Abre Ajustes > Dispositivos y servicios y selecciona este NAS cuando aparezca.", step3: "Introduce el código de seis cifras mostrado arriba.",
    footer: "Alexa se configura aparte a través de Home Assistant."
  }
};

const $ = (id) => document.getElementById(id);
let language = navigator.language.toLowerCase().startsWith("es") ? "es" : "en";
let status = "loading";
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
}

function setStatus(next) {
  status = next;
  $("status-line").className = "status-line " + next;
  $("status-line").textContent = words[language][next];
  $("pair").disabled = next !== "online";
  $("network").hidden = next !== "online";
}

async function loadStatus() {
  setStatus("loading");
  try {
    const response = await fetch("setup.cgi?action=status", { credentials: "same-origin", cache: "no-store" });
    if (response.status === 403) { setStatus("login"); return; }
    if (!response.ok) throw new Error("Agent unavailable");
    const info = await response.json();
    if (!info.online) throw new Error("Agent unavailable");
    $("hostname").textContent = info.hostname || words[language].unknown;
    $("address").textContent = info.ip_address || words[language].unknown;
    $("mac").textContent = info.mac_address || words[language].unknown;
    setStatus("online");
  } catch (_) {
    setStatus("offline");
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
      headers: { "X-WakeLink-Action": "pair" }
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
$("copy").addEventListener("click", copyCode);
translate();
loadStatus();
