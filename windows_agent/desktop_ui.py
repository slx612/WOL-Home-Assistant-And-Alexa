"""WakeLink desktop: guided first run, daily status and explicit configuration."""
from __future__ import annotations

import ctypes
import ipaddress
import queue
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

import setup_wizard_gui as setup
from ui_preferences import load_language, save_language

BG, PAPER, INK, MUTED, ACCENT, LINE = "#f2f3ee", "#ffffff", "#183b3a", "#5f706d", "#147d69", "#dce4dc"
LANGUAGES = {"en": "English", "es": "Espa\u00f1ol"}
TEXT = {
    "tagline": ("Your PC. On your terms.", "Tu PC. A tu manera."),
    "home": ("Overview", "Inicio"), "setup": ("Get started", "Primeros pasos"),
    "pairing": ("Home Assistant", "Home Assistant"), "settings": ("Settings", "Ajustes"),
    "updates": ("Updates", "Actualizaciones"), "language": ("Language", "Idioma"),
    "local": ("LOCAL CONTROL / NO SUBSCRIPTION", "CONTROL LOCAL / SIN SUSCRIPCIONES"),
    "home_title": ("Ready when you are.", "A punto cuando lo necesites."),
    "home_desc": ("Check your PC and decide when remote power commands are allowed.", "Comprueba tu PC y decide cu\u00e1ndo permitir las \u00f3rdenes de apagado remoto."),
    "agent": ("PC CONNECTION", "CONEXI\u00d3N CON EL PC"),
    "checking": ("Checking...", "Comprobando..."), "ready": ("Agent is running", "El agente est\u00e1 activo"),
    "offline": ("Agent unavailable", "Agente no disponible"), "not_set": ("Setup needed", "Falta configurar"),
    "agent_note": ("This checks the local agent, not Alexa or Wake-on-LAN hardware.", "Esto comprueba el agente local, no Alexa ni el encendido f\u00edsico por Wake-on-LAN."),
    "refresh": ("Check connection", "Comprobar conexi\u00f3n"),
    "guard": ("SHUTDOWN PROTECTION", "PROTECCI\u00d3N CONTRA APAGADOS"),
    "guard_on": ("Protected from remote shutdowns", "Protegido frente a apagados remotos"),
    "guard_off": ("Remote power commands allowed", "\u00d3rdenes de energ\u00eda permitidas"),
    "guard_unknown": ("Check the agent to see protection status", "Comprueba el agente para ver la protecci\u00f3n"),
    "guard_until": ("Protected until {time}", "Protegido hasta las {time}"),
    "guard_note": ("Blocks shutdown and restart from Home Assistant. It does not turn this PC off.", "Bloquea apagados y reinicios desde Home Assistant. No apaga este PC."),
    "hour": ("Protect for 1 hour", "Proteger durante 1 hora"),
    "protect": ("Protect until I allow", "Proteger hasta que yo lo permita"),
    "allow": ("Allow commands", "Permitir \u00f3rdenes"),
    "setup_title": ("Let's connect your PC.", "Vamos a conectar tu PC."),
    "setup_desc": ("WakeLink is installed. One more step enables local control and automatic startup.", "WakeLink ya est\u00e1 instalado. Un paso m\u00e1s activa el control local y el inicio autom\u00e1tico."),
    "step_one": ("01   Enable this PC", "01   Activar este PC"),
    "step_one_note": ("Detect the network, allow local traffic and start the agent with Windows. No fixed IP needed.", "Detectar la red, permitir tr\u00e1fico local e iniciar el agente con Windows. Sin IP fija."),
    "step_two": ("02   Link Home Assistant", "02   Vincular Home Assistant"),
    "step_two_note": ("Use the temporary code on the next screen. Home Assistant must be on the same local network.", "Usa el c\u00f3digo temporal de la siguiente pantalla. Home Assistant debe estar en la misma red local."),
    "enable": ("Enable and continue", "Activar y continuar"),
    "working": ("Working... Please keep this window open.", "Preparando... Mant\u00e9n esta ventana abierta."),
    "pair_title": ("A code. A connection.", "Un c\u00f3digo. Una conexi\u00f3n."),
    "pair_desc": ("Existing pairings are kept. Generate a code only for a new connection.", "Se conservan las vinculaciones existentes. Genera un c\u00f3digo solo para una conexi\u00f3n nueva."),
    "pair_label": ("TEMPORARY PAIRING CODE", "C\u00d3DIGO TEMPORAL DE VINCULACI\u00d3N"),
    "no_code": ("No code generated in this window", "No se ha generado un c\u00f3digo en esta ventana"),
    "expires": ("Expires in {minutes}:{seconds:02d}", "Caduca en {minutes}:{seconds:02d}"),
    "expired": ("Code expired or already used. Generate a new one if needed.", "C\u00f3digo caducado o utilizado. Genera otro si lo necesitas."),
    "new_code": ("Generate a code", "Generar un c\u00f3digo"), "copy": ("Copy code", "Copiar c\u00f3digo"),
    "copied": ("Pairing code copied", "C\u00f3digo copiado"),
    "pair_steps": ("1. In Home Assistant, install PC Power Free from HACS.\n2. Open Settings > Devices & services and select the discovered PC.\n3. Enter this six-digit code within 10 minutes.", "1. En Home Assistant, instala PC Power Free desde HACS.\n2. Abre Ajustes > Dispositivos y servicios y selecciona el PC descubierto.\n3. Introduce estos seis d\u00edgitos antes de 10 minutos."),
    "open_ha": ("Open Home Assistant", "Abrir Home Assistant"),
    "ha_address": ("Uses homeassistant.local. If it does not open, use your usual Home Assistant address.", "Usa homeassistant.local. Si no abre, entra con tu direcci\u00f3n habitual de Home Assistant."),
    "matter": ("Alexa setup is separate and still experimental. This code is for Home Assistant, not Matter.", "La configuraci\u00f3n de Alexa es independiente y sigue en pruebas. Este c\u00f3digo es para Home Assistant, no para Matter."),
    "certificate": ("PC certificate fingerprint (SHA-256)", "Huella del certificado del PC (SHA-256)"),
    "certificate_unavailable": ("Certificate inaccessible. Open Settings > Repair local setup.", "No se puede leer el certificado. Abre Ajustes > Reparar configuraci\u00f3n local."),
    "settings_title": ("Simple by default.", "Sencillo por defecto."),
    "settings_desc": ("Network details are detected automatically. Change advanced options only when needed.", "La red se detecta autom\u00e1ticamente. Cambia las opciones avanzadas solo si lo necesitas."),
    "network": ("NETWORK DETAILS", "DATOS DE RED"), "network_wait": ("Detecting the active connection...", "Detectando la conexi\u00f3n activa..."),
    "advanced": ("Advanced connection settings", "Ajustes avanzados de conexi\u00f3n"),
    "port": ("Agent port", "Puerto del agente"), "networks": ("Allowed networks (comma separated)", "Redes permitidas (separadas por comas)"),
    "force": ("Force applications to close (may lose unsaved work)", "Forzar el cierre de aplicaciones (puede perder trabajo sin guardar)"),
    "save": ("Apply connection settings", "Aplicar ajustes de conexi\u00f3n"),
    "unlock": ("Unlock system settings", "Desbloquear ajustes del sistema"),
    "repair": ("Repair local setup", "Reparar configuraci\u00f3n local"),
    "repair_confirm": ("This enables automatic startup, repairs local firewall access and starts the agent. Your pairing is kept. Continue?", "Esto activa el inicio autom\u00e1tico, repara el acceso local del firewall y arranca el agente. Se conserva la vinculaci\u00f3n. \u00bfContinuar?"),
    "saved": ("Settings applied. Existing pairing kept.", "Ajustes aplicados. Vinculaci\u00f3n conservada."),
    "admin": ("Windows will ask for administrator permission to change agent settings. Then repeat the action in the new window.", "Windows pedir\u00e1 permiso de administrador para cambiar el agente. Despu\u00e9s repite la acci\u00f3n en la nueva ventana."),
    "save_confirm": ("This changes network access and briefly restarts the agent. Apply these settings?", "Esto cambia el acceso de red y reinicia brevemente el agente. \u00bfAplicar estos ajustes?"),
    "force_confirm": ("Forced shutdown can discard unsaved work. Enable it?", "El apagado forzado puede perder trabajo sin guardar. \u00bfActivarlo?"),
    "updates_title": ("Keep the connection fresh.", "Mant\u00e9n todo al d\u00eda."),
    "updates_desc": ("Check for a Windows installer. Updates keep your settings and pairing; do not uninstall first.", "Busca un instalador para Windows. Actualizar conserva ajustes y vinculaci\u00f3n; no desinstales antes."),
    "installed": ("INSTALLED DESKTOP VERSION", "VERSI\u00d3N DEL PROGRAMA INSTALADA"),
    "check_updates": ("Check for updates", "Buscar actualizaciones"),
    "update_idle": ("Ready to check GitHub releases, including betas.", "Listo para consultar las versiones de GitHub, incluidas las betas."),
    "latest": ("No newer Windows release found. Latest published: {version}", "No hay una versi\u00f3n m\u00e1s nueva para Windows. \u00daltima publicada: {version}"),
    "available": ("Windows update available: {version}", "Actualizaci\u00f3n para Windows disponible: {version}"),
    "download": ("Download Windows installer", "Descargar instalador para Windows"),
    "unsigned": ("Preview build, not digitally signed. Windows may show a security warning. Do not disable antivirus protection.", "Versi\u00f3n de prueba sin firma digital. Windows puede mostrar un aviso de seguridad. No desactives el antivirus."),
    "error": ("Could not complete this step", "No se pudo completar este paso"),
    "details": ("Details", "Detalles"), "invalid_port": ("Enter a port between 1 and 65535.", "Introduce un puerto entre 1 y 65535."),
    "invalid_network": ("Enter at least one allowed local network.", "Introduce al menos una red local permitida."),
    "not_ready": ("Complete the first-run setup before using this action.", "Completa la configuraci\u00f3n inicial antes de usar esta acci\u00f3n."),
    "close_busy": ("Please wait until the current operation finishes.", "Espera a que termine la operaci\u00f3n actual."),
}


