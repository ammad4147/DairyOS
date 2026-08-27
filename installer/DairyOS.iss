; DairyOS Windows Installer — Release Candidate
; Farm data lives under %LOCALAPPDATA%\DairyOS and is deliberately not removed by uninstall.

#define AppName "DairyOS"
#define AppVersion "0.1.0"
#define AppPublisher "Trident Dairies"
#define AppExeName "DairyOS.exe"

[Setup]
AppId={{C4A3D0AB-0B6D-4B86-A7E7-7F8C47B5C3D2}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\DairyOS
DefaultGroupName=DairyOS
OutputDir=..\dist\installer
OutputBaseFilename=DairyOS-Setup-{#AppVersion}-rc1
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
DisableProgramGroupPage=yes
Uninstallable=yes

[Files]
Source: "..\dist\DairyOS\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autodesktop}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autoprograms}\DairyOS\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autoprograms}\DairyOS\Uninstall DairyOS"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch DairyOS"; Flags: nowait postinstall skipifsilent

[Uninstall]
; Intentionally no UninstallDelete entry for %LOCALAPPDATA%\DairyOS.
; Governed farm data must survive application removal/reinstallation.
