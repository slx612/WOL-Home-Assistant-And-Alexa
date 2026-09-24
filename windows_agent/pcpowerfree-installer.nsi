Unicode true
ManifestDPIAware true
RequestExecutionLevel admin

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"

!define APP_NAME "PC Power Free"
!define APP_DISPLAY_NAME "WakeLink"
!define APP_PUBLISHER "WakeLink open-source project"
!define APP_VERSION "0.2.0-beta.12"
!define INSTALL_BASENAME "pcpowerfree-windows-x64-setup.exe"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

!ifndef OUTPUT_DIR
  !define OUTPUT_DIR ".\dist"
!endif

; Keep APP_NAME and the legacy filenames/registry key stable for in-place upgrades.
Name "${APP_DISPLAY_NAME}"
OutFile "${OUTPUT_DIR}\${INSTALL_BASENAME}"
InstallDir "$ProgramFiles64\${APP_NAME}"
InstallDirRegKey HKLM "${UNINSTALL_KEY}" "InstallLocation"
ShowInstDetails hide
ShowUnInstDetails hide
BrandingText "${APP_DISPLAY_NAME} ${APP_VERSION}"
VIProductVersion "0.2.0.10"
VIAddVersionKey "ProductName" "${APP_DISPLAY_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "FileDescription" "${APP_DISPLAY_NAME} Windows installer"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "MIT License"
Var IsUpgrade

!define MUI_ABORTWARNING
!insertmacro MUI_RESERVEFILE_LANGDLL
!define MUI_ICON "assets\wakelink.ico"
!define MUI_UNICON "assets\wakelink.ico"
!define MUI_WELCOMEPAGE_TITLE "${APP_DISPLAY_NAME}"
!define MUI_WELCOMEPAGE_TEXT "$(WelcomeText)"
!define MUI_FINISHPAGE_TITLE "$(FinishTitle)"
!define MUI_FINISHPAGE_TEXT "$(FinishText)"
!define MUI_FINISHPAGE_TEXT_LARGE
!define MUI_FINISHPAGE_NOREBOOTSUPPORT
!define MUI_FINISHPAGE_RUN "$INSTDIR\PCPowerSetup.exe"
!define MUI_FINISHPAGE_RUN_FUNCTION FinishRun
!define MUI_FINISHPAGE_RUN_TEXT "$(FinishRunText)"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!define MUI_PAGE_CUSTOMFUNCTION_SHOW FinishPageShow
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Spanish"

LangString WelcomeText 1033 "Local PC power control with Home Assistant.$\r$\n$\r$\nInstall or update WakeLink. Existing PC Power Free settings and pairing are kept.$\r$\n$\r$\nOn a new PC, the dashboard guides you through first-time configuration after installation."
LangString WelcomeText 1034 "Control local del PC con Home Assistant.$\r$\n$\r$\nInstala o actualiza WakeLink. Se conservan los ajustes y la vinculacion de PC Power Free.$\r$\n$\r$\nEn un PC nuevo, el panel te guiara por la configuracion inicial al terminar."
LangString FinishTitle 1033 "WakeLink installed"
LangString FinishTitle 1034 "WakeLink instalado"
LangString FinishText 1033 "Next: first-time configuration in the dashboard. Review your PC settings and pair with Home Assistant.$\r$\n$\r$\nNo Windows restart is required."
LangString FinishText 1034 "Siguiente: configuracion inicial en el panel. Revisa los ajustes del PC y vincula Home Assistant.$\r$\n$\r$\nNo hace falta reiniciar Windows."
LangString UpgradeFinishTitle 1033 "WakeLink updated"
LangString UpgradeFinishTitle 1034 "WakeLink actualizado"
LangString UpgradeFinishText 1033 "Your settings and pairing are preserved. No setup or new pairing code is needed.$\r$\n$\r$\nStartup preferences are unchanged. No Windows restart is required."
LangString UpgradeFinishText 1034 "Se conservan tus ajustes y vinculacion. No necesitas repetir la configuracion ni otro codigo.$\r$\n$\r$\nEl inicio automatico no cambia. No hace falta reiniciar Windows."
LangString FinishRunText 1033 "Open WakeLink"
LangString FinishRunText 1034 "Abrir WakeLink"
LangString UpgradeFinishRunText 1033 "Open WakeLink and the tray app"
LangString UpgradeFinishRunText 1034 "Abrir WakeLink y la bandeja"
LangString UpgradeFailed 1033 "Could not restart the updated agent. Your configuration was kept. Check upgrade.log in the data folder before retrying; do not uninstall."
LangString UpgradeFailed 1034 "No se pudo arrancar el agente actualizado. Se conserva tu configuracion. Consulta upgrade.log en la carpeta de datos antes de reintentar; no desinstales."
LangString OnlyX64Message 1033 "This installer is only for Windows x64."
LangString OnlyX64Message 1034 "Este instalador es solo para Windows x64."
LangString DesktopShortcut 1033 "Create a desktop shortcut"
LangString DesktopShortcut 1034 "Crear un acceso directo en el escritorio"
LangString ShortcutFailed 1033 "The desktop shortcut could not be updated. WakeLink is installed; open it from the Start menu."
LangString ShortcutFailed 1034 "No se pudo actualizar el acceso directo del escritorio. WakeLink esta instalado; abrelo desde el menu Inicio."

