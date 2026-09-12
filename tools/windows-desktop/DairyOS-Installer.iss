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
  DataChoicePage: TInputOptionWizardPage;
  CleanConfirmationPage: TInputQueryWizardPage;
  BackupChoicePage: TInputOptionWizardPage;
  ExistingDataDetected: Boolean;
  PreservationDestination: String;
  SelectedInstallMode: String;
  SelectedBackupPath: String;
  CleanConfirmationAccepted: Boolean;
  RestoreChoiceIndex: Integer;
  BackupCandidatePaths: array of String;

function CreatePreservationPackage(): Boolean; forward;
procedure StageInstallationChoice(); forward;

function DairyOSDataRoot(): String;
begin
  Result := ExpandConstant('{commonappdata}\DairyOS');
end;


function StripTrailingSeparators(const Value: String): String;
begin
  Result := Value;
  while (Length(Result) > 3) and
    ((Result[Length(Result)] = '\') or (Result[Length(Result)] = '/')) do
    Delete(Result, Length(Result), 1);
end;


function IsPathWithinRoot(const Candidate, Root: String): Boolean;
var
  CandidatePath: String;
  RootPath: String;
begin
  CandidatePath := Lowercase(
    StripTrailingSeparators(ExpandFileName(Candidate))
  );
  RootPath := Lowercase(
    StripTrailingSeparators(ExpandFileName(Root))
  );

  Result :=
    (CandidatePath = RootPath) or
    (Pos(AddBackslash(RootPath), AddBackslash(CandidatePath)) = 1);
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

procedure StageInstallationChoice();
var
  DairyOSExe: String;
  Params: String;
  ResultCode: Integer;
begin
  if SelectedInstallMode = 'clean' then
  begin
    if not CleanConfirmationAccepted then
      RaiseException('Clean installation was not explicitly confirmed.');
    Params :=
      '--lifecycle-choice ' +
      '--choice-mode clean ' +
      '--data-root "' + DairyOSDataRoot() + '"';
  end
  else if SelectedInstallMode = 'restore' then
  begin
    if SelectedBackupPath = '' then
      RaiseException('Restore was selected but no backup candidate was chosen.');
    Params :=
      '--lifecycle-choice ' +
      '--choice-mode restore ' +
      '--backup-path "' + SelectedBackupPath + '" ' +
      '--data-root "' + DairyOSDataRoot() + '"';
  end
  else if SelectedInstallMode = 'keep' then
  begin
    Params :=
      '--lifecycle-choice ' +
      '--choice-mode keep ' +
      '--data-root "' + DairyOSDataRoot() + '"';
  end
  else if SelectedInstallMode = 'new' then
  begin
    { Setup provisions lifecycle/storage folders before the packaged startup
      gate runs.  A genuinely new install must therefore carry an explicit
      clean-bootstrap authorization; treating it as Keep would make the
      safety gate mistake the freshly provisioned runtime folders for an
      established farm and block first start. }
    Params :=
      '--lifecycle-choice ' +
      '--choice-mode clean ' +
      '--data-root "' + DairyOSDataRoot() + '"';
  end
  else
    exit;

  DairyOSExe := ExpandConstant('{app}\DairyOS.exe');
  if (not Exec(
    DairyOSExe,
    Params,
    ExpandConstant('{app}'),
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  )) or (ResultCode <> 0) then
    RaiseException(
      'The selected DairyOS installation action could not be recorded. ' +
      'No farm data was intentionally deleted.'
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
    StageInstallationChoice();
  end;
end;

function DirectoryHasEntries(const Directory: String): Boolean;
var
  FindRec: TFindRec;
begin
  Result := False;
  if not DirExists(Directory) then
    exit;

  if FindFirst(AddBackslash(Directory) + '*', FindRec) then
  try
    repeat
      if (FindRec.Name <> '.') and (FindRec.Name <> '..') then
      begin
        Result := True;
        exit;
      end;
    until not FindNext(FindRec);
  finally
    FindClose(FindRec);
  end;
end;

procedure AddBackupCandidate(const Candidate: String);
var
  I: Integer;
  Normalized: String;
begin
  Normalized := Candidate;
  while (Length(Normalized) > 3) and
        (Normalized[Length(Normalized)] = '\') do
    Delete(Normalized, Length(Normalized), 1);

  if Normalized = '' then
    exit;

  for I := 0 to GetArrayLength(BackupCandidatePaths) - 1 do
    if Lowercase(BackupCandidatePaths[I]) = Lowercase(Normalized) then
      exit;

  SetArrayLength(BackupCandidatePaths, GetArrayLength(BackupCandidatePaths) + 1);
  BackupCandidatePaths[GetArrayLength(BackupCandidatePaths) - 1] := Normalized;
end;

procedure ScanBackupDirectory(const Directory: String; Depth: Integer);
var
  FindRec: TFindRec;
  Candidate: String;
begin
  if (Depth > 4) or (not DirExists(Directory)) then
    exit;

  if FileExists(AddBackslash(Directory) + 'backup.json') then
  begin
    AddBackupCandidate(Directory);
    exit;
  end;

  if not FindFirst(AddBackslash(Directory) + '*', FindRec) then
    exit;
  try
    repeat
      if (FindRec.Name <> '.') and (FindRec.Name <> '..') and
         (FindRec.Name <> 'backup-health.json') and
         (FindRec.Name[1] <> '.') then
      begin
        Candidate := AddBackslash(Directory) + FindRec.Name;
        if DirExists(Candidate) then
          ScanBackupDirectory(Candidate, Depth + 1)
        else if (Lowercase(ExtractFileExt(Candidate)) = '.dump') and
                FileExists(Candidate + '.json') then
          AddBackupCandidate(Candidate);
      end;
    until not FindNext(FindRec);
  finally
    FindClose(FindRec);
  end;
end;

procedure ScanKnownBackupRoots();
var
  Root: String;
  ConfiguredRoot: String;
  Drive: String;
  I: Integer;
begin
  SetArrayLength(BackupCandidatePaths, 0);
  Root := DairyOSDataRoot();

  ScanBackupDirectory(AddBackslash(Root) + 'backups', 0);
  ScanBackupDirectory(AddBackslash(ExtractFileDir(Root)) + 'recovery', 0);
  ScanBackupDirectory(AddBackslash(ExtractFileDir(Root)) + 'DairyOS-PurgeBackups', 0);

  ConfiguredRoot := GetEnv('DAIRYOS_BACKUP_MIRROR_ROOT');
  if ConfiguredRoot <> '' then
    ScanBackupDirectory(ConfiguredRoot, 0);
  ConfiguredRoot := GetEnv('DAIRYOS_RECOVERY_ROOT');
  if ConfiguredRoot <> '' then
    ScanBackupDirectory(ConfiguredRoot, 0);

  { Match the bounded, known removable/external backup roots used by the
    recovery catalog without searching arbitrary user files. }
  for I := Ord('C') to Ord('Z') do
  begin
    Drive := Chr(I) + ':\DairyOS-Backups';
    ScanBackupDirectory(Drive, 0);
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
    DirectoryHasEntries(Root + '\storage') or
    DirectoryHasEntries(Root + '\backups') or
    FileExists(ExpandConstant('{localappdata}\DairyOS-installation-state.json'));
end;

procedure InitializeWizard();
var
  I: Integer;
begin
  ExistingDataDetected := DetectExistingDairyOSData();
  ScanKnownBackupRoots();
  SelectedBackupPath := '';
  CleanConfirmationAccepted := False;
  RestoreChoiceIndex := -1;

  if ExistingDataDetected then
  begin
    DataChoicePage := CreateInputOptionPage(
      wpSelectDir,
      'DairyOS Farm Data',
      'Choose how this installation should use the existing farm data.',
      'Keep the current farm, restore one selected recovery point, or start a clean active farm.',
      True,
      True
    );
    DataChoicePage.Add('Keep existing farm data (recommended)');
    DataChoicePage.Add('Restore from a verified backup');
    DataChoicePage.Add('Start a clean farm');
    DataChoicePage.SelectedValueIndex := 0;
    SelectedInstallMode := 'keep';
    RestoreChoiceIndex := 1;
  end
  else if GetArrayLength(BackupCandidatePaths) > 0 then
  begin
    DataChoicePage := CreateInputOptionPage(
      wpSelectDir,
      'DairyOS Farm Data',
      'No active DairyOS farm was detected, but recovery points are available.',
      'Restore one selected recovery point or initialize a new empty active farm.',
      True,
      True
    );
    DataChoicePage.Add('Initialize a new empty farm');
    DataChoicePage.Add('Restore from a verified backup');
    DataChoicePage.SelectedValueIndex := 0;
    SelectedInstallMode := 'new';
    RestoreChoiceIndex := 1;
  end
  else
  begin
    DataChoicePage := CreateInputOptionPage(
      wpSelectDir,
      'DairyOS Farm Data',
      'This is a new DairyOS installation.',
      'DairyOS will initialize an empty active farm. No recovery data is copied.',
      True,
      True
    );
    DataChoicePage.Add('Initialize a new empty farm');
    DataChoicePage.SelectedValueIndex := 0;
    SelectedInstallMode := 'new';
  end;

  CleanConfirmationPage := CreateInputQueryPage(
    DataChoicePage.ID,
    'Confirm clean DairyOS farm',
    'This action clears the active farm history.',
    'Type the exact phrase below to confirm that the new installation starts with no prior farm data or logs.'
  );
  CleanConfirmationPage.Add(
    'Type CLEAN INSTALL DAIRYOS DATA to confirm:',
    False
  );

  BackupChoicePage := CreateInputOptionPage(
    DataChoicePage.ID,
    'DairyOS Recovery Point',
    'Choose one backup to restore.',
    'Only the selected path will be re-verified by DairyOS immediately before restoration.',
    True,
    True
  );
  if GetArrayLength(BackupCandidatePaths) = 0 then
    BackupChoicePage.Add('No backup candidates were found in the known DairyOS backup locations.')
  else
  begin
    for I := 0 to GetArrayLength(BackupCandidatePaths) - 1 do
      BackupChoicePage.Add(
        'Backup candidate (DairyOS verifies before restore): ' + BackupCandidatePaths[I]
      );
    BackupChoicePage.SelectedValueIndex := 0;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = DataChoicePage.ID then
  begin
    CleanConfirmationAccepted := False;
    if ExistingDataDetected then
    begin
      if DataChoicePage.SelectedValueIndex = 0 then
      begin
        SelectedInstallMode := 'keep';
        exit;
      end;

      if DataChoicePage.SelectedValueIndex = 1 then
      begin
        SelectedInstallMode := 'restore';
        exit;
      end;

      SelectedInstallMode := 'clean';
      exit;
    end;
    if (RestoreChoiceIndex >= 0) and
       (DataChoicePage.SelectedValueIndex = RestoreChoiceIndex) then
    begin
      SelectedInstallMode := 'restore';
      exit;
    end;
    SelectedInstallMode := 'new';
    exit;
  end;

  if CurPageID = CleanConfirmationPage.ID then
  begin
    if CleanConfirmationPage.Values[0] <> 'CLEAN INSTALL DAIRYOS DATA' then
    begin
      MsgBox(
        'Clean installation was not confirmed. No active farm data was changed.',
        mbError,
        MB_OK
      );
      Result := False;
      exit;
    end;
    CleanConfirmationAccepted := True;
    SelectedInstallMode := 'clean';
    exit;
  end;

  if CurPageID = BackupChoicePage.ID then
  begin
    if (DataChoicePage.SelectedValueIndex <> RestoreChoiceIndex) or
       (GetArrayLength(BackupCandidatePaths) = 0) then
    begin
      MsgBox(
        'No verified DairyOS backup candidate is available to restore. Choose another action or place a valid recovery point in a known backup location.',
        mbError,
        MB_OK
      );
      Result := False;
      exit;
    end;
    SelectedInstallMode := 'restore';
    SelectedBackupPath := BackupCandidatePaths[BackupChoicePage.SelectedValueIndex];
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if PageID = CleanConfirmationPage.ID then
    Result := (not ExistingDataDetected) or
      (SelectedInstallMode <> 'clean');
  if PageID = BackupChoicePage.ID then
    Result := (RestoreChoiceIndex < 0) or
      (DataChoicePage.SelectedValueIndex <> RestoreChoiceIndex);
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

function RemoveInstalledBackupTask(): Boolean;
var
  PowerShellExe: String;
  PowerShellCommand: String;
  Params: String;
  ResultCode: Integer;
begin
  { Treat an already-removed task as success, but fail closed if the task
    exists and cannot be removed. This prevents the uninstaller from leaving
    a scheduled action pointing at an application that has been removed. }
  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  PowerShellCommand :=
    '$ErrorActionPreference = ''Stop''; ' +
    '$task = Get-ScheduledTask -TaskName ''DairyOS-Automatic-Backup'' ' +
      '-ErrorAction SilentlyContinue; ' +
    'if ($null -ne $task) { ' +
      'Unregister-ScheduledTask -TaskName ''DairyOS-Automatic-Backup'' ' +
        '-Confirm:$false }';
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

  { Verify and create the preservation package before changing the scheduled
    task. If archiving fails, uninstall remains blocked without leaving the
    installed runtime's automatic-backup protection removed. }
  if not CreatePreservationPackage() then
    exit;

  { Remove the scheduled task only after preservation succeeds. Backup data
    itself remains under ProgramData. }
  if not RemoveInstalledBackupTask() then
  begin
    MsgBox(
      'The farm-data preservation package was verified, but the DairyOS automatic-backup task ' +
      'could not be removed. Uninstall is blocked and the application remains installed.',
      mbError,
      MB_OK
    );
    exit;
  end;

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

  { Never allow the destination to be inside the data being archived.  Apart
    from producing a misleading backup, that would let the archive include
    itself and can leave Compress-Archive with a locked/incomplete file. }
  if IsPathWithinRoot(PreservationDestination, DairyOSDataRoot()) then
  begin
    MsgBox(
      'Choose a preservation location outside the DairyOS farm-data directory. ' +
      'The selected location would otherwise be included in its own archive.',
      mbError,
      MB_OK
    );
    exit;
  end;

  if not ForceDirectories(PreservationDestination) then
  begin
    MsgBox(
      'DairyOS could not create the selected preservation folder. ' +
      'Uninstall is blocked and the application remains installed.',
      mbError,
      MB_OK
    );
    exit;
  end;

  ArchivePath :=
    AddBackslash(PreservationDestination) +
    'DairyOS-Farm-Preservation-' +
    GetDateTimeString('yyyymmdd-hhnnss', '', '') +
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
    'Add-Type -AssemblyName System.IO.Compression.FileSystem; ' +
    '$source = ''' + SafeDataRoot + '''; ' +
    '$archive = ''' + SafeArchivePath + '''; ' +
    'if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw ''DairyOS farm data root is unavailable.'' }; ' +
    '$items = @(Get-ChildItem -LiteralPath $source -Force); ' +
    'if ($items.Count -eq 0) { throw ''DairyOS farm data root is empty.'' }; ' +
    '[System.IO.Compression.ZipFile]::CreateFromDirectory($source, $archive, [System.IO.Compression.CompressionLevel]::Optimal, $true); ' +
    'if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) { throw ''The preservation package was not created.'' }; ' +
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
  { The environment value is used only by the unattended certification path.
    Interactive uninstall still requires the operator to choose the destination
    through BrowseForFolder. The same path validation and ZIP verification are
    used in both cases. }
  PreservationDestination := GetEnv('DAIRYOS_UNINSTALL_PRESERVATION_DESTINATION');

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
    if not BrowseForFolder(
      'Select a destination folder for the verified DairyOS farm-data preservation package:',
      PreservationDestination,
      False
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