class WakeLinkApplication:
    def __init__(self, root: tk.Tk, *, initial_language: str = "", initial_page: str | None = None):
        self.root = root
        self.agent_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
        self.data_dir = setup.resolve_data_dir(self.agent_dir)
        self.config_path = self.data_dir / "config.json"
        self.config = setup.load_existing_config(self.config_path)
        self.can_edit_settings = setup.is_admin()
        self.language_code = initial_language if initial_language in LANGUAGES else load_language()
        if initial_language in LANGUAGES:
            save_language(initial_language)
        self.language_var = tk.StringVar(value=LANGUAGES[self.language_code])
        self.port_var = tk.StringVar(value=str(self.config.get("port", setup.DEFAULT_AGENT_PORT)))
        self.networks_var = tk.StringVar(value=", ".join(self.config.get("allowed_subnets", [])))
        self.force_var = tk.BooleanVar(value=bool(self.config.get("shutdown_force", False)))
        self.pairing_code_var = tk.StringVar(value="------")
        self.status_var = tk.StringVar()
        self.network_var = tk.StringVar(value=self.t("network_wait"))
        self.agent_status_var = tk.StringVar(value=self.t("checking") if self.config else self.t("not_set"))
        self.guard_status_var = tk.StringVar(value=self.t("guard_unknown"))
        self.update_var = tk.StringVar(value=self.t("update_idle"))
        self.code_note_var = tk.StringVar(value=self.t("no_code"))
        self.fingerprint_var = tk.StringVar(value="-")
        if (self.data_dir / "agent-cert.pem").exists():
            try:
                self.fingerprint_var.set(setup.certificate_fingerprint(self.data_dir))
            except OSError:
                self.fingerprint_var.set(self.t("certificate_unavailable"))
        self.online = None
        self.guard_status = None
        self.adapter = None
        self.download_url = None
        self.code_deadline = 0.0
        self.next_status_poll = time.monotonic() + 10
        self.jobs = set()
        self.results = queue.Queue()
        self.text_widgets = []
        self.guard_buttons = []
        self.current_page = "home" if self.config else "setup"
        self._configure_style()
        self._build_ui()
        self.show_page(initial_page or self.current_page)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.after(80, self._drain_results)
        self.root.after(500, self._tick)
        self._run_job("network", setup.detect_primary_adapter, self._network_detected)
        if self.config:
            self.refresh_status()

    def t(self, key, **values):
        return TEXT[key][1 if self.language_code == "es" else 0].format(**values)

    def _configure_style(self):
        self.root.title(f"WakeLink  |  {setup.APP_VERSION}")
        self.root.configure(bg=BG)
        self.root.geometry("960x740")
        self.root.minsize(740, 560)
        self.root.resizable(True, True)
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=PAPER)
        style.configure("TLabel", background=PAPER, foreground=INK, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", foreground=MUTED)
        style.configure("Eyebrow.TLabel", foreground=ACCENT, font=("Bahnschrift", 10))
        style.configure("Title.TLabel", font=("Bahnschrift", 25), background=BG)
        style.configure("PageNote.TLabel", foreground=MUTED, background=BG)
        style.configure("Metric.TLabel", font=("Bahnschrift", 19))
        style.configure("Code.TLabel", font=("Consolas", 38, "bold"), foreground=ACCENT)
        style.configure("TButton", padding=(14, 9), background=PAPER, foreground=INK, borderwidth=1, font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#e4eee8")], foreground=[("disabled", "#7b8783")])
        style.configure("Primary.TButton", background=ACCENT, foreground="white", borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#106454"), ("disabled", "#b7c6bc")], foreground=[("disabled", "#3d554c")])
        style.configure("Nav.TButton", padding=(14, 10), anchor="w", borderwidth=0, background=INK, foreground="#e3ede5")
        style.map("Nav.TButton", background=[("active", "#29514c")])
        style.configure("Selected.Nav.TButton", background="#31685c", foreground="white")
        style.configure("TCheckbutton", background=PAPER, foreground=INK, padding=6)
        style.configure("TEntry", padding=7, fieldbackground=PAPER)
        icon_path = (Path(sys._MEIPASS) if getattr(sys, "frozen", False) else self.agent_dir) / "assets/wakelink.ico"
        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))

    def _label(self, parent, key, style="TLabel", **kwargs):
        widget = ttk.Label(parent, text=self.t(key), style=style, **kwargs)
        self.text_widgets.append((widget, key))
        return widget

    def _button(self, parent, key, command, primary=False):
        widget = ttk.Button(parent, text=self.t(key), command=command, style="Primary.TButton" if primary else "TButton")
        self.text_widgets.append((widget, key))
        return widget

    def _build_ui(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        rail = tk.Frame(self.root, bg=INK, width=186, padx=18, pady=28)
        rail.grid(row=0, column=0, sticky="nsew")
        rail.grid_propagate(False)
        rail.columnconfigure(0, weight=1)
        tk.Label(rail, text="WakeLink", font=("Bahnschrift", 23), fg="white", bg=INK, anchor="w").grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.rail_note = tk.Label(rail, text=self.t("tagline"), font=("Segoe UI", 9), fg="#adcbc1", bg=INK, anchor="w", wraplength=148, justify="left")
        self.rail_note.grid(row=1, column=0, sticky="ew", pady=(0, 32))
        self.nav = {}
        for row, key in enumerate(("home", "pairing", "settings", "updates"), 2):
            button = ttk.Button(rail, text=self.t(key), style="Nav.TButton", command=lambda page=key: self.show_page(page))
            button.grid(row=row, column=0, sticky="ew", pady=3)
            self.text_widgets.append((button, key))
            self.nav[key] = button
        rail.rowconfigure(6, weight=1)
        self.language_caption = tk.Label(rail, text=self.t("language"), fg="#adcbc1", bg=INK, anchor="w")
        self.language_caption.grid(row=7, column=0, sticky="ew", pady=(0, 6))
        combo = ttk.Combobox(rail, textvariable=self.language_var, state="readonly", values=list(LANGUAGES.values()), width=13)
        combo.grid(row=8, column=0, sticky="ew")
        combo.bind("<<ComboboxSelected>>", self._on_language_changed)
        tk.Label(rail, text=setup.APP_VERSION, font=("Consolas", 9), fg="#adcbc1", bg=INK, anchor="w").grid(row=9, column=0, sticky="ew", pady=(16, 0))

        container = ttk.Frame(self.root)
        container.grid(row=0, column=1, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.body = ttk.Frame(self.canvas, padding=(30, 24))
        self.body_window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.columnconfigure(0, weight=1)
        self.body.bind("<Configure>", lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._resize)
        self.root.bind("<MouseWheel>", lambda event: self.canvas.yview_scroll(-int(event.delta / 120), "units"))
        self.pages = {}
        for key in ("setup", "home", "pairing", "settings", "updates"):
            page = ttk.Frame(self.body)
            page.columnconfigure(0, weight=1)
            self.pages[key] = page
        self._build_setup()
        self._build_home()
        self._build_pairing()
        self._build_settings()
        self._build_updates()
        ttk.Label(container, textvariable=self.status_var, style="PageNote.TLabel", padding=(22, 12), wraplength=560).grid(row=1, column=0, columnspan=2, sticky="ew")

    def _heading(self, page, key):
        self._label(page, "local", "PageNote.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 14))
        self._label(page, key + "_title", "Title.TLabel", wraplength=620).grid(row=1, column=0, sticky="ew")
        self._label(page, key + "_desc", "PageNote.TLabel", wraplength=620, justify="left").grid(row=2, column=0, sticky="ew", pady=(10, 24))

    def _card(self, page, row):
        card = ttk.Frame(page, style="Card.TFrame", padding=22)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        card.columnconfigure(0, weight=1)
        return card

    def _build_setup(self):
        page = self.pages["setup"]
        self._heading(page, "setup")
        card = self._card(page, 3)
        for row, key in enumerate(("step_one", "step_one_note", "step_two", "step_two_note")):
            self._label(card, key, "Metric.TLabel" if row % 2 == 0 else "Muted.TLabel", wraplength=580, justify="left").grid(row=row, column=0, sticky="ew", pady=(0, 14))
        self.enable_button = self._button(card, "enable", self.enable_pc, True)
        self.enable_button.grid(row=4, column=0, sticky="w", pady=(10, 0))

    def _build_home(self):
        page = self.pages["home"]
        self._heading(page, "home")
        card = self._card(page, 3)
        self._label(card, "agent", "Eyebrow.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, textvariable=self.agent_status_var, style="Metric.TLabel", wraplength=580).grid(row=1, column=0, sticky="ew", pady=(8, 4))
        ttk.Label(card, text=socket.gethostname(), style="Muted.TLabel").grid(row=2, column=0, sticky="w")
        self._label(card, "agent_note", "Muted.TLabel", wraplength=580).grid(row=3, column=0, sticky="ew", pady=(12, 14))
        self._button(card, "refresh", self.refresh_status).grid(row=4, column=0, sticky="w")
        card = self._card(page, 4)
        self._label(card, "guard", "Eyebrow.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, textvariable=self.guard_status_var, style="Metric.TLabel", wraplength=580).grid(row=1, column=0, sticky="ew", pady=(8, 12))
        self._label(card, "guard_note", "Muted.TLabel", wraplength=580).grid(row=2, column=0, sticky="ew", pady=(0, 12))
        for row, (key, payload) in enumerate((("hour", {"mode": "ignore_until", "duration_minutes": 60}), ("protect", {"mode": "ignore_manual"}), ("allow", {"mode": "allow"})), 3):
            button = self._button(card, key, lambda data=payload: self.set_guard(data), key == "hour")
            button.grid(row=row, column=0, sticky="ew", pady=3)
            button.state(["disabled"])
            self.guard_buttons.append(button)

    def _build_pairing(self):
        page = self.pages["pairing"]
        self._heading(page, "pair")
        card = self._card(page, 3)
        self._label(card, "pair_label", "Eyebrow.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, textvariable=self.pairing_code_var, style="Code.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Label(card, textvariable=self.code_note_var, style="Muted.TLabel", wraplength=580).grid(row=2, column=0, sticky="ew", pady=(0, 16))
        self.pair_button = self._button(card, "new_code", self.generate_code, True)
        self.pair_button.grid(row=3, column=0, sticky="w")
        self.copy_button = self._button(card, "copy", self.copy_code)
        self.copy_button.grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.copy_button.state(["disabled"])
        card = self._card(page, 4)
        self._label(card, "pair_steps", wraplength=580, justify="left").grid(row=0, column=0, sticky="ew", pady=(0, 18))
        self._button(card, "open_ha", lambda: webbrowser.open("http://homeassistant.local:8123/config/integrations")).grid(row=1, column=0, sticky="w")
        self._label(card, "ha_address", "Muted.TLabel", wraplength=580).grid(row=2, column=0, sticky="ew", pady=(10, 14))
        self._label(card, "matter", "Muted.TLabel", wraplength=580).grid(row=3, column=0, sticky="ew")
        self._label(card, "certificate", "Muted.TLabel", wraplength=580).grid(row=4, column=0, sticky="ew", pady=(16, 4))
        ttk.Label(card, textvariable=self.fingerprint_var, font=("Consolas", 9), wraplength=580).grid(row=5, column=0, sticky="ew")

    def _build_settings(self):
        page = self.pages["settings"]
        self._heading(page, "settings")
        card = self._card(page, 3)
        self._label(card, "network", "Eyebrow.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, textvariable=self.network_var, wraplength=580, justify="left").grid(row=1, column=0, sticky="ew", pady=(12, 0))
        card = self._card(page, 4)
        self._label(card, "advanced", "Metric.TLabel", wraplength=580).grid(row=0, column=0, sticky="ew", pady=(0, 18))
        self._label(card, "port").grid(row=1, column=0, sticky="w")
        self.port_entry = ttk.Entry(card, textvariable=self.port_var, width=10,
            state="normal" if self.can_edit_settings else "readonly")
        self.port_entry.grid(row=2, column=0, sticky="w", pady=(5, 14))
        self._label(card, "networks").grid(row=3, column=0, sticky="w")
        self.networks_entry = ttk.Entry(card, textvariable=self.networks_var,
            state="normal" if self.can_edit_settings else "readonly")
        self.networks_entry.grid(row=4, column=0, sticky="ew", pady=(5, 14))
        check = tk.Checkbutton(card, text=self.t("force"), variable=self.force_var,
            bg=PAPER, fg=INK, activebackground=PAPER, font=("Segoe UI", 10),
            wraplength=550, anchor="w", justify="left", state="normal" if self.can_edit_settings else "disabled")
        check.grid(row=5, column=0, sticky="ew", pady=(0, 18))
        self.text_widgets.append((check, "force"))
        self.save_button = self._button(card, "save", self.save_settings, True)
        self.save_button.grid(row=6, column=0, sticky="w")
        self.unlock_button = self._button(card, "unlock", lambda: self._require_admin("settings"))
        if not self.can_edit_settings:
            self.save_button.state(["disabled"])
            self.unlock_button.grid(row=7, column=0, sticky="w", pady=(12, 0))
        self.repair_button = self._button(card, "repair", self.repair_setup)
        self.repair_button.grid(row=8, column=0, sticky="w", pady=(12, 0))

    def _build_updates(self):
        page = self.pages["updates"]
        self._heading(page, "updates")
        card = self._card(page, 3)
        self._label(card, "installed", "Eyebrow.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, text=setup.APP_VERSION, style="Metric.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 18))
        self.update_button = self._button(card, "check_updates", self.check_updates, True)
        self.update_button.grid(row=2, column=0, sticky="w")
        ttk.Label(card, textvariable=self.update_var, wraplength=580, justify="left").grid(row=3, column=0, sticky="ew", pady=(18, 12))
        self.download_button = self._button(card, "download", self.download_update)
        self.download_button.grid(row=4, column=0, sticky="w")
        self.download_button.grid_remove()
        card = self._card(page, 4)
        self._label(card, "unsigned", "Muted.TLabel", wraplength=580, justify="left").grid(row=0, column=0, sticky="ew")

    def _resize(self, event):
        self.canvas.itemconfigure(self.body_window, width=event.width)
        width = max(220, event.width - 110)
        pending = list(self.pages.values())
        while pending:
            widget = pending.pop()
            pending.extend(widget.winfo_children())
            if isinstance(widget, (ttk.Label, tk.Checkbutton)) and widget.cget("wraplength"):
                widget.configure(wraplength=width - 26 if isinstance(widget, tk.Checkbutton) else width)

    def show_page(self, page):
        for frame in self.pages.values():
            frame.grid_remove()
        self.current_page = page
        self.pages[page].grid(row=0, column=0, sticky="nsew")
        for key, button in self.nav.items():
            button.configure(style="Selected.Nav.TButton" if key == page else "Nav.TButton")
        self.canvas.yview_moveto(0)

    def _on_language_changed(self, _event=None):
        self.language_code = next(code for code, label in LANGUAGES.items() if label == self.language_var.get())
        try:
            save_language(self.language_code)
        except OSError as err:
            messagebox.showerror("WakeLink", str(err), parent=self.root)
        for widget, key in self.text_widgets:
            widget.configure(text=self.t(key))
        self.rail_note.configure(text=self.t("tagline"))
        self.language_caption.configure(text=self.t("language"))
        self.status_var.set("")
        self.update_var.set(self.t("update_idle"))
        self._render_status()
        if not self.code_deadline:
            self.code_note_var.set(self.t("no_code"))

    def _run_job(self, name, work, done):
        if name in self.jobs:
            return
        self.jobs.add(name)
        self._busy_buttons()
        def worker():
            try:
                self.results.put((name, done, work(), None))
            except Exception as err:
                self.results.put((name, done, None, err))
        threading.Thread(target=worker, daemon=True).start()

    def _drain_results(self):
        while True:
            try:
                name, done, value, error = self.results.get_nowait()
            except queue.Empty:
                break
            self.jobs.discard(name)
            if error:
                if name == "status":
                    self.online = False
                    self.guard_status = None
                    self._render_status()
                    self.status_var.set(f"{self.t('offline')}: {error}")
                elif name == "network":
                    self.network_var.set(str(error))
                elif name == "updates":
                    self.update_var.set(f"{self.t('error')}: {setup.format_update_error(error)}")
                else:
                    self.status_var.set(self.t("error"))
                    messagebox.showerror("WakeLink", f"{self.t('error')}\n\n{error}", parent=self.root)
            else:
                done(value)
            self._busy_buttons()
        self.root.after(80, self._drain_results)

    def _busy_buttons(self):
        for button in (self.enable_button, self.save_button, self.pair_button, self.repair_button):
            button.state(["disabled"] if self.jobs.intersection({"configure", "pairing"}) else ["!disabled"])
        if not self.can_edit_settings:
            self.save_button.state(["disabled"])
        self.update_button.state(["disabled"] if "updates" in self.jobs else ["!disabled"])
        for button in self.guard_buttons:
            button.state(["!disabled"] if self.online and not self.jobs.intersection({"guard", "configure"}) else ["disabled"])

    def _network_detected(self, adapter):
        self.adapter = adapter
        self.network_var.set(f"{adapter.hostname}\n{adapter.interface_alias}  /  {adapter.ipv4_address}\nMAC  {adapter.mac_address}")
        if not self.config and not self.networks_var.get():
            self.networks_var.set(f"{adapter.subnet_cidr}, 127.0.0.1/32")

    def _local_request(self, method="GET", path="/v1/status", payload=None):
        from pc_power_tray import build_local_api_request, load_runtime_config
        config = load_runtime_config(self.config_path)
        return build_local_api_request(config=config, method=method, path=path, payload=payload, timeout=3)

    def refresh_status(self):
        if not self.config_path.exists():
            self.show_page("setup")
            return
        self.agent_status_var.set(self.t("checking"))
        self._run_job("status", self._local_request, self._status_received)

    def _status_received(self, status):
        self.online = status.get("online") is True
        self.guard_status = status
        self.status_var.set("")
        self._render_status()

    def _render_status(self):
        self.agent_status_var.set(self.t("ready" if self.online else "offline" if self.online is False else "checking" if self.config else "not_set"))
        status = self.guard_status
        if not status or not self.online:
            self.guard_status_var.set(self.t("guard_unknown"))
        elif not status.get("command_guard_active"):
            self.guard_status_var.set(self.t("guard_off"))
        elif status.get("command_guard_until_ts"):
            self.guard_status_var.set(self.t("guard_until", time=time.strftime("%H:%M", time.localtime(status["command_guard_until_ts"]))))
        else:
            self.guard_status_var.set(self.t("guard_on"))

    def set_guard(self, payload):
        self._run_job("guard", lambda: self._local_request("POST", "/v1/local/guard", payload), lambda _value: self.refresh_status())

    def _require_admin(self, page):
        if setup.is_admin():
            return True
        messagebox.showinfo("WakeLink", self.t("admin"), parent=self.root)
        arguments = ["--page", page, "--lang", self.language_code]
        if not getattr(sys, "frozen", False):
            arguments.insert(0, str(self.agent_dir / "setup_wizard_gui.py"))
        launch = ctypes.windll.shell32.ShellExecuteW
        launch.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int]
        launch.restype = ctypes.c_void_p
        result = launch(None, "runas", sys.executable, subprocess.list2cmdline(arguments), str(self.agent_dir), 1)
        if not result or result <= 32:
            self.status_var.set(self.t("error"))
        else:
            self.root.destroy()
        return False

    def enable_pc(self):
        if self.config_path.exists():
            self.show_page("home")
            return
        if not self._require_admin("setup"):
            return
        self.status_var.set(self.t("working"))
        self._run_job("configure", self._initial_setup, self._setup_done)

    def _initial_setup(self):
        adapter = setup.detect_primary_adapter()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # Recheck at the write boundary: another window must not replace a pairing.
        if self.config_path.exists():
            raise ValueError("Configuration already exists. Reopen WakeLink; do not uninstall.")
        code = setup.generate_pairing_code()
        setup.write_config(self.config_path, port=setup.DEFAULT_AGENT_PORT, token=setup.generate_token(),
            allowed_subnets=[adapter.subnet_cidr, "127.0.0.1/32"], force=False,
            machine_id=setup.uuid.uuid4().hex, pairing_code_hash=setup.hash_pairing_code(code),
            pairing_code_expires_at=time.time() + setup.PAIRING_CODE_TTL_SECONDS)
        setup.create_server_context(self.data_dir)
        self._install_runtime(setup.DEFAULT_AGENT_PORT, [adapter.subnet_cidr], first_run=True)
        return code

    def _install_runtime(self, port, addresses, *, first_run=False):
        command, prefix = setup.resolve_agent_command(self.agent_dir)
        setup.configure_firewall(setup.DEFAULT_RULE_NAME, port=port, remote_addresses=addresses)
        if first_run:
            setup.install_startup_task(setup.DEFAULT_TASK_NAME, command_exe=command, command_prefix=prefix, config_path=self.config_path)
            setup.wait_for_agent(self.config_path)
            tray, tray_prefix = setup.resolve_tray_command(self.agent_dir)
            setup.configure_tray_startup(enabled=True, command_exe=tray, command_prefix=tray_prefix, config_path=self.config_path)
            setup.start_tray_application(tray, tray_prefix, self.config_path)
        else:
            setup.upgrade_existing_installation(self.agent_dir, self.config_path)

    def _setup_done(self, code):
        self.config = setup.load_existing_config(self.config_path)
        self.port_var.set(str(self.config["port"]))
        self.networks_var.set(", ".join(self.config["allowed_subnets"]))
        self.fingerprint_var.set(setup.certificate_fingerprint(self.data_dir))
        self.status_var.set("")
        self._code_ready(code)
        self.show_page("pairing")
        self.refresh_status()

    def generate_code(self):
        if not self.config_path.exists():
            self.show_page("setup")
            return
        if self._require_admin("pairing"):
            self._run_job("pairing", lambda: setup.activate_pairing_code(self.config_path), self._code_ready)

    def _code_ready(self, code):
        self.pairing_code_var.set(code)
        self.code_deadline = float(setup.load_existing_config(self.config_path)["pairing_code_expires_at"])
        self.copy_button.state(["!disabled"])

    def _tick(self):
        if self.config_path.exists() and time.monotonic() >= self.next_status_poll:
            self.next_status_poll = time.monotonic() + 10
            if not self.jobs.intersection({"configure", "pairing", "guard"}):
                self.refresh_status()
        if self.code_deadline:
            remaining = max(0, int(self.code_deadline - time.time()))
            try:
                config = setup.load_existing_config(self.config_path)
                active = config.get("pairing_code_hash") == setup.hash_pairing_code(self.pairing_code_var.get())
            except ValueError:
                active = False
            if remaining and active:
                self.code_note_var.set(self.t("expires", minutes=remaining // 60, seconds=remaining % 60))
            else:
                self.code_deadline = 0
                self.pairing_code_var.set("------")
                self.copy_button.state(["disabled"])
                self.code_note_var.set(self.t("expired"))
        self.root.after(1000, self._tick)

    def copy_code(self):
        if self.code_deadline <= time.time():
            return
        config = setup.load_existing_config(self.config_path)
        if config.get("pairing_code_hash") != setup.hash_pairing_code(self.pairing_code_var.get()):
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.pairing_code_var.get())
        self.status_var.set(self.t("copied"))

    def save_settings(self):
        if not self.config_path.exists():
            self.show_page("setup")
            return
        if not self._require_admin("settings"):
            return
        try:
            port = int(self.port_var.get())
            if not 1 <= port <= 65535:
                raise ValueError(self.t("invalid_port"))
            networks = [str(ipaddress.ip_network(value.strip(), strict=False)) for value in self.networks_var.get().split(",") if value.strip()]
            if not networks:
                raise ValueError(self.t("invalid_network"))
            if "127.0.0.1/32" not in networks:
                networks.append("127.0.0.1/32")
            force = self.force_var.get()
        except ValueError as err:
            messagebox.showerror("WakeLink", str(err), parent=self.root)
            return
        if force and not self.config.get("shutdown_force") and not messagebox.askyesno("WakeLink", self.t("force_confirm"), parent=self.root):
            return
        if not messagebox.askyesno("WakeLink", self.t("save_confirm"), parent=self.root):
            return
        self.status_var.set(self.t("working"))
        def save():
            config = setup.load_existing_config(self.config_path)
            setup.run_task_script(setup.DEFAULT_TASK_NAME, "Stop")
            config.update(port=port, allowed_subnets=networks, shutdown_force=force)
            setup.atomic_write_json(self.config_path, config)
            self._install_runtime(port, networks)
            return config
        def done(config):
            self.config = config
            self.status_var.set(self.t("saved"))
            self.refresh_status()
        self._run_job("configure", save, done)

    def repair_setup(self):
        if not self.config_path.exists():
            self.show_page("setup")
            return
        if not self._require_admin("settings"):
            return
        if messagebox.askyesno("WakeLink", self.t("repair_confirm"), parent=self.root):
            self.status_var.set(self.t("working"))
            self._run_job("configure", self._repair_runtime, lambda _result: self.refresh_status())

    def _repair_runtime(self):
        config = setup.load_existing_config(self.config_path)
        setup.create_server_context(self.data_dir)
        self._install_runtime(int(config["port"]), config["allowed_subnets"], first_run=True)
        return config

    def check_updates(self):
        self.download_url = None
        self.download_button.grid_remove()
        self.update_var.set(self.t("checking"))
        self._run_job("updates", setup.fetch_latest_github_release, self._update_received)

    def _update_received(self, release):
        if setup.is_newer_version(release.version, setup.APP_VERSION):
            self.update_var.set(self.t("available", version=release.version))
            self.download_url = getattr(release, "installer_url", "") or release.html_url
            self.download_button.grid()
        else:
            self.update_var.set(self.t("latest", version=release.version))

    def download_update(self):
        if self.download_url:
            webbrowser.open(self.download_url)

    def _close(self):
        if self.jobs.intersection({"configure", "pairing"}):
            messagebox.showinfo("WakeLink", self.t("close_busy"), parent=self.root)
            return
        self.root.destroy()
