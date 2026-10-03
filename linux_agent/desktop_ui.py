"""Small Ubuntu setup window for the WakeLink background agent."""

from __future__ import annotations

import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser

from network_info import detect_primary_adapter
from agent_core.common import AGENT_VERSION
from agent_core.update_check import fetch_latest_github_release, format_update_error, is_newer_version


SERVICE = "pcpowerfree-agent.service"
HELPER = "/usr/lib/wakelink/setup-helper"
BG = "#f2f3ee"
PAPER = "#ffffff"
INK = "#183b3a"
MUTED = "#5f706d"
ACCENT = "#147d69"
TEXT = {
    "en": {
        "subtitle": "YOUR COMPUTER, ON YOUR TERMS",
        "title": "Connect this computer.",
        "description": "WakeLink runs locally. No subscription, fixed IP, or terminal commands.",
        "running": "Agent running",
        "stopped": "Setup needed",
        "network": "DETECTED NETWORK",
        "unknown": "Network not detected yet. Check the connection and try again.",
        "activate": "Enable WakeLink",
        "pair": "Generate pairing code",
        "working": "Working... approve the system prompt if one appears.",
        "code_label": "YOUR TEMPORARY CODE",
        "code_note": "Expires in 10 minutes. Existing connections stay linked.",
        "steps": "1. Install WakeLink in Home Assistant through HACS.\n2. Open Settings > Devices & services and select this computer.\n3. Enter the six-digit code above.",
        "ready_steps": "WakeLink is ready. Generate a code only when linking a new Home Assistant installation.",
        "copy": "Copy code",
        "open_ha": "Open Home Assistant",
        "error": "WakeLink could not complete setup",
        "cancelled": "Authorization was canceled or setup failed. Try again.",
        "wait": "Wait for the current operation to finish.",
        "footer": "Alexa setup is separate and uses Home Assistant.",
        "updates": "Version {version}",
        "check_updates": "Check for updates",
        "checking": "Checking official Ubuntu releases...",
        "current": "No newer Ubuntu installer is available.",
        "available": "Update available: {version}",
        "update_error": "Could not check updates: {error}",
        "install_update": "Install update",
        "confirm_update": "Download and install the official Ubuntu update? Ubuntu will ask for administrator authorization. Your Home Assistant connection stays linked.",
        "updated": "Update installed. Open WakeLink again to use the new version. No new pairing is needed.",
    },
    "es": {
        "subtitle": "TU ORDENADOR, A TU MANERA",
        "title": "Conecta este ordenador.",
        "description": "WakeLink funciona en tu red. Sin suscripción, IP fija ni comandos de terminal.",
        "running": "Agente en marcha",
        "stopped": "Falta configurar",
        "network": "RED DETECTADA",
        "unknown": "Todavía no se detecta la red. Comprueba la conexión e inténtalo de nuevo.",
        "activate": "Activar WakeLink",
        "pair": "Generar código de vinculación",
        "working": "Preparando... acepta el permiso del sistema si aparece.",
        "code_label": "TU CÓDIGO TEMPORAL",
        "code_note": "Caduca en 10 minutos. Las vinculaciones anteriores se conservan.",
        "steps": "1. Instala WakeLink en Home Assistant desde HACS.\n2. Abre Ajustes > Dispositivos y servicios y selecciona este ordenador.\n3. Introduce el código de seis cifras de arriba.",
        "ready_steps": "WakeLink está listo. Genera un código solo si vas a vincular otra instalación de Home Assistant.",
        "copy": "Copiar código",
        "open_ha": "Abrir Home Assistant",
        "error": "No se pudo configurar WakeLink",
        "cancelled": "Se canceló el permiso o falló la configuración. Inténtalo de nuevo.",
        "wait": "Espera a que termine la operación actual.",
        "footer": "Alexa se configura aparte a través de Home Assistant.",
        "updates": "Versión {version}",
        "check_updates": "Buscar actualizaciones",
        "checking": "Buscando publicaciones oficiales para Ubuntu...",
        "current": "No hay un instalador Ubuntu más nuevo disponible.",
        "available": "Actualización disponible: {version}",
        "update_error": "No se pudieron comprobar las actualizaciones: {error}",
        "install_update": "Instalar actualización",
        "confirm_update": "¿Descargar e instalar la actualización oficial para Ubuntu? Ubuntu pedirá autorización de administrador. La vinculación con Home Assistant se conserva.",
        "updated": "Actualización instalada. Abre WakeLink de nuevo para usar la nueva versión. No necesitas volver a vincular.",
    },
}


def parse_pairing_code(output: str) -> str | None:
    match = re.search(r"(?m)^Pairing code: ([0-9]{6})$", output)
    return match.group(1) if match else None


