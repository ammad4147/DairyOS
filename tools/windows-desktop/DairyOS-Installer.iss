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
  DataChoicePage: TInputOptionWizardPage;
  FarmChoicePage: TInputOptionWizardPage;
  CleanConfirmationPage: TInputQueryWizardPage;
  BackupChoicePage: TInputOptionWizardPage;
  ExistingDataDetected: Boolean;
  SelectedInstallMode: String;
  SelectedBackupPath: String;
  CleanConfirmationAccepted: Boolean;
  KeepChoiceIndex: Integer;
  RestoreChoiceIndex: Integer;
  BackupCandidatePaths: array of String;
  BackupCandidateTimes: array of String;
  FarmCandidatePaths: array of String;
  SelectedDataRoot: String;

procedure StageInstallationChoice(); forward;

function CanonicalDairyOSDataRoot(): String;
begin
  Result := ExpandConstant('{commonappdata}\DairyOS');
end;

function ConfiguredDairyOSDataRoot(): String;
var
  ConfiguredRoot: String;
begin
  { Return only a genuine surviving machine-level farm pointer.
    An absent pointer is not equivalent to the canonical fallback. }
  Result := '';

  if RegQueryStringValue(
    HKLM,
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
    'DAIRYOS_DATA_DIR',
    ConfiguredRoot
  ) and (ConfiguredRoot <> '') then
    Result := ConfiguredRoot;
end;

function ExistingDairyOSDataRoot(): String;
var
  ConfiguredRoot: String;
begin
  { Runtime path authority retains the historical canonical fallback.
    Farm identity/discovery must use ConfiguredDairyOSDataRoot() instead. }
  ConfiguredRoot := ConfiguredDairyOSDataRoot();

  if ConfiguredRoot <> '' then
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
    GetDateTimeString('yyyymmdd-hhnnss', '-', ':');
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

procedure ProvisionInstallationChoiceAcl();
var
  PendingChoicePath: String;
  IcaclsExe: String;
  Params: String;
  ResultCode: Integer;
