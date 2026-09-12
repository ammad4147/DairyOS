; DairyOS Windows release installer
; Packages the already-built frozen desktop bundle. Farm data lives outside
; the application directory and must survive uninstall/reinstall.

#define AppName "DairyOS"
#define AppVersion "0.1.0"
#define AppPublisher "DairyOS"
#define AppExeName "DairyOS.exe"
#ifndef SourceCommit
  #define SourceCommit "unknown"
#endif
#ifndef SourceTree
  #define SourceTree "unknown"
#endif

[Setup]
AppId={{D7F1A4D7-5F15-4CC5-B0D0-DA1A05000001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
SetupIconFile=..\..\assets\dairyos-cow.ico
DefaultDirName={autopf}\DairyOS
DefaultGroupName=DairyOS
; Keep the one-click setup beside the staged DairyOS application folder:
; dist\DairyOS-Release\DairyOS-Windows-Installer.exe
; dist\DairyOS-Release\DairyOS\
OutputDir=..\..\dist\DairyOS-Release
OutputBaseFilename=DairyOS-Windows-Installer
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=140,135
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\dairyos-cow.ico
DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
; Source commit and tree are bound in the release manifests. Inno Setup does
; not support VersionInfoComments; keeping provenance in the manifest avoids
; compiler-version-specific directives in the executable version resource.

[Files]
Source: "..\..\dist\DairyOS-Release\DairyOS\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Registry]
; Configuration only. Database passwords are deliberately never stored here.
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_ENV"; ValueData: "production"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_DATA_DIR"; ValueData: "{commonappdata}\DairyOS"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_INSTALL_ROOT"; ValueData: "{app}"; Flags: uninsdeletevalue

[Icons]
Name: "{autoprograms}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\dairyos-cow.ico"
Name: "{autodesktop}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\dairyos-cow.ico"

[Dirs]
Name: "{commonappdata}\DairyOS"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch DairyOS"; Flags: nowait postinstall skipifsilent; Check: ShouldLaunchDairyOS

[UninstallDelete]
; Deliberately empty. ProgramData contains farm data, the private PostgreSQL
; cluster, backups, logs and protected runtime state and must survive uninstall.


[Code]
var
  DataChoicePage: TWizardPage;
  ExistingDataDetected: Boolean;
  PreservationDestination: String;

function CreatePreservationPackage(): Boolean; forward;

function DairyOSDataRoot(): String;
begin
  Result := ExpandConstant('{commonappdata}\DairyOS');
end;


procedure ProvisionLifecycleState();
var
  DairyOSExe: String;
  Params: String;
  ResultCode: Integer;
begin
  DairyOSExe := ExpandConstant('{app}\DairyOS.exe');
  if not FileExists(DairyOSExe) then
    RaiseException('DairyOS.exe is missing; lifecycle state cannot be initialized.');

  Params :=
    '--lifecycle-install ' +
    '--installation-root "' + ExpandConstant('{app}') + '" ' +
    '--data-root "' + DairyOSDataRoot() + '"';

  if (not Exec(
    DairyOSExe,
    Params,
    ExpandConstant('{app}'),
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  )) or (ResultCode <> 0) then
    RaiseException(
      'DairyOS lifecycle state could not be initialized. ' +
      'Setup cannot continue safely.'
    );
end;

procedure ProvisionLifecycleManifestAcl();
var
  LifecyclePath: String;
  IcaclsExe: String;
  Params: String;
  ResultCode: Integer;
begin
  LifecyclePath := DairyOSDataRoot() + '\lifecycle.json';

  if not FileExists(LifecyclePath) then
    RaiseException(
      'DairyOS lifecycle.json is missing after lifecycle provisioning. ' +
      'Setup cannot continue safely.'
    );

  { lifecycle.json is mutable application metadata. Setup creates it while
    elevated, while the normal DairyOS runtime operates without elevation.
    Grant Modify only on this file to the built-in Users SID. Do not grant
    recursive rights to ProgramData, PostgreSQL or security state. }
  IcaclsExe := ExpandConstant('{sys}\icacls.exe');
  Params := '"' + LifecyclePath + '" /grant:r *S-1-5-32-545:(M)';

  if (not Exec(
    IcaclsExe,
    Params,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  )) or (ResultCode <> 0) then
    RaiseException(
      'DairyOS lifecycle metadata permissions could not be provisioned. ' +
      'Setup cannot continue safely.'
    );
end;

procedure ProvisionBackupTreeAcl();
var
  BackupPath: String;
  IcaclsExe: String;
  Params: String;
  ResultCode: Integer;
begin
  BackupPath := DairyOSDataRoot() + '\backups';

  if not DirExists(BackupPath) then
    ForceDirectories(BackupPath);

  { Automatic backups run as the ordinary interactive user with a limited
    token. The backup tree is mutable farm-protection state: rolling dumps,
    mirror metadata and backup-health.json must support atomic replacement,
    pruning and retained-install repair. Scope Modify strictly to backups; do
    not broaden PostgreSQL or security-state permissions. }
  IcaclsExe := ExpandConstant('{sys}\icacls.exe');
  Params := '"' + BackupPath + '" /grant:r *S-1-5-32-545:(OI)(CI)(M) /T /C';

  if (not Exec(
    IcaclsExe,
    Params,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  )) or (ResultCode <> 0) then
    RaiseException(
      'DairyOS backup-data permissions could not be provisioned. ' +
      'Setup cannot continue safely.'
    );
end;

procedure ProvisionStorageTreeAcl();
var
  StoragePath: String;
  IcaclsExe: String;
  Params: String;
  ResultCode: Integer;
begin
  StoragePath := DairyOSDataRoot() + '\storage';

  if not DirExists(StoragePath) then
    ForceDirectories(StoragePath);

  { Operational JSON projections are mutable state written by the ordinary
    DairyOS runtime. Scope Modify to this dedicated storage tree; PostgreSQL,
    credentials and the rest of ProgramData remain protected. }
  IcaclsExe := ExpandConstant('{sys}\icacls.exe');
  Params := '"' + StoragePath + '" /grant:r *S-1-5-32-545:(OI)(CI)(M) /T /C';

  if (not Exec(
    IcaclsExe,
    Params,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  )) or (ResultCode <> 0) then
    RaiseException(
      'DairyOS operational storage permissions could not be provisioned. ' +
      'Setup cannot continue safely.'
    );
end;

procedure ProvisionAutomaticBackupTask();
var
  BackupExe: String;
  EscapedBackupExe: String;
  PowerShellExe: String;
  PowerShellCommand: String;
  TaskCommand: String;
  ResultCode: Integer;
begin
  BackupExe := ExpandConstant('{app}\DairyOSBackup.exe');
  if not FileExists(BackupExe) then
    RaiseException('DairyOSBackup.exe is missing; automatic backups cannot be provisioned.');

  { Use the ScheduledTasks API rather than schtasks /TR command-line parsing.
    /TR can persist an invalid Program Files split. New-ScheduledTaskAction
    stores Execute and Arguments as separate structured fields. }
  EscapedBackupExe := BackupExe;
  StringChangeEx(EscapedBackupExe, '''', '''''', True);

  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  PowerShellCommand :=
    '$ErrorActionPreference = ''Stop''; ' +
    '$action = New-ScheduledTaskAction -Execute ''' + EscapedBackupExe + '''; ' +
    '$trigger = New-ScheduledTaskTrigger -Once -At ([datetime]::Today) ' +
      '-RepetitionInterval (New-TimeSpan -Hours 6); ' +
    '$principal = New-ScheduledTaskPrincipal ' +
      '-UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) ' +
      '-LogonType Interactive -RunLevel Limited; ' +
    'Register-ScheduledTask -TaskName ''DairyOS-Automatic-Backup'' ' +
      '-Action $action -Trigger $trigger -Principal $principal -Force | Out-Null';

  TaskCommand :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "' +
    PowerShellCommand + '"';

  if (not Exec(
    PowerShellExe,
    TaskCommand,
    ExpandConstant('{app}'),
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  )) or (ResultCode <> 0) then
    RaiseException(
      'DairyOS automatic backup protection could not be installed. ' +
      'Setup cannot continue safely.'
    );
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    ProvisionLifecycleState();
    ProvisionLifecycleManifestAcl();
    ProvisionStorageTreeAcl();
    ProvisionBackupTreeAcl();
    ProvisionAutomaticBackupTask();
  end;
end;

function DetectExistingDairyOSData(): Boolean;
var
  Root: String;
begin
  Root := DairyOSDataRoot();
  Result :=
    FileExists(Root + '\installation_state.json') or
    FileExists(Root + '\lifecycle.json') or
    FileExists(Root + '\postgres\runtime.json') or
    FileExists(Root + '\postgres\security.json') or
    DirExists(Root + '\postgres\data') or
    DirExists(Root + '\storage') or
    DirExists(Root + '\backups');
end;

procedure InitializeWizard();
var
  Intro: TNewStaticText;
  ExistingDetail: TNewStaticText;
  Caution: TNewStaticText;
begin
  ExistingDataDetected := DetectExistingDairyOSData();

  DataChoicePage := CreateCustomPage(
    wpSelectDir,
    'DairyOS Farm Data',
    'Review how this installation will use farm data on this computer.'
  );

  Intro := TNewStaticText.Create(DataChoicePage);
  Intro.Parent := DataChoicePage.Surface;
  Intro.Left := ScaleX(8);
  Intro.Top := ScaleY(8);
  Intro.Width := DataChoicePage.SurfaceWidth - ScaleX(16);
  Intro.AutoSize := False;
  Intro.WordWrap := True;
  Intro.Font.Name := 'Segoe UI';
  Intro.Font.Size := 12;
  Intro.Font.Style := [fsBold];
  Intro.Caption := '';
  Intro.AdjustHeight();

  if ExistingDataDetected then
  begin
    Intro.Caption := 'Existing DairyOS farm data was detected on this computer.';
    Intro.AdjustHeight();

    ExistingDetail := TNewStaticText.Create(DataChoicePage);
    ExistingDetail.Parent := DataChoicePage.Surface;
    ExistingDetail.Left := ScaleX(12);
    ExistingDetail.Top := Intro.Top + Intro.Height + ScaleY(20);
    ExistingDetail.Width := DataChoicePage.SurfaceWidth - ScaleX(48);
    ExistingDetail.AutoSize := False;
    ExistingDetail.WordWrap := True;
    ExistingDetail.Font.Name := 'Segoe UI';
    ExistingDetail.Font.Size := 10;
    ExistingDetail.Caption :=
      'INSTALLER STATUS: the existing farm database and ProgramData records will be retained. ' +
      'Setup does not provide a data-selection or reset command.';
    ExistingDetail.AdjustHeight();

  end
  else
  begin
    Intro.Caption := 'No existing DairyOS farm data was detected on this computer.';
    Intro.AdjustHeight();

    ExistingDetail := TNewStaticText.Create(DataChoicePage);
    ExistingDetail.Parent := DataChoicePage.Surface;
    ExistingDetail.Left := ScaleX(12);
    ExistingDetail.Top := Intro.Top + Intro.Height + ScaleY(20);
    ExistingDetail.Width := DataChoicePage.SurfaceWidth - ScaleX(48);
    ExistingDetail.AutoSize := False;
    ExistingDetail.WordWrap := True;
    ExistingDetail.Font.Name := 'Segoe UI';
    ExistingDetail.Font.Size := 10;
    ExistingDetail.Caption :=
      'INSTALLER STATUS: no existing farm data was detected. Setup will initialize the ' +
      'new DairyOS installation; it does not copy or restore farm data.';
    ExistingDetail.AdjustHeight();

  end;

  Caution := TNewStaticText.Create(DataChoicePage);
  Caution.Parent := DataChoicePage.Surface;
  Caution.Left := ScaleX(12);
  Caution.Top := ExistingDetail.Top + ExistingDetail.Height + ScaleY(28);
  Caution.Width := DataChoicePage.SurfaceWidth - ScaleX(24);
  Caution.AutoSize := False;
  Caution.WordWrap := True;
  Caution.Font.Name := 'Segoe UI';
  Caution.Font.Size := 10;
  Caution.Font.Style := [fsBold];
  Caution.Caption :=
    'IMPORTANT' + #13#10 +
    'This page is informational, not a data-choice control. ' +
    'The installer will not delete or overwrite an existing DairyOS farm database. ' +
    'A protected zero-state reset is available from Settings after the application starts.';
  Caution.AdjustHeight();
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
end;

function ShouldLaunchDairyOS(): Boolean;
begin
  Result := True;
end;

function IsSilentUninstall(): Boolean;
var
  I: Integer;
  Param: String;
begin
  Result := False;
  for I := 1 to ParamCount do
  begin
    Param := Uppercase(ParamStr(I));
    if (Param = '/SILENT') or (Param = '/VERYSILENT') then
    begin
      Result := True;
      exit;
    end;
  end;
end;

function StopInstalledProcessByPath(const ExecutablePath: String): Boolean;
var
  PowerShellExe: String;
  PowerShellCommand: String;
  Params: String;
  SafePath: String;
  ResultCode: Integer;
begin
  SafePath := ExecutablePath;
  StringChangeEx(SafePath, '''', '''''', True);
  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  PowerShellCommand :=
    '$ErrorActionPreference = ''Stop''; ' +
    '$target = [IO.Path]::GetFullPath(''' + SafePath + '''); ' +
    'Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and ' +
      '[IO.Path]::GetFullPath($_.ExecutablePath) -ieq $target } | ' +
    'ForEach-Object { Stop-Process -Id $_.ProcessId -Force }';
  Params :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "' +
    PowerShellCommand + '"';

  Result := Exec(
    PowerShellExe,
    Params,
    ExpandConstant('{app}'),
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) and (ResultCode = 0);
end;

function StopInstalledDairyOSForUninstall(): Boolean;
var
  PgCtl: String;
  DataDir: String;
  PidFile: String;
  ResultCode: Integer;
begin
  Result := False;

  { Stop only the private DairyOS PostgreSQL cluster, identified by its
    persistent data directory. Never terminate arbitrary postgres.exe
    processes because the workstation may host unrelated PostgreSQL services. }
  PgCtl := ExpandConstant('{app}\runtime\PostgreSQL\bin\pg_ctl.exe');
  DataDir := DairyOSDataRoot() + '\postgres\data';
  PidFile := DataDir + '\postmaster.pid';

  if FileExists(PidFile) then
  begin
    if not FileExists(PgCtl) then
    begin
      MsgBox(
        'DairyOS private PostgreSQL is running but the bundled pg_ctl.exe is missing. ' +
        'Uninstall is blocked so the application runtime is not left partially removed.',
        mbError,
        MB_OK
      );
      exit;
    end;

    if (not Exec(
      PgCtl,
      '-D "' + DataDir + '" stop -m fast -w -t 30',
      ExpandConstant('{app}'),
      SW_HIDE,
      ewWaitUntilTerminated,
      ResultCode
    )) or (ResultCode <> 0) then
    begin
      MsgBox(
        'DairyOS private PostgreSQL could not be stopped cleanly. ' +
        'Uninstall is blocked so the database and application runtime remain intact.',
        mbError,
        MB_OK
      );
      exit;
    end;
  end;

  { Stop only processes whose executable path is inside the installed
    DairyOS directory. Image-name matching could terminate an unrelated
    process that happens to use the same filename. }
  if not StopInstalledProcessByPath(ExpandConstant('{app}\DairyOS.exe')) then
  begin
    MsgBox(
      'DairyOS application processes could not be stopped by installed path. ' +
      'Uninstall is blocked so unrelated processes are not affected.',
      mbError,
      MB_OK
    );
    exit;
  end;
  if not StopInstalledProcessByPath(ExpandConstant('{app}\DairyOSBackup.exe')) then
  begin
    MsgBox(
      'DairyOS backup processes could not be stopped by installed path. ' +
      'Uninstall is blocked so unrelated processes are not affected.',
      mbError,
      MB_OK
    );
    exit;
  end;

  { Remove the scheduled task whose executable is about to be removed.
    Backup data itself remains under ProgramData. }
  Exec(
    ExpandConstant('{sys}\schtasks.exe'),
    '/Delete /F /TN "DairyOS-Automatic-Backup"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

  if not CreatePreservationPackage() then
    exit;

  Sleep(1000);
  Result := True;
end;

function CreatePreservationPackage(): Boolean;
var
  PowerShellExe: String;
  PowerShellCommand: String;
  Params: String;
  ArchivePath: String;
  SafeDataRoot: String;
  SafeArchivePath: String;
  ResultCode: Integer;
begin
  Result := False;

  if PreservationDestination = '' then
  begin
    Result := True;
    exit;
  end;

  if not DirExists(DairyOSDataRoot()) then
  begin
    MsgBox(
      'The DairyOS farm-data directory does not exist, so a preservation package could not be created.',
      mbError,
      MB_OK
    );
    exit;
  end;

  ForceDirectories(PreservationDestination);
  ArchivePath :=
    AddBackslash(PreservationDestination) +
    'DairyOS-Farm-Preservation-' +
    GetDateTimeString('yyyymmdd-hhnnss', True, True) +
    '.zip';

  SafeDataRoot := DairyOSDataRoot();
  StringChangeEx(SafeDataRoot, '''', '''''', True);
  SafeArchivePath := ArchivePath;
  StringChangeEx(SafeArchivePath, '''', '''''', True);

  { PostgreSQL is stopped before this function is called. Package the entire
    ProgramData farm root, then reopen the archive and verify that it contains
    entries before uninstall is allowed to continue. }
  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  PowerShellCommand :=
    '$ErrorActionPreference = ''Stop''; ' +
    '$source = ''' + SafeDataRoot + '''; ' +
    '$archive = ''' + SafeArchivePath + '''; ' +
    '$items = @(Get-ChildItem -LiteralPath $source -Force | ForEach-Object { $_.FullName }); ' +
    'if ($items.Count -eq 0) { throw ''DairyOS farm data root is empty.'' }; ' +
    'Compress-Archive -Path $items -DestinationPath $archive -CompressionLevel Optimal -Force; ' +
    '$zip = [System.IO.Compression.ZipFile]::OpenRead($archive); ' +
    'try { if ($zip.Entries.Count -eq 0) { throw ''The preservation package is empty.'' } } ' +
    'finally { $zip.Dispose() }';
  Params :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "' +
    PowerShellCommand + '"';

  if (not Exec(
    PowerShellExe,
    Params,
    PreservationDestination,
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  )) or (ResultCode <> 0) or (not FileExists(ArchivePath)) then
  begin
    MsgBox(
      'DairyOS could not create and verify the farm-data preservation package. ' +
      'Uninstall is blocked and the application remains installed.',
      mbError,
      MB_OK
    );
    exit;
  end;

  MsgBox(
    'Verified DairyOS farm-data preservation package saved at:' + #13#10 +
    ArchivePath,
    mbInformation,
    MB_OK
  );
  Result := True;
end;

function InitializeUninstall(): Boolean;
var
  Choice: Integer;
begin
  Result := True;

  if IsSilentUninstall() then
  begin
    Result := StopInstalledDairyOSForUninstall();
    exit;
  end;

  Choice := MsgBox(
    'Choose how to proceed with DairyOS uninstall:' + #13#10 + #13#10 +
    'YES - PRESERVE FARM DATA AND UNINSTALL' + #13#10 +
    'Choose a destination for a verified farm-data package, then remove the DairyOS application.' + #13#10 + #13#10 +
    'NO - CANCEL AND KEEP THE APPLICATION' + #13#10 +
    'No data or application files are removed.',
    mbConfirmation,
    MB_YESNO
  );

  if Choice = IDYES then
  begin
    if not SelectDirectory(
      'Select a destination folder for the verified DairyOS farm-data preservation package:',
      '',
      PreservationDestination
    ) then
    begin
      Result := False;
      exit;
    end;
    Result := StopInstalledDairyOSForUninstall();
    exit;
  end;

  Result := False;
end;
