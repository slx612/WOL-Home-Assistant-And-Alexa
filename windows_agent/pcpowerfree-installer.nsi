Unicode true
ManifestDPIAware true
RequestExecutionLevel admin

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"

!define APP_NAME "PC Power Free"
!define APP_PUBLISHER "PC Power Free"
!define APP_VERSION "0.2.0-beta.7"
!define INSTALL_BASENAME "pcpowerfree-windows-x64-setup.exe"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"

!ifndef OUTPUT_DIR
  !define OUTPUT_DIR ".\dist"
!endif

Name "${APP_NAME}"
OutFile "${OUTPUT_DIR}\${INSTALL_BASENAME}"
InstallDir "$ProgramFiles64\${APP_NAME}"
InstallDirRegKey HKLM "${UNINSTALL_KEY}" "InstallLocation"
ShowInstDetails show
ShowUnInstDetails show
BrandingText "${APP_NAME}"
Var IsUpgrade

!define MUI_ABORTWARNING
!insertmacro MUI_RESERVEFILE_LANGDLL
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
!define MUI_FINISHPAGE_RUN "$INSTDIR\PCPowerSetup.exe"
!define MUI_FINISHPAGE_RUN_FUNCTION FinishRun
!define MUI_FINISHPAGE_RUN_TEXT "$(FinishRunText)"
!define MUI_FINISHPAGE_SHOWREADME ""

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_PAGE_CUSTOMFUNCTION_SHOW FinishPageShow
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Spanish"

LangString FinishRunText 1033 "Open the configurator now"
LangString FinishRunText 1034 "Abrir el configurador ahora"
LangString UpgradeFinishRunText 1033 "Open the tray app (existing pairing preserved)"
LangString UpgradeFinishRunText 1034 "Abrir la bandeja (vinculacion anterior conservada)"
LangString UpgradeFailed 1033 "Could not restart the updated agent. Your configuration was kept. Check upgrade.log in the data folder before retrying; do not uninstall."
LangString UpgradeFailed 1034 "No se pudo arrancar el agente actualizado. Se conserva tu configuracion. Consulta upgrade.log en la carpeta de datos antes de reintentar; no desinstales."
LangString OnlyX64Message 1033 "This installer is only for Windows x64."
LangString OnlyX64Message 1034 "Este instalador es solo para Windows x64."
LangString ConfigureShortcut 1033 "Configure ${APP_NAME}"
LangString ConfigureShortcut 1034 "Configurar ${APP_NAME}"
LangString UninstallShortcut 1033 "Uninstall ${APP_NAME}"
LangString UninstallShortcut 1034 "Desinstalar ${APP_NAME}"

Function .onInit
  StrCpy $IsUpgrade 0
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Function FinishPageShow
  ${If} $IsUpgrade == 1
    SendMessage $mui.FinishPage.Run ${WM_SETTEXT} 0 "STR:$(UpgradeFinishRunText)"
  ${EndIf}
FunctionEnd

Function FinishRun
  ${If} $IsUpgrade == 1
    Exec '"$INSTDIR\PCPowerTray.exe"'
  ${Else}
    Exec '"$INSTDIR\PCPowerSetup.exe"'
  ${EndIf}
FunctionEnd

Section "Install" SEC_MAIN
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
  File "${OUTPUT_DIR}\config.example.json"

  ExecWait '"$INSTDIR\PCPowerSetup.exe" --upgrade-existing' $0
  ${If} $0 == 0
    StrCpy $IsUpgrade 1
  ${ElseIf} $0 != 3
    MessageBox MB_ICONSTOP "$(UpgradeFailed)"
    Abort
  ${EndIf}

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\$(ConfigureShortcut).lnk" "$INSTDIR\PCPowerSetup.exe"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\$(UninstallShortcut).lnk" "$INSTDIR\Uninstall.exe"
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\PCPowerSetup.exe"

  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\PCPowerSetup.exe"
  WriteRegStr HKLM "${UNINSTALL_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINSTALL_KEY}" "NoRepair" 1
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

  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\$(ConfigureShortcut).lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\$(UninstallShortcut).lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"

  Delete "$INSTDIR\PCPowerAgent.exe"
  Delete "$INSTDIR\PCPowerTray.exe"
  Delete "$INSTDIR\PCPowerSetup.exe"
  Delete "$INSTDIR\install-task.ps1"
  Delete "$INSTDIR\uninstall-task.ps1"
  Delete "$INSTDIR\add-firewall-rule.ps1"
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