begin
  PendingChoicePath :=
    DairyOSDataRoot('') + '\pending-installation-choice.json';

  { StageInstallationChoice runs elevated and creates this one-shot control
    file. The normal, non-elevated supervisor must be able to consume it and
    atomically replace it if a recovery action fails. Grant Modify only to
    this control file; do not broaden permissions to PostgreSQL or farm data. }
  if not FileExists(PendingChoicePath) then
    exit;

  IcaclsExe := ExpandConstant('{sys}\icacls.exe');
  Params := '"' + PendingChoicePath + '" /grant:r *S-1-5-32-545:(M)';

  if (not Exec(
    IcaclsExe,
    Params,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  )) or (ResultCode <> 0) then
    RaiseException(
      'DairyOS installation-choice permissions could not be provisioned. ' +
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
    StageInstallationChoice();
    ProvisionInstallationChoiceAcl();
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

function IsRecognizedDairyOSFarmRoot(const Root: String): Boolean;
begin
  { A directory name alone is never sufficient. Accept only roots containing
    recognizable DairyOS-owned lifecycle, PostgreSQL or operational state.
    A stopped PostgreSQL cluster remains valid after uninstall, so no running
    postmaster.pid is required. }
  Result :=
    DirExists(Root) and
    (
      FileExists(AddBackslash(Root) + 'installation_state.json') or
      FileExists(AddBackslash(Root) + 'lifecycle.json') or
      FileExists(AddBackslash(Root) + 'postgres\runtime.json') or
      FileExists(AddBackslash(Root) + 'postgres\security.json') or
      DirExists(AddBackslash(Root) + 'postgres\data') or
      DirectoryHasEntries(AddBackslash(Root) + 'storage')
    );
end;

procedure AddFarmCandidate(const Candidate: String);
var
  I: Integer;
  Normalized: String;
begin
  Normalized := Candidate;
  while (Length(Normalized) > 3) and
        (Normalized[Length(Normalized)] = '\') do
    Delete(Normalized, Length(Normalized), 1);

  if (Normalized = '') or (not IsRecognizedDairyOSFarmRoot(Normalized)) then
    exit;

  for I := 0 to GetArrayLength(FarmCandidatePaths) - 1 do
    if Lowercase(FarmCandidatePaths[I]) = Lowercase(Normalized) then
      exit;

  SetArrayLength(FarmCandidatePaths, GetArrayLength(FarmCandidatePaths) + 1);
  FarmCandidatePaths[GetArrayLength(FarmCandidatePaths) - 1] := Normalized;
end;

procedure ScanKnownFarmRoots();
var
  CommonDataRoot: String;
  ConfiguredRoot: String;
  Candidate: String;
  FindRec: TFindRec;
begin
  SetArrayLength(FarmCandidatePaths, 0);

  { A genuine surviving configured root remains a candidate, but canonical
    fallback is never misrepresented as configured identity. Preserved
    canonical and DairyOS-New-* roots are discovered independently below. }
  ConfiguredRoot := ConfiguredDairyOSDataRoot();
  if ConfiguredRoot <> '' then
    AddFarmCandidate(ConfiguredRoot);

  CommonDataRoot := ExpandConstant('{commonappdata}');

  { Canonical DairyOS root is always checked explicitly. }
  AddFarmCandidate(AddBackslash(CommonDataRoot) + 'DairyOS');

  { DairyOS itself creates sibling roots with this exact prefix. Restrict the
    scan to that owned namespace; never enumerate arbitrary drives or unrelated
    ProgramData directories as farm candidates. }
  if FindFirst(AddBackslash(CommonDataRoot) + 'DairyOS-New-*', FindRec) then
  try
    repeat
      if (FindRec.Name <> '.') and (FindRec.Name <> '..') then
      begin
        Candidate := AddBackslash(CommonDataRoot) + FindRec.Name;
        if DirExists(Candidate) then
          AddFarmCandidate(Candidate);
      end;
    until not FindNext(FindRec);
  finally
    FindClose(FindRec);
  end;
end;

function SelectedFarmCandidate(): String;
begin
  Result := '';
  if (FarmChoicePage <> nil) and
     (FarmChoicePage.SelectedValueIndex >= 0) and
     (FarmChoicePage.SelectedValueIndex < GetArrayLength(FarmCandidatePaths)) then
    Result := FarmCandidatePaths[FarmChoicePage.SelectedValueIndex];
end;

procedure AddBackupCandidate(const Candidate: String);
var
  I: Integer;
  InsertAt: Integer;
  Normalized: String;
  ManifestPath: String;
  ManifestText: AnsiString;
  CreatedAt: String;
  StartAt: Integer;
  EndAt: Integer;
  ManifestLoaded: Boolean;
  CandidateName: String;
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

  { DairyOS backup folders carry an immutable UTC timestamp in their name.
    Prefer that operator-safe identity: it avoids locale parsing and remains
    available even while a manifest is being written. }
  CandidateName := ExtractFileName(Normalized);
  CreatedAt := '';
  if (Length(CandidateName) >= 16) and
     (CandidateName[9] = 'T') and
     (CandidateName[16] = 'Z') then
    CreatedAt :=
      Copy(CandidateName, 1, 4) + '-' +
      Copy(CandidateName, 5, 2) + '-' +
      Copy(CandidateName, 7, 2) + 'T' +
      Copy(CandidateName, 10, 2) + ':' +
      Copy(CandidateName, 12, 2) + ':' +
      Copy(CandidateName, 14, 2);

  { File-based recovery points may not have a timestamped folder name. Use
    their manifest timestamp when available, otherwise sort them last and
    label them clearly instead of inventing a date. }
  ManifestPath := AddBackslash(Normalized) + 'backup.json';
  if (CreatedAt = '') and FileExists(ManifestPath) then
  begin
    ManifestLoaded := LoadStringFromFile(ManifestPath, ManifestText);
    if ManifestLoaded then
    begin
      StartAt := Pos('"created_at"', ManifestText);
      if StartAt > 0 then
      begin
        StartAt := StartAt + 11 + Pos('"', Copy(ManifestText, StartAt + 11, Length(ManifestText)));
        if StartAt > 0 then
        begin
          StartAt := StartAt + 1;
          EndAt := StartAt - 1 + Pos('"', Copy(ManifestText, StartAt, Length(ManifestText)));
          if EndAt > StartAt then
            CreatedAt := Copy(ManifestText, StartAt, EndAt - StartAt);
        end;
      end;
    end;
  end;
  if CreatedAt = '' then
    CreatedAt := '0000-00-00T00:00:00';

  InsertAt := GetArrayLength(BackupCandidatePaths);
  for I := 0 to GetArrayLength(BackupCandidateTimes) - 1 do
    if CreatedAt > BackupCandidateTimes[I] then
    begin
      InsertAt := I;
      break;
    end;

  SetArrayLength(BackupCandidatePaths, GetArrayLength(BackupCandidatePaths) + 1);
  SetArrayLength(BackupCandidateTimes, GetArrayLength(BackupCandidateTimes) + 1);
  for I := GetArrayLength(BackupCandidatePaths) - 1 downto InsertAt + 1 do
  begin
    BackupCandidatePaths[I] := BackupCandidatePaths[I - 1];
    BackupCandidateTimes[I] := BackupCandidateTimes[I - 1];
  end;
  BackupCandidatePaths[InsertAt] := Normalized;
  BackupCandidateTimes[InsertAt] := CreatedAt;
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
  I: Integer;
begin
  SetArrayLength(BackupCandidatePaths, 0);
  SetArrayLength(BackupCandidateTimes, 0);

  { Every validated DairyOS farm may own preserved backups. Enumerate those
    owned roots, then retain the existing explicitly configured mirror and
    recovery locations. Only explicitly owned/declared recovery locations are
    inspected; arbitrary historical backup trees and unrelated drives are not
    searched or treated as active farm data. }
  for I := 0 to GetArrayLength(FarmCandidatePaths) - 1 do
    ScanBackupDirectory(
      AddBackslash(FarmCandidatePaths[I]) + 'backups',
      0
    );

  ConfiguredRoot := GetEnv('DAIRYOS_BACKUP_MIRROR_ROOT');
  if ConfiguredRoot <> '' then
    ScanBackupDirectory(ConfiguredRoot, 0);

  ConfiguredRoot := GetEnv('DAIRYOS_RECOVERY_ROOT');
  if ConfiguredRoot <> '' then
    ScanBackupDirectory(ConfiguredRoot, 0);
end;

function DetectExistingDairyOSData(): Boolean;
begin
  { Only validated selectable farm roots establish preserved farm data.
    A stale installation marker is not itself farm data and must never expose
    Keep/Restore destination choices without a valid farm root. }
  Result := GetArrayLength(FarmCandidatePaths) > 0;
end;

procedure InitializeWizard();
var
  I: Integer;
  ConfiguredRoot: String;
  CandidateLabel: String;
  InitialFarmIndex: Integer;
begin
  ScanKnownFarmRoots();
  ExistingDataDetected := DetectExistingDairyOSData();
  ScanKnownBackupRoots();

  SelectedBackupPath := '';
  SelectedDataRoot := '';
  CleanConfirmationAccepted := False;
  KeepChoiceIndex := -1;
  RestoreChoiceIndex := -1;
  InitialFarmIndex := -1;
  ConfiguredRoot := ConfiguredDairyOSDataRoot();

  DataChoicePage := CreateInputOptionPage(
    wpSelectDir,
    'DairyOS Installation',
    'Choose how to start DairyOS.',
    'Choose New Installation for a fresh farm, Continue with Existing Farm to use saved farm data without restoring it, or Restore to Verified Backup to bring back a saved recovery point.',
    True,
    True
  );
  DataChoicePage.Add('New Installation');

  if ExistingDataDetected then
  begin
    DataChoicePage.Add('Continue with Existing Farm');
    KeepChoiceIndex := 1;
  end;

  DataChoicePage.Add('Restore to Verified Backup');
  RestoreChoiceIndex := DataChoicePage.CheckListBox.Items.Count - 1;
  DataChoicePage.SelectedValueIndex := 0;
  SelectedInstallMode := 'new';

  if GetArrayLength(FarmCandidatePaths) > 0 then
  begin
    FarmChoicePage := CreateInputOptionPage(
      DataChoicePage.ID,
      'DairyOS Farm',
      'Choose the existing DairyOS farm.',
      'Select the exact saved DairyOS farm to continue with or restore.',
      True,
      True
    );

    for I := 0 to GetArrayLength(FarmCandidatePaths) - 1 do
    begin
      if Lowercase(FarmCandidatePaths[I]) = Lowercase(ConfiguredRoot) then
        InitialFarmIndex := I;

      if Lowercase(FarmCandidatePaths[I]) =
         Lowercase(CanonicalDairyOSDataRoot()) then
        CandidateLabel :=
          'Farm data: ' + FarmCandidatePaths[I] + ' [Primary farm]'
      else
        CandidateLabel :=
          'Farm data: ' + FarmCandidatePaths[I] +
          ' [Preserved separate farm]';

      if (ConfiguredRoot <> '') and
         (Lowercase(FarmCandidatePaths[I]) = Lowercase(ConfiguredRoot)) then
        CandidateLabel := CandidateLabel + ' [Currently configured]';

      FarmChoicePage.Add(CandidateLabel);
    end;

    { A surviving configured pointer identifies an exact active farm.
      Otherwise one discovered farm is unambiguous. Multiple preserved farms
      with no surviving pointer require an explicit operator selection. }
    if InitialFarmIndex >= 0 then
      FarmChoicePage.SelectedValueIndex := InitialFarmIndex
    else if GetArrayLength(FarmCandidatePaths) = 1 then
      FarmChoicePage.SelectedValueIndex := 0
    else
      FarmChoicePage.SelectedValueIndex := -1;
  end
  else
    FarmChoicePage := nil;

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

  if FarmChoicePage <> nil then
    BackupChoicePage := CreateInputOptionPage(
      FarmChoicePage.ID,
      'Saved Backups',
      'Choose a backup by date and time.',
      'The newest backup is first. DairyOS checks the selected backup again before restoring it.',
      True,
      True
    )
  else
    BackupChoicePage := CreateInputOptionPage(
      DataChoicePage.ID,
      'Saved Backups',
      'Choose a backup by date and time.',
      'The newest backup is first. DairyOS checks the selected backup again before restoring it.',
      True,
      True
    );

  if GetArrayLength(BackupCandidatePaths) = 0 then
    BackupChoicePage.Add(
      'No backup candidates were found in the known DairyOS backup locations.'
    )
  else
  begin
    for I := 0 to GetArrayLength(BackupCandidatePaths) - 1 do
      if BackupCandidateTimes[I] = '0000-00-00T00:00:00' then
        BackupChoicePage.Add('Date unavailable - Backup')
      else
        BackupChoicePage.Add(
          Copy(BackupCandidateTimes[I], 1, 10) + ' ' +
          Copy(BackupCandidateTimes[I], 12, 5) + ' - Backup'
        );
    BackupChoicePage.SelectedValueIndex := 0;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  FarmRoot: String;
begin
  Result := True;

  if CurPageID = DataChoicePage.ID then
  begin
    CleanConfirmationAccepted := False;
    SelectedBackupPath := '';

    if (KeepChoiceIndex >= 0) and
       (DataChoicePage.SelectedValueIndex = KeepChoiceIndex) then
    begin
      SelectedInstallMode := 'keep';
      SelectedDataRoot := '';
      exit;
    end;

    if (RestoreChoiceIndex >= 0) and
       (DataChoicePage.SelectedValueIndex = RestoreChoiceIndex) then
    begin
      SelectedInstallMode := 'restore';

      { When preserved farms exist, the exact destination is selected on the
        farm page. Without a preserved destination, Restore targets a newly
        allocated DairyOS-owned empty root rather than the canonical fallback. }
      if FarmChoicePage = nil then
        SelectedDataRoot := SelectNewDairyOSDataRoot()
      else
        SelectedDataRoot := '';
      exit;
    end;

    SelectedInstallMode := 'new';
    SelectedDataRoot := SelectNewDairyOSDataRoot();
    exit;
  end;

  if (FarmChoicePage <> nil) and (CurPageID = FarmChoicePage.ID) then
  begin
    FarmRoot := SelectedFarmCandidate();

    if FarmRoot = '' then
    begin
      MsgBox(
        'Select the exact DairyOS farm data path to continue. No farm has been changed.',
        mbError,
        MB_OK
      );
      Result := False;
      exit;
    end;

    SelectedDataRoot := FarmRoot;
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

    if (SelectedDataRoot = '') or
       IsRecognizedDairyOSFarmRoot(SelectedDataRoot) then
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

    if (BackupChoicePage.SelectedValueIndex < 0) or
       (BackupChoicePage.SelectedValueIndex >=
        GetArrayLength(BackupCandidatePaths)) then
    begin
      MsgBox(
        'Select the exact DairyOS recovery point to restore.',
        mbError,
        MB_OK
      );
      Result := False;
      exit;
    end;

    SelectedInstallMode := 'restore';
    SelectedBackupPath :=
      BackupCandidatePaths[BackupChoicePage.SelectedValueIndex];
    exit;
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;

  if (FarmChoicePage <> nil) and (PageID = FarmChoicePage.ID) then
    Result :=
      (DataChoicePage.SelectedValueIndex <> KeepChoiceIndex) and
      (DataChoicePage.SelectedValueIndex <> RestoreChoiceIndex);

  if PageID = CleanConfirmationPage.ID then
    Result :=
      (not ExistingDataDetected) or
      (SelectedInstallMode <> 'clean');

  if PageID = BackupChoicePage.ID then
    Result :=
      (RestoreChoiceIndex < 0) or
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
