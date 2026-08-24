!include LogicLib.nsh

; NSIS does not provide a $PROGRAMDATA special variable. $COMMONAPPDATA
; resolves to the Windows common application-data directory (C:\ProgramData).
!define DAIRYOS_DATA_ROOT "$COMMONAPPDATA\DairyOS"

!macro customInstall
  ; Farm data is deliberately outside the program directory.
  CreateDirectory "${DAIRYOS_DATA_ROOT}"
  CreateDirectory "${DAIRYOS_DATA_ROOT}\backups"
  CreateDirectory "${DAIRYOS_DATA_ROOT}\recovery"

  ; Allow the local Windows Users group to operate the farm application while
  ; keeping Program Files protected. The database itself still listens only
  ; on loopback.
  nsExec::ExecToLog '"$SYSDIR\icacls.exe" "${DAIRYOS_DATA_ROOT}" /grant *S-1-5-32-545:(OI)(CI)M /T /C'

  ; Persist the installer location for the recovery/uninstall data guard.
  FileOpen $0 "${DAIRYOS_DATA_ROOT}\install.json" w
  FileWrite $0 '{"install_root":"$INSTDIR"}'
  FileClose $0

  ; Copy the recovery tooling into ProgramData so it survives an application
  ; uninstall and remains available for disaster recovery.
  SetOutPath "${DAIRYOS_DATA_ROOT}\recovery"
  File "..\..\recovery\DairyOS-Data-Backup.ps1"
  File "..\..\recovery\DairyOS-Data-Restore.ps1"
  File "..\..\recovery\README.txt"
!macroend

!macro customUnInstall
  ; Never delete the farm data directory. Before removing application files,
  ; make a final logical backup. If the backup cannot be completed, abort the
  ; uninstall rather than risk an avoidable data-loss event.
  IfFileExists "${DAIRYOS_DATA_ROOT}\recovery\DairyOS-Data-Backup.ps1" 0 done
    nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "${DAIRYOS_DATA_ROOT}\recovery\DairyOS-Data-Backup.ps1" -InstallRoot "$INSTDIR" -Reason uninstall'
    Pop $0
    ${If} $0 != 0
      MessageBox MB_ICONSTOP|MB_OK "DairyOS could not complete the final farm-data backup.\n\nUninstallation has been cancelled to protect your farm data."
      Abort
    ${EndIf}
done:
!macroend
