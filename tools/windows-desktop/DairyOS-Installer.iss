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
Name: "{autoprograms}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\dairyos-cow.ico"
Name: "{autodesktop}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\dairyos-cow.ico"

[Dirs]
Name: "{commonappdata}\DairyOS"

[Run]
Filename: "{app}\{#AppExeName}"; Parameters: "--data-root ""{code:DairyOSDataRoot}"""; Description: "Launch DairyOS"; Flags: nowait postinstall skipifsilent; Check: ShouldLaunchDairyOS

[UninstallDelete]
; Deliberately empty. ProgramData contains farm data, the private PostgreSQL
; cluster, backups, logs and protected runtime state and must survive uninstall.


[Code]
var
  DataChoicePage: TInputOptionWizardPage;
  CleanConfirmationPage: TInputQueryWizardPage;
  BackupChoicePage: TInputOptionWizardPage;
  ExistingDataDetected: Boolean;
  SelectedInstallMode: String;
  SelectedBackupPath: String;
  CleanConfirmationAccepted: Boolean;
  RestoreChoiceIndex: Integer;
  BackupCandidatePaths: array of String;
  SelectedDataRoot: String;

procedure StageInstallationChoice(); forward;

function CanonicalDairyOSDataRoot(): String;
begin
  Result := ExpandConstant('{commonappdata}\DairyOS');
end;

function ExistingDairyOSDataRoot(): String;
var
  ConfiguredRoot: String;
begin
  { The machine-level pointer is the active root after a prior installation,
    including a previously selected sibling new-farm root. Fall back to the
    conventional root only when no active pointer exists. }
  if RegQueryStringValue(
    HKLM,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'DAIRYOS_DATA_DIR',
    ConfiguredRoot
  ) and (ConfiguredRoot <> '') then
    Result := ConfiguredRoot
  else
    Result := CanonicalDairyOSDataRoot();
end;

function AllocateNewDairyOSDataRoot(): String;
var
  Base: String;
  Candidate: String;
  Suffix: Integer;
begin
  Base := ExpandConstant('{commonappdata}\DairyOS-New-') +
    GetDateTimeString('yyyymmdd-hhnnss', '', '');
  Candidate := Base;
  Suffix := 0;
  while DirExists(Candidate) do
  begin
    Suffix := Suffix + 1;
    Candidate := Base + '-' + IntToStr(Suffix);
  end;
  Result := Candidate;
end;

function DairyOSDataRoot(Param: String): String;
begin
  if SelectedDataRoot <> '' then
    Result := SelectedDataRoot
  else
    Result := ExistingDairyOSDataRoot();
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

procedure StageInstallationChoice();
var
  DairyOSExe: String;
  Params: String;
  ResultCode: Integer;
begin
  if SelectedInstallMode = 'clean' then
  begin
    if not CleanConfirmationAccepted then
      RaiseException('New empty farm was not explicitly confirmed.');
    Params :=
      '--lifecycle-choice ' +
      '--choice-mode new ' +
      '--data-root "' + DairyOSDataRoot('') + '"';
  end
  else if SelectedInstallMode = 'restore' then
  begin
    if SelectedBackupPath = '' then
      RaiseException('Restore was selected but no backup candidate was chosen.');
    Params :=
      '--lifecycle-choice ' +
      '--choice-mode restore ' +
      '--backup-path "' + SelectedBackupPath + '" ' +
      '--data-root "' + DairyOSDataRoot('') + '"';
  end
  else if SelectedInstallMode = 'keep' then
  begin
    Params :=
      '--lifecycle-choice ' +
      '--choice-mode keep ' +
      '--data-root "' + DairyOSDataRoot('') + '"';
  end
  else if SelectedInstallMode = 'new' then
  begin
    { A new root carries an explicit non-destructive bootstrap authorization.
      The previous root is never opened for deletion or reset. }
    Params :=
      '--lifecycle-choice ' +
      '--choice-mode new ' +
      '--data-root "' + DairyOSDataRoot('') + '"';
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

function SelectNewDairyOSDataRoot(): String;
begin
  { Reuse the conventional root only when it is genuinely empty. If any
    prior material exists there, allocate a sibling so a new farm starts with
    no inherited records or logs while the prior root remains untouched. }
  if DirectoryHasEntries(ExistingDairyOSDataRoot()) then
    Result := AllocateNewDairyOSDataRoot()
  else
    Result := ExistingDairyOSDataRoot();