Function .onInit
  StrCpy $IsUpgrade 0
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Function FinishPageShow
  ${If} $IsUpgrade == 1
    SendMessage $mui.FinishPage.Title ${WM_SETTEXT} 0 "STR:$(UpgradeFinishTitle)"
    SendMessage $mui.FinishPage.Text ${WM_SETTEXT} 0 "STR:$(UpgradeFinishText)"
    SendMessage $mui.FinishPage.Run ${WM_SETTEXT} 0 "STR:$(UpgradeFinishRunText)"
  ${EndIf}
FunctionEnd

Function FinishRun
  ${If} $IsUpgrade == 1
    Exec '"$INSTDIR\PCPowerTray.exe"'
    ; Do not override the dashboard's saved language on an upgrade.
    Exec '"$INSTDIR\PCPowerSetup.exe"'
  ${ElseIf} $LANGUAGE == ${LANG_SPANISH}
    Exec '"$INSTDIR\PCPowerSetup.exe" --lang es'
  ${Else}
    Exec '"$INSTDIR\PCPowerSetup.exe" --lang en'
  ${EndIf}
FunctionEnd

Section "WakeLink" SEC_MAIN
  SectionIn RO
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "$(OnlyX64Message)"
    Abort
  ${EndIf}

  SetShellVarContext all
  SetOutPath "$INSTDIR"

  ExecWait '"$SYSDIR\schtasks.exe" /End /TN "PC Power Agent"'
  ExecWait '"$SYSDIR\taskkill.exe" /IM "PCPowerAgent.exe" /F'
  ExecWait '"$SYSDIR\taskkill.exe" /IM "PCPowerTray.exe" /F'
  Sleep 1200

  File "${OUTPUT_DIR}\PCPowerAgent.exe"
  File "${OUTPUT_DIR}\PCPowerTray.exe"
  File "${OUTPUT_DIR}\PCPowerSetup.exe"
  File "${OUTPUT_DIR}\install-task.ps1"
  File "${OUTPUT_DIR}\uninstall-task.ps1"
  File "${OUTPUT_DIR}\add-firewall-rule.ps1"
  File "desktop-shortcut.ps1"
  File "${OUTPUT_DIR}\config.example.json"

  ExecWait '"$INSTDIR\PCPowerSetup.exe" --upgrade-existing' $0
  ${If} $0 == 0
    StrCpy $IsUpgrade 1
  ${ElseIf} $0 != 3
    MessageBox MB_ICONSTOP "$(UpgradeFailed)"
    Abort
  ${EndIf}

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Remove only the two known legacy shortcuts; keep the old data/install paths.
  Delete "$SMPROGRAMS\${APP_NAME}\Configure PC Power Free.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Configurar PC Power Free.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Uninstall PC Power Free.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Desinstalar PC Power Free.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"

  ; Keep one public Start menu entry; desktop creation is optional below.
  CreateDirectory "$SMPROGRAMS\${APP_DISPLAY_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_DISPLAY_NAME}\${APP_DISPLAY_NAME}.lnk" "$INSTDIR\PCPowerSetup.exe"
  ExecWait '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "$INSTDIR\desktop-shortcut.ps1" -DesktopPath "$DESKTOP" -InstallDir "$INSTDIR"' $0
  ${If} $0 != 0
    MessageBox MB_ICONEXCLAMATION "$(ShortcutFailed)"
  ${EndIf}

  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName" "${APP_DISPLAY_NAME}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\PCPowerSetup.exe"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section /o "$(DesktopShortcut)" SEC_DESKTOP
  SetShellVarContext all
  ExecWait '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "$INSTDIR\desktop-shortcut.ps1" -DesktopPath "$DESKTOP" -InstallDir "$INSTDIR" -Create' $0
  ${If} $0 != 0
    MessageBox MB_ICONEXCLAMATION "$(ShortcutFailed)"
  ${EndIf}
