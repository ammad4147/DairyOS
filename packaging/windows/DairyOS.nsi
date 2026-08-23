!include "MUI2.nsh"
!include "LogicLib.nsh"

Unicode True
RequestExecutionLevel admin

Name "DairyOS"
Caption "DairyOS Enterprise Installer"
OutFile "DairyOS-Setup.exe"
InstallDir "$PROGRAMFILES64\DairyOS"
InstallDirRegKey HKLM "Software\DairyOS" "InstallDir"

VIProductVersion "0.1.0.0"
VIAddVersionKey "ProductName" "DairyOS"
VIAddVersionKey "CompanyName" "Trident Dairies"
VIAddVersionKey "FileDescription" "DairyOS Enterprise Dairy Farm Operating System"
VIAddVersionKey "FileVersion" "0.1.0"
VIAddVersionKey "LegalCopyright" "Trident Dairies"

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\uninstall.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

Var DataDir
Var PostgresInstaller

Section "DairyOS" SecMain
  StrCpy $DataDir "$COMMONAPPDATA\DairyOS"
  StrCpy $PostgresInstaller "$INSTDIR\postgresql-18.6-1-windows-x64.exe"

  SetOutPath "$INSTDIR"
  File /r "build\DairyOS\*.*"
  File "postgresql-18.6-1-windows-x64.exe"
  File "install.ps1"
  File "uninstall.ps1"

  WriteRegStr HKLM "Software\DairyOS" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\DairyOS" "DataDir" "$DataDir"

  CreateDirectory "$SMPROGRAMS\DairyOS"
  CreateShortcut "$SMPROGRAMS\DairyOS\DairyOS.lnk" "$INSTDIR\DairyOS.exe" "" "$INSTDIR\DairyOS.exe" 0 SW_SHOWNORMAL "" "Open DairyOS"
  CreateShortcut "$DESKTOP\DairyOS.lnk" "$INSTDIR\DairyOS.exe" "" "$INSTDIR\DairyOS.exe" 0 SW_SHOWNORMAL "" "Open DairyOS"

  ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\install.ps1" -AppDir "$INSTDIR" -DataDir "$DataDir" -PostgresInstaller "$PostgresInstaller"' $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "DairyOS installation failed while initializing the farm database. No existing farm data was modified."
    Abort
  ${EndIf}

  WriteUninstaller "$INSTDIR\Uninstall DairyOS.exe"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DairyOS" "DisplayName" "DairyOS"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DairyOS" "DisplayVersion" "0.1.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DairyOS" "Publisher" "Trident Dairies"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DairyOS" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DairyOS" "UninstallString" '"$INSTDIR\Uninstall DairyOS.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DairyOS" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DairyOS" "NoRepair" 1
SectionEnd

Section "Uninstall"
  ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\uninstall.ps1" -AppDir "$INSTDIR" -DataDir "$COMMONAPPDATA\DairyOS"' $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "DairyOS could not create its final farm-data backup. Uninstall has been aborted and your farm data has been left untouched."
    Abort
  ${EndIf}

  Delete "$DESKTOP\DairyOS.lnk"
  RMDir /r "$SMPROGRAMS\DairyOS"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DairyOS"
  DeleteRegKey HKLM "Software\DairyOS"
  RMDir /r "$INSTDIR"

  ; Deliberately DO NOT remove %ProgramData%\DairyOS.
  ; It contains the PostgreSQL cluster, credentials, backups and recovery evidence.
SectionEnd
