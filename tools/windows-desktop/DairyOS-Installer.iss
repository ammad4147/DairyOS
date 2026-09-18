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
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_DATA_DIR"; ValueData: "{code:DairyOSDataRoot}"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: string; ValueName: "DAIRYOS_INSTALL_ROOT"; ValueData: "{app}"; Flags: uninsdeletevalue

[Icons]
Name: "{autoprograms}\DairyOS"; Filename: "{app}\{#AppExeName}"; Parameters: "--data-root ""{code:DairyOSDataRoot}"""; WorkingDir: "{app}"; IconFilename: "{app}\dairyos-cow.ico"
Name: "{autodesktop}\DairyOS"; Filename: "{app}\{#AppExeName}"; Parameters: "--data-root ""{code:DairyOSDataRoot}"""; WorkingDir: "{app}"; IconFilename: "{app}\dairyos-cow.ico"

[Dirs]
Name: "{commonappdata}\DairyOS"

[Run]
Filename: "{app}\{#AppExeName}"; Parameters: "--data-root ""{code:DairyOSDataRoot}"""; Description: "Launch DairyOS"; Flags: nowait postinstall skipifsilent; Check: ShouldLaunchDairyOS

[UninstallDelete]
; Deliberately empty. ProgramData contains farm data, the private PostgreSQL
; cluster, backups, logs and protected runtime state and must survive uninstall.


[Code]
var
  PreserveFarmDataOnUninstall: Boolean;
  PreservedFarmDataPath: String;

function CanonicalDairyOSDataRoot(): String;
begin
  Result := ExpandConstant('{commonappdata}\DairyOS');
end;


function DairyOSDataRoot(Param: String): String;
begin
  Result := CanonicalDairyOSDataRoot();
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
    '--data-root "' + DairyOSDataRoot('') + '"';

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
  LifecyclePath := DairyOSDataRoot('') + '\lifecycle.json';

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
  BackupPath := DairyOSDataRoot('') + '\backups';

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
  StoragePath := DairyOSDataRoot('') + '\storage';

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

function CanonicalDairyOSDataRootHasExistingState(): Boolean;
var
  FindRec: TFindRec;
  Root: String;
begin
  Result := False;
  Root := CanonicalDairyOSDataRoot();

  if not DirExists(Root) then
    exit;

  if FindFirst(AddBackslash(Root) + '*', FindRec) then
  begin
    try
      repeat
        if (FindRec.Name <> '.') and
           (FindRec.Name <> '..') then
        begin
          Result := True;
          exit;
        end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;


function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';

  if CanonicalDairyOSDataRootHasExistingState() then
  begin
    Result :=
      'DairyOS clean installation cannot continue because the canonical ' +
      'DairyOS data location already contains existing state:' + #13#10#13#10 +
      CanonicalDairyOSDataRoot() + #13#10#13#10 +
      'Setup will not overwrite, import, restore, select, or adopt existing ' +
      'farm data. Preserve or remove the existing DairyOS data through the ' +
      'supported DairyOS Data Management or uninstall workflow, then run ' +
      'Setup again.';
    exit;
  end;
end;