SectionEnd

Section "Uninstall"
  SetShellVarContext all

  ExecWait '"$SYSDIR\taskkill.exe" /IM "PCPowerTray.exe" /F'
  ExecWait '"$SYSDIR\schtasks.exe" /End /TN "PC Power Agent"'
  ExecWait '"$SYSDIR\taskkill.exe" /IM "PCPowerAgent.exe" /F'
  Sleep 1200
  ExecWait '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -WindowStyle Hidden -Command "if (Get-Process -Name PCPowerAgent -ErrorAction SilentlyContinue) { exit 1 }"' $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "Could not stop PC Power Agent. Close it and retry uninstalling."
    Abort
  ${EndIf}
  ExecWait '"$SYSDIR\schtasks.exe" /Delete /TN "PC Power Agent" /F'
  ExecWait '"$SYSDIR\netsh.exe" advfirewall firewall delete rule name="PC Power Agent"'

  ExecWait '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "$INSTDIR\desktop-shortcut.ps1" -DesktopPath "$DESKTOP" -InstallDir "$INSTDIR"'
  Delete "$SMPROGRAMS\${APP_DISPLAY_NAME}\${APP_DISPLAY_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_DISPLAY_NAME}"
  Delete "$SMPROGRAMS\${APP_NAME}\Configure PC Power Free.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Configurar PC Power Free.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Uninstall PC Power Free.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Desinstalar PC Power Free.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"

  Delete "$INSTDIR\PCPowerAgent.exe"
  Delete "$INSTDIR\PCPowerTray.exe"
  Delete "$INSTDIR\PCPowerSetup.exe"
  Delete "$INSTDIR\install-task.ps1"
  Delete "$INSTDIR\uninstall-task.ps1"
  Delete "$INSTDIR\add-firewall-rule.ps1"
  Delete "$INSTDIR\desktop-shortcut.ps1"
  Delete "$INSTDIR\config.example.json"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "PC Power Free Tray"

  Delete "$APPDATA\${APP_NAME}\config.json"
  Delete "$APPDATA\${APP_NAME}\guard_state.json"
  Delete "$APPDATA\${APP_NAME}\home_assistant_values.txt"
  Delete "$APPDATA\${APP_NAME}\pc_power_agent.log"
  Delete "$APPDATA\${APP_NAME}\pc_power_agent.log.*"
  Delete "$APPDATA\${APP_NAME}\update_state.json"
  Delete "$APPDATA\${APP_NAME}\upgrade.log"
  Delete "$APPDATA\${APP_NAME}\agent-cert.pem"
  Delete "$APPDATA\${APP_NAME}\agent-key.pem"
  RMDir "$APPDATA\${APP_NAME}"

  DeleteRegKey HKLM "${UNINSTALL_KEY}"
SectionEnd