end;

procedure ScanKnownBackupRoots();
var
  ConfiguredRoot: String;
begin
  SetArrayLength(BackupCandidatePaths, 0);
  { Only explicitly owned/declared recovery locations are inspected. A clean
    install must not treat arbitrary historical backup trees as active farm
    data or make a recovery choice from an unrelated drive. }
  ScanBackupDirectory(AddBackslash(ExistingDairyOSDataRoot()) + 'backups', 0);

  ConfiguredRoot := GetEnv('DAIRYOS_BACKUP_MIRROR_ROOT');
  if ConfiguredRoot <> '' then
    ScanBackupDirectory(ConfiguredRoot, 0);
  ConfiguredRoot := GetEnv('DAIRYOS_RECOVERY_ROOT');
  if ConfiguredRoot <> '' then
    ScanBackupDirectory(ConfiguredRoot, 0);

end;

function DetectExistingDairyOSData(): Boolean;
var
  Root: String;
begin
  Root := ExistingDairyOSDataRoot();
  Result :=
    FileExists(Root + '\installation_state.json') or
    FileExists(Root + '\lifecycle.json') or
    FileExists(Root + '\postgres\runtime.json') or
    FileExists(Root + '\postgres\security.json') or
    DirExists(Root + '\postgres\data') or
    DirectoryHasEntries(Root + '\storage') or
    FileExists(ExpandConstant('{localappdata}\DairyOS-installation-state.json'));
end;

procedure InitializeWizard();
var
  I: Integer;
begin
  SelectedDataRoot := ExistingDairyOSDataRoot();
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
      'Keep the current farm, restore one selected recovery point, or create a separate empty farm.',
      True,
      True
    );
    DataChoicePage.Add('Keep existing farm data (recommended)');
    DataChoicePage.Add('Restore from a verified backup');
    DataChoicePage.Add('Create a separate empty farm (preserve existing data)');
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
    SelectedDataRoot := SelectNewDairyOSDataRoot();
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
    SelectedDataRoot := SelectNewDairyOSDataRoot();
  end;

  CleanConfirmationPage := CreateInputQueryPage(
    DataChoicePage.ID,
    'Confirm new empty DairyOS farm',
    'This action creates a separate empty farm data root.',
    'Type the exact phrase below to confirm. Existing DairyOS records, logs and backups will not be deleted or changed.'
  );
  CleanConfirmationPage.Add(
    'Type CLEAN INSTALL DAIRYOS DATA to confirm a new farm:',
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
        SelectedDataRoot := ExistingDairyOSDataRoot();
        exit;
      end;

      if DataChoicePage.SelectedValueIndex = 1 then
      begin
        SelectedInstallMode := 'restore';
        SelectedDataRoot := ExistingDairyOSDataRoot();
        exit;
      end;

      SelectedInstallMode := 'clean';
      SelectedDataRoot := AllocateNewDairyOSDataRoot();
      exit;
    end;
    if (RestoreChoiceIndex >= 0) and
       (DataChoicePage.SelectedValueIndex = RestoreChoiceIndex) then
    begin
      SelectedInstallMode := 'restore';
      SelectedDataRoot := ExistingDairyOSDataRoot();
      exit;
    end;
    SelectedInstallMode := 'new';
    SelectedDataRoot := SelectNewDairyOSDataRoot();
    exit;
  end;

  if CurPageID = CleanConfirmationPage.ID then
  begin
    if CleanConfirmationPage.Values[0] <> 'CLEAN INSTALL DAIRYOS DATA' then
    begin
      MsgBox(
        'New empty farm was not confirmed. Existing farm data was not changed.',
        mbError,
        MB_OK
      );
      Result := False;
      exit;
    end;
    CleanConfirmationAccepted := True;
    SelectedInstallMode := 'clean';
    if SelectedDataRoot = ExistingDairyOSDataRoot() then
      SelectedDataRoot := AllocateNewDairyOSDataRoot();
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

function InitializeUninstall(): Boolean;
begin
  Log('DairyOS uninstall: beginning straightforward keep-data uninstall.');
  Result := StopInstalledDairyOSForUninstall();
end;
