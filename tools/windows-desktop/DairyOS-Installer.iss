; DairyOS Windows installer
; Installs the complete DairyOS application bundle into Program Files while
; keeping farm data under ProgramData. Uninstall deliberately does not remove
; ProgramData so a reinstall/upgrade cannot destroy farm records.

#define AppName "DairyOS"
#define AppVersion "0.1.0"
#define AppPublisher "DairyOS"
#define AppExeName "DairyOS.exe"

[Setup]
AppId={{D7F1A4D7-5F15-4CC5-B0D0-DAIRYOS0001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\DairyOS
DefaultGroupName=DairyOS
OutputDir=..\..\dist\DairyOS-Installer
OutputBaseFilename=DairyOS-Windows-Installer
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
DisableProgramGroupPage=yes

[Files]
Source: "..\..\dist\DairyOS-Release\DairyOS\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Registry]
; Application configuration only. Never store database passwords here.
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_ENV"; ValueData: "production"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_DATA_DIR"; ValueData: "{commonappdata}\DairyOS"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_INSTALL_ROOT"; ValueData: "{app}"; Flags: uninsdeletevalue

[Icons]
Name: "{autoprograms}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExeName}"
Name: "{autodesktop}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppExeName}"

[Dirs]
Name: "{commonappdata}\DairyOS"

[UninstallDelete]
; Deliberately empty: ProgramData is farm data and survives uninstall/reinstall.

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  NeedsRestart := False;
end;
