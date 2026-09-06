; DairyOS Windows release installer
; Packages the already-built frozen desktop bundle. Farm data lives outside
; the application directory and must survive uninstall/reinstall.

#define AppName "DairyOS"
#define AppVersion "0.1.0"
#define AppPublisher "DairyOS"
#define AppExeName "DairyOS.exe"

[Setup]
AppId={{D7F1A4D7-5F15-4CC5-B0D0-DA1A05000001}
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
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Files]
Source: "..\..\dist\DairyOS-Release\DairyOS\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Registry]
; Configuration only. Database passwords are deliberately never stored here.
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_ENV"; ValueData: "production"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_DATA_DIR"; ValueData: "{commonappdata}\DairyOS"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_INSTALL_ROOT"; ValueData: "{app}"; Flags: uninsdeletevalue

[Icons]
Name: "{autoprograms}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autoprograms}\DairyOS Administration"; Filename: "{app}\DairyOS-Admin.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"

[Dirs]
Name: "{commonappdata}\DairyOS"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch DairyOS"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Deliberately empty. ProgramData contains farm data, the private PostgreSQL
; cluster, backups, logs and protected runtime state and must survive uninstall.