def agent_running() -> bool:
    try:
        return subprocess.run(
            ["/usr/bin/systemctl", "is-active", "--quiet", SERVICE],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ).returncode == 0
    except OSError:
        return False


class WakeLinkWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.language = "es" if os.environ.get("LANG", "").lower().startswith("es") else "en"
        self.code: str | None = None
        self.busy = False
        self.checking_updates = False
        self.latest_release = None
        self.update_state = "checking"
        self.update_error = ""
        self.results: queue.Queue[tuple[str, object]] = queue.Queue()
        self.root.title("WakeLink")
        available_height = max(500, self.root.winfo_screenheight() - 100)
        self.root.geometry(f"760x{min(760, available_height)}")
        self.root.minsize(620, min(650, available_height))
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.icon = None
        icon_path = Path("/usr/share/icons/hicolor/256x256/apps/wakelink.png")
        if icon_path.exists():
            self.icon = tk.PhotoImage(file=str(icon_path))
            self.root.iconphoto(True, self.icon)
        self.draw()
        self.root.after(100, self.poll)
        self.root.after(500, self.check_updates)

    def t(self, key: str) -> str:
        return TEXT[self.language][key]

    def close(self) -> None:
        if self.busy:
            messagebox.showinfo("WakeLink", self.t("wait"))
            return
        self.root.destroy()

    def set_language(self, language: str) -> None:
        self.language = language
        self.draw()

    def network_summary(self) -> str:
        try:
            adapter = detect_primary_adapter()
            return f"{adapter.hostname}  /  {adapter.ipv4_address}  /  {adapter.mac_address}"
        except (OSError, ValueError, RuntimeError):
            return self.t("unknown")

    def draw(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()

        header = tk.Frame(self.root, bg=INK, padx=36, pady=26)
        header.pack(fill="x")
        tk.Label(header, text="WakeLink", font=("DejaVu Sans", 23, "bold"), fg=PAPER, bg=INK).pack(side="left")
        for language, label in (("es", "ES"), ("en", "EN")):
            tk.Button(header, text=label, command=lambda value=language: self.set_language(value),
                      font=("DejaVu Sans", 10, "bold"), fg=PAPER if language == self.language else "#aecbc4",
                      bg=INK, activebackground=INK, activeforeground=PAPER, relief="flat", bd=0,
                      cursor="hand2", padx=9).pack(side="right")

        updates = tk.Frame(self.root, bg=PAPER, padx=36, pady=10)
        updates.pack(fill="x")
        tk.Label(updates, text=self.t("updates").format(version=AGENT_VERSION),
                 font=("DejaVu Sans", 10, "bold"), fg=INK, bg=PAPER).pack(anchor="w")
        update_text = self.t(self.update_state).format(
            version=self.latest_release.version if self.latest_release else "", error=self.update_error,
        )
        tk.Label(updates, text=update_text, fg=MUTED, bg=PAPER,
                 wraplength=630, justify="left").pack(anchor="w")
        tk.Button(updates, text=self.t("check_updates"), command=self.check_updates,
                  state="disabled" if self.checking_updates or self.busy else "normal",
                  fg=ACCENT, bg=PAPER, relief="flat", cursor="hand2").pack(side="left")
        if self.update_state == "available":
            tk.Button(updates, text=self.t("install_update"), command=self.confirm_update,
                      state="disabled" if self.busy else "normal", fg=PAPER, bg=ACCENT,
                      relief="flat", padx=12, cursor="hand2").pack(side="left")

        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True)
        canvas = tk.Canvas(content, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(content, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        body = tk.Frame(canvas, bg=BG, padx=36, pady=26)
        body_window = canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(body_window, width=event.width))
        body.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        self.root.bind("<Button-4>", lambda _event: canvas.yview_scroll(-1, "units"))
        self.root.bind("<Button-5>", lambda _event: canvas.yview_scroll(1, "units"))
        tk.Label(body, text=self.t("subtitle"), font=("DejaVu Sans", 10, "bold"),
                 fg=ACCENT, bg=BG).pack(anchor="w")
        tk.Label(body, text=self.t("title"), font=("DejaVu Sans", 25, "bold"),
                 fg=INK, bg=BG).pack(anchor="w", pady=(6, 4))
        tk.Label(body, text=self.t("description"), font=("DejaVu Sans", 11),
                 fg=MUTED, bg=BG, wraplength=650, justify="left").pack(anchor="w")

        card = tk.Frame(body, bg=PAPER, padx=23, pady=20, highlightbackground="#dce4dc", highlightthickness=1)
        card.pack(fill="x", pady=(23, 18))
        running = agent_running()
        status = self.t("running") if running else self.t("stopped")
        tk.Label(card, text="●  " + status, font=("DejaVu Sans", 12, "bold"),
                 fg=ACCENT if running else "#a05b31", bg=PAPER).pack(anchor="w")
        tk.Label(card, text=self.t("network"), font=("DejaVu Sans", 9, "bold"),
                 fg=MUTED, bg=PAPER).pack(anchor="w", pady=(18, 4))
        tk.Label(card, text=self.network_summary(), font=("DejaVu Sans", 11),
                 fg=INK, bg=PAPER, wraplength=620, justify="left").pack(anchor="w")

        action = "pair" if running else "enable"
        tk.Button(body, text=self.t("pair" if running else "activate"), command=lambda: self.start(action),
                  state="disabled" if self.busy else "normal", font=("DejaVu Sans", 12, "bold"),
                  fg=PAPER, bg=ACCENT, activeforeground=PAPER, activebackground="#0f6556",
                  relief="flat", padx=20, pady=11, cursor="hand2").pack(anchor="w")
        if self.busy:
            tk.Label(body, text=self.t("working"), font=("DejaVu Sans", 10),
                     fg=MUTED, bg=BG).pack(anchor="w", pady=(9, 0))

        if self.code:
            tk.Label(body, text=self.t("code_label"), font=("DejaVu Sans", 9, "bold"),
                     fg=ACCENT, bg=BG).pack(anchor="w", pady=(23, 3))
            tk.Label(body, text=self.code, font=("DejaVu Sans Mono", 30, "bold"),
                     fg=INK, bg=BG).pack(anchor="w")
            tk.Button(body, text=self.t("copy"), command=self.copy_code, relief="flat",
                      fg=ACCENT, bg=BG, cursor="hand2").pack(anchor="w")
            note = self.t("code_note") + "\n" + self.t("steps")
        else:
            note = self.t("ready_steps") if running else self.t("steps")
        tk.Label(body, text=note, font=("DejaVu Sans", 10), fg=MUTED,
                 bg=BG, justify="left", wraplength=650).pack(anchor="w", pady=(14, 0))
        tk.Button(body, text=self.t("open_ha"), command=lambda: webbrowser.open("http://homeassistant.local:8123"),
                  fg=ACCENT, bg=BG, relief="flat", cursor="hand2").pack(anchor="w", pady=(8, 0))
        tk.Label(self.root, text=self.t("footer"), font=("DejaVu Sans", 9),
                 fg=MUTED, bg=BG, padx=36, pady=12).pack(anchor="w")

    def copy_code(self) -> None:
        if self.code:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.code)

    def start(self, action: str) -> None:
        if self.busy:
            return
        self.busy = True
        if action != "update":
            self.code = None
        self.draw()

        def run() -> None:
            try:
                result = subprocess.run(["pkexec", HELPER, action], capture_output=True,
                                        text=True, timeout=None if action == "update" else 180, check=False)
            except (OSError, subprocess.TimeoutExpired) as err:
                self.results.put((action, err))
            else:
                self.results.put((action, result))

        threading.Thread(target=run, daemon=True).start()

    def check_updates(self) -> None:
        if self.checking_updates or self.busy:
            return
        self.checking_updates = True
        self.update_state = "checking"
        self.draw()

        def run() -> None:
            try:
                result = fetch_latest_github_release(platform="ubuntu", include_prereleases="-" in AGENT_VERSION)
            except Exception as error:
                result = error
            self.results.put(("check_updates", result))

        threading.Thread(target=run, daemon=True).start()

    def confirm_update(self) -> None:
        if not self.busy and messagebox.askyesno("WakeLink", self.t("confirm_update")):
            self.start("update")

    def poll(self) -> None:
        try:
            action, result = self.results.get_nowait()
        except queue.Empty:
            self.root.after(100, self.poll)
            return
        if action == "check_updates":
            self.checking_updates = False
            try:
                if isinstance(result, Exception):
                    raise result
                self.latest_release = result
                self.update_state = "available" if is_newer_version(result.version, AGENT_VERSION) else "current"
            except Exception as error:
                self.latest_release = None
                self.update_state = "update_error"
                self.update_error = format_update_error(error)
        elif isinstance(result, Exception):
            self.busy = False
            messagebox.showerror(self.t("error"), str(result))
        elif result.returncode:
            self.busy = False
            messagebox.showerror(self.t("error"), result.stderr.strip() or self.t("cancelled"))
        elif action == "update":
            self.busy = False
            messagebox.showinfo("WakeLink", self.t("updated"))
            self.root.destroy()
            return
        else:
            self.busy = False
            self.code = parse_pairing_code(result.stdout)
        self.draw()
        self.root.after(100, self.poll)


def main() -> None:
    root = tk.Tk()
    WakeLinkWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