function ShouldLaunchDairyOS(): Boolean;
begin
  Result := True;
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

  if not Exec(
    PowerShellExe,
    Params,
    ExpandConstant('{app}'),
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
  begin
    Log('DairyOS uninstall: could not start process-stop helper for ' + ExecutablePath);
    Result := False;
    exit;
  end;
  Log('DairyOS uninstall: process-stop helper for ' + ExecutablePath +
    ' exited with code ' + IntToStr(ResultCode));
  Result := ResultCode = 0;
end;

function RemoveInstalledBackupTask(): Boolean;
var
  SchtasksExe: String;
  ExecResult: Boolean;
  ResultCode: Integer;
  QueryResultCode: Integer;
begin
  Result := False;
  { Treat an already-removed task as success, but fail closed if the task
    remains after deletion. This prevents the uninstaller from leaving a
    scheduled action pointing at an application that has been removed. }
  SchtasksExe := ExpandConstant('{sys}\schtasks.exe');
  Log('DairyOS uninstall: removing automatic backup task with ' + SchtasksExe);
  ExecResult := Exec(
    SchtasksExe,
    '/Delete /F /TN "DairyOS-Automatic-Backup"',
    ExpandConstant('{app}'),
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );
  if not ExecResult then
  begin
    Log('DairyOS uninstall: could not start scheduled-task delete helper.');
    exit;
  end;
  Log('DairyOS uninstall: scheduled-task delete helper exited with code ' +
    IntToStr(ResultCode));

  { The delete command returns a nonzero code when the task is already
    absent. Querying afterward distinguishes that harmless case from a task
    that still exists and could run an executable that Setup is removing. }
  ExecResult := Exec(
    SchtasksExe,
    '/Query /TN "DairyOS-Automatic-Backup"',
    ExpandConstant('{app}'),
    SW_HIDE,
    ewWaitUntilTerminated,
    QueryResultCode
  );
  if not ExecResult then
  begin
    Log('DairyOS uninstall: could not start scheduled-task query helper.');
    exit;
  end;
  Log('DairyOS uninstall: scheduled-task query helper exited with code ' +
    IntToStr(QueryResultCode));

  Result := QueryResultCode <> 0;
  if Result then
    Log('DairyOS uninstall: automatic backup task is absent.')
  else
    Log('DairyOS uninstall: automatic backup task remains; uninstall blocked.');
end;

function ChoosePreservationDestination(): Boolean;
var
  SuggestedName: String;
begin
  SuggestedName := 'DairyOS-Farm-' + GetDateTimeString('yyyymmdd-hhnnss', '-', ':') + '.dairypkg';
  Result := GetSaveFileName(
    'Choose where to save the complete DairyOS farm-data package',
    PreservedFarmDataPath,
    SuggestedName,
    'DairyOS Farm Package (*.dairypkg)|*.dairypkg',
    'dairypkg'
  );
  if Result and (CompareText(ExtractFileExt(PreservedFarmDataPath), '.dairypkg') <> 0) then
    PreservedFarmDataPath := PreservedFarmDataPath + '.dairypkg';
end;

function ExportFarmDataForUninstall(): Boolean;
var
  DairyOSExe: String;
  Params: String;
  ResultCode: Integer;
begin
  Result := False;
  DairyOSExe := ExpandConstant('{app}\\DairyOS.exe');
  if not FileExists(DairyOSExe) then
  begin
    MsgBox('DairyOS.exe is missing. Farm data cannot be verified for preservation, so uninstall is blocked.', mbError, MB_OK);
    exit;
  end;

  Params := '--farm-data-export "' + PreservedFarmDataPath + '" ' +
    '--data-root "' + DairyOSDataRoot('') + '"';
  if (not Exec(DairyOSExe, Params, ExpandConstant('{app}'), SW_HIDE,
    ewWaitUntilTerminated, ResultCode)) or (ResultCode <> 0) then
  begin
    MsgBox(
      'DairyOS could not create and verify the requested farm-data package. ' +
      'Uninstall is blocked and the installed farm state remains in place.',
      mbError, MB_OK
    );
    exit;
  end;

  if not DirExists(PreservedFarmDataPath) then
  begin
    MsgBox('The verified farm-data package was not found at the selected destination. Uninstall is blocked.', mbError, MB_OK);
    exit;
  end;

  MsgBox(
    'Complete DairyOS farm data was saved and verified at:' + #13#10#13#10 +
    PreservedFarmDataPath + #13#10#13#10 +
    'Keep this package safe. It can be imported later from Settings > Data Management.',
    mbInformation, MB_OK
  );
  Log('DairyOS uninstall: verified farm-data preservation package: ' + PreservedFarmDataPath);
  Result := True;
end;

function StopInstalledDairyOSForUninstall(): Boolean;
var
  PgCtl: String;
  DataDir: String;
  PidFile: String;
  ResultCode: Integer;
begin
  Result := False;
  Log('DairyOS uninstall: stopping the private runtime.');

  { Stop only the private DairyOS PostgreSQL cluster, identified by its
    persistent data directory. Never terminate arbitrary postgres.exe
    processes because the workstation may host unrelated PostgreSQL services. }
  PgCtl := ExpandConstant('{app}\runtime\PostgreSQL\bin\pg_ctl.exe');
  DataDir := DairyOSDataRoot('') + '\postgres\data';
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
      Log('DairyOS uninstall: private PostgreSQL stop failed with code ' +
        IntToStr(ResultCode));
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

  { Remove the application-owned task. Farm data and existing backups remain
    untouched under ProgramData. }
  if not RemoveInstalledBackupTask() then
  begin
    MsgBox(
      'The DairyOS automatic-backup task could not be removed. ' +
      'Uninstall is blocked and the application remains installed.',
      mbError,
      MB_OK
    );
    Log('DairyOS uninstall: scheduled-task removal failed.');
    exit;
  end;

  Sleep(1000);
  Log('DairyOS uninstall: guarded pre-uninstall operations passed.');
  Result := True;
end;

function UninstallPreservationChoiceFromCommandLine(): String;
var
  I: Integer;
  Arg: String;
begin
  Result := '';
  for I := 1 to ParamCount do
  begin
    Arg := Uppercase(ParamStr(I));
    if Arg = '/PRESERVEFARMDATA=NO' then
      Result := 'NO'
    else if Arg = '/PRESERVEFARMDATA=YES' then
      Result := 'YES';
  end;
end;

function InitializeUninstall(): Boolean;
var
  Choice: Integer;
  CommandChoice: String;
begin
  Result := False;
  PreserveFarmDataOnUninstall := False;
  PreservedFarmDataPath := '';
  CommandChoice := UninstallPreservationChoiceFromCommandLine();

  { An explicit automation decision may bypass the interactive prompt. Normal
    operator uninstall remains Yes/No/Cancel. }
  if CommandChoice = 'NO' then
  begin
    Log('DairyOS uninstall: explicit command-line decision is not to create a preservation package.');
    Result := StopInstalledDairyOSForUninstall();
    exit;
  end;

  Choice := MsgBox(
    'Do you want to preserve the complete DairyOS farm data before uninstalling?' + #13#10#13#10 +
    'Choose Yes to select a destination and create a verified portable farm-data package.' + #13#10 +
    'Choose No to uninstall without creating a preservation package.' + #13#10 +
    'Choose Cancel to leave DairyOS installed.',
    mbConfirmation, MB_YESNOCANCEL
  );
  if Choice = IDCANCEL then
    exit;

  if Choice = IDYES then
  begin
    PreserveFarmDataOnUninstall := True;
    if not ChoosePreservationDestination() then
      exit;
    if not ExportFarmDataForUninstall() then
      exit;
  end
  else
  begin
    Choice := MsgBox(
      'No preservation package will be created. Continue uninstalling DairyOS?',
      mbConfirmation, MB_YESNO
    );
    if Choice <> IDYES then
      exit;
  end;

  Result := StopInstalledDairyOSForUninstall();
end;
