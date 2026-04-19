Unicode true
ManifestDPIAware true
RequestExecutionLevel admin

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"

!define APP_NAME "PC Power Free"
!define APP_PUBLISHER "PC Power Free"
!define APP_VERSION "0.1.0"
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

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
!define MUI_FINISHPAGE_RUN "$INSTDIR\PCPowerSetup.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Abrir el configurador ahora"
!define MUI_FINISHPAGE_SHOWREADME ""

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Spanish"

Section "Install" SEC_MAIN
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Este instalador es solo para Windows x64."
    Abort
  ${EndIf}

  SetShellVarContext all
  SetOutPath "$INSTDIR"

  File "${OUTPUT_DIR}\PCPowerAgent.exe"
  File "${OUTPUT_DIR}\PCPowerSetup.exe"
  File "${OUTPUT_DIR}\install-task.ps1"
  File "${OUTPUT_DIR}\uninstall-task.ps1"
  File "${OUTPUT_DIR}\add-firewall-rule.ps1"
  File "${OUTPUT_DIR}\config.example.json"

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\Configurar ${APP_NAME}.lnk" "$INSTDIR\PCPowerSetup.exe"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\Desinstalar ${APP_NAME}.lnk" "$INSTDIR\Uninstall.exe"
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

  ExecWait '"$SYSDIR\schtasks.exe" /Delete /TN "PC Power Agent" /F'
  ExecWait '"$SYSDIR\netsh.exe" advfirewall firewall delete rule name="PC Power Agent"'

  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Configurar ${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Desinstalar ${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"

  Delete "$INSTDIR\PCPowerAgent.exe"
  Delete "$INSTDIR\PCPowerSetup.exe"
  Delete "$INSTDIR\install-task.ps1"
  Delete "$INSTDIR\uninstall-task.ps1"
  Delete "$INSTDIR\add-firewall-rule.ps1"
  Delete "$INSTDIR\config.example.json"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

  Delete "$APPDATA\${APP_NAME}\config.json"
  Delete "$APPDATA\${APP_NAME}\home_assistant_values.txt"
  Delete "$APPDATA\${APP_NAME}\pc_power_agent.log"
  RMDir "$APPDATA\${APP_NAME}"

  DeleteRegKey HKLM "${UNINSTALL_KEY}"
SectionEnd
