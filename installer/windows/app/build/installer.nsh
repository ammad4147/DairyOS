!include LogicLib.nsh

!macro customInstall
  ; Farm data is deliberately outside the program directory.
  CreateDirectory "$PROGRAMDATA\DairyOS"
  CreateDirectory "$PROGRAMDATA\DairyOS\backups"
  CreateDirectory "$PROGRAMDATA\DairyOS\recovery"

  ; Allow the local Windows Users group to operate the farm application while
  ; keeping Program Files protected. The database itself still listens only
  ; on loopback.
  nsExec::ExecToLog '"$SYSDIR\icacls.exe" "$PROGRAMDATA\DairyOS" /grant *S-1-5-32-545:(OI)(CI)M /T /C'

  ; Persist the installer location for the recovery/uninstall data guard.
  FileOpen $0 "$PROGRAMDATA\DairyOS\install.json" w
  FileWrite $0 '{"install_root":"$INSTDIR"}'
  FileClose $0

  ; Copy the recovery tooling into ProgramData so it survives an application
  ; uninstall and remains available for disaster recovery.
  SetOutPath "$PROGRAMDATA\DairyOS\recovery"
  File /nonfatal "..\runtime\recovery\DairyOS-Data-Backup.ps1"
  File /nonfatal "..\runtime\recovery\DairyOS-Data-Restore.ps1"
  File /nonfatal "..\runtime\recovery\README.txt"
!macroend

!macro customUnInstall
  ; Never delete the farm data directory. Before removing application files,
  ; make a final logical backup. If the backup cannot be completed, abort the
  ; uninstall rather than risk an avoidable data-loss event.
  IfFileExists "$PROGRAMDATA\DairyOS\recovery\DairyOS-Data-Backup.ps1" 0 done
    nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$PROGRAMDATA\DairyOS\recovery\DairyOS-Data-Backup.ps1" -InstallRoot "$INSTDIR" -Reason uninstall'
    Pop $0
    ${If} $0 != 0
      MessageBox MB_ICONSTOP|MB_OK "DairyOS could not complete the final farm-data backup.\n\nUninstallation has been cancelled to protect your farm data."
      Abort
    ${EndIf}
done:
!macroend
