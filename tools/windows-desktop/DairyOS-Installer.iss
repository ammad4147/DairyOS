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
WizardSizePercent=140,135
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
Name: "{autoprograms}\DairyOS Operator Manual"; Filename: "{app}\Documentation\DairyOS-Operator-Manual.html"; WorkingDir: "{app}\Documentation"
Name: "{autodesktop}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"

[Dirs]
Name: "{commonappdata}\DairyOS"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch DairyOS"; Flags: nowait postinstall skipifsilent; Check: ShouldLaunchDairyOS
Filename: "{app}\DairyOS-Admin.exe"; Parameters: "--restore-mode"; Description: "Choose a verified backup in DairyOS Administration"; Flags: nowait postinstall skipifsilent; Check: ShouldLaunchAdminAfterInstall

[UninstallDelete]
; Deliberately empty. ProgramData contains farm data, the private PostgreSQL
; cluster, backups, logs and protected runtime state and must survive uninstall.


[Code]
var
  DataChoicePage: TWizardPage;
  UseExistingRadio: TRadioButton;
  RestoreRadio: TRadioButton;
  FreshRadio: TRadioButton;
  ExistingDataDetected: Boolean;
  RestoreRequested: Boolean;

function DairyOSDataRoot(): String;
begin
  Result := ExpandConstant('{commonappdata}\DairyOS');
end;


procedure ProvisionLifecycleState();
var
  AdminExe: String;
  Params: String;
  ResultCode: Integer;
begin
  AdminExe := ExpandConstant('{app}\DairyOS-Admin.exe');
  if not FileExists(AdminExe) then
    RaiseException('DairyOS-Admin.exe is missing; lifecycle state cannot be initialized.');

  Params :=
    '--lifecycle-install ' +
    '--installation-root "' + ExpandConstant('{app}') + '" ' +
    '--data-root "' + DairyOSDataRoot() + '"';

  if (not Exec(
    AdminExe,
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
    elevated, while normal DairyOS Administration operates without elevation.
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
  RestoreDetail: TNewStaticText;
  Caution: TNewStaticText;
begin
  ExistingDataDetected := DetectExistingDairyOSData();
  RestoreRequested := False;

  DataChoicePage := CreateCustomPage(
    wpSelectDir,
    'DairyOS Farm Data',
    'Choose how DairyOS should use farm data on this computer.'
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

    UseExistingRadio := TRadioButton.Create(DataChoicePage);
    UseExistingRadio.Parent := DataChoicePage.Surface;
    UseExistingRadio.Left := ScaleX(12);
    UseExistingRadio.Top := Intro.Top + Intro.Height + ScaleY(20);
    UseExistingRadio.Width := DataChoicePage.SurfaceWidth - ScaleX(24);
    UseExistingRadio.Height := ScaleY(24);
    UseExistingRadio.Font.Name := 'Segoe UI';
    UseExistingRadio.Font.Size := 11;
    UseExistingRadio.Font.Style := [fsBold];
    UseExistingRadio.Caption := 'Use existing DairyOS data';
    UseExistingRadio.Checked := True;

    ExistingDetail := TNewStaticText.Create(DataChoicePage);
    ExistingDetail.Parent := DataChoicePage.Surface;
    ExistingDetail.Left := ScaleX(34);
    ExistingDetail.Top := UseExistingRadio.Top + UseExistingRadio.Height + ScaleY(4);
    ExistingDetail.Width := DataChoicePage.SurfaceWidth - ScaleX(48);
    ExistingDetail.AutoSize := False;
    ExistingDetail.WordWrap := True;
    ExistingDetail.Font.Name := 'Segoe UI';
    ExistingDetail.Font.Size := 10;
    ExistingDetail.Caption :=
      'Reinstall the DairyOS application and reconnect to the existing farm database. ' +
      'Existing farm data is retained.';
    ExistingDetail.AdjustHeight();

    RestoreRadio := TRadioButton.Create(DataChoicePage);
    RestoreRadio.Parent := DataChoicePage.Surface;
    RestoreRadio.Left := ScaleX(12);
    RestoreRadio.Top := ExistingDetail.Top + ExistingDetail.Height + ScaleY(22);
    RestoreRadio.Width := DataChoicePage.SurfaceWidth - ScaleX(24);
    RestoreRadio.Height := ScaleY(24);
    RestoreRadio.Font.Name := 'Segoe UI';
    RestoreRadio.Font.Size := 11;
    RestoreRadio.Font.Style := [fsBold];
    RestoreRadio.Caption := 'Restore from a verified DairyOS backup';

    RestoreDetail := TNewStaticText.Create(DataChoicePage);
    RestoreDetail.Parent := DataChoicePage.Surface;
    RestoreDetail.Left := ScaleX(34);
    RestoreDetail.Top := RestoreRadio.Top + RestoreRadio.Height + ScaleY(4);
    RestoreDetail.Width := DataChoicePage.SurfaceWidth - ScaleX(48);
    RestoreDetail.AutoSize := False;
    RestoreDetail.WordWrap := True;
    RestoreDetail.Font.Name := 'Segoe UI';
    RestoreDetail.Font.Size := 10;
    RestoreDetail.Caption :=
      'Install DairyOS first, then open authenticated DairyOS Administration ' +
      'to choose from automatically discovered verified backups, newest first. ' +
      'Full farm snapshots and database-only backups are labelled separately.';
    RestoreDetail.AdjustHeight();
  end
  else
  begin
    Intro.Caption := 'No existing DairyOS farm data was detected on this computer.';
    Intro.AdjustHeight();

    FreshRadio := TRadioButton.Create(DataChoicePage);
    FreshRadio.Parent := DataChoicePage.Surface;
    FreshRadio.Left := ScaleX(12);
    FreshRadio.Top := Intro.Top + Intro.Height + ScaleY(20);
    FreshRadio.Width := DataChoicePage.SurfaceWidth - ScaleX(24);
    FreshRadio.Height := ScaleY(24);
    FreshRadio.Font.Name := 'Segoe UI';
    FreshRadio.Font.Size := 11;
    FreshRadio.Font.Style := [fsBold];
    FreshRadio.Caption := 'Start a new DairyOS farm';
    FreshRadio.Checked := True;

    ExistingDetail := TNewStaticText.Create(DataChoicePage);
    ExistingDetail.Parent := DataChoicePage.Surface;
    ExistingDetail.Left := ScaleX(34);
    ExistingDetail.Top := FreshRadio.Top + FreshRadio.Height + ScaleY(4);
    ExistingDetail.Width := DataChoicePage.SurfaceWidth - ScaleX(48);
    ExistingDetail.AutoSize := False;
    ExistingDetail.WordWrap := True;
    ExistingDetail.Font.Name := 'Segoe UI';
    ExistingDetail.Font.Size := 10;
    ExistingDetail.Caption :=
      'Create a new DairyOS farm database on this computer.';
    ExistingDetail.AdjustHeight();

    RestoreRadio := TRadioButton.Create(DataChoicePage);
    RestoreRadio.Parent := DataChoicePage.Surface;
    RestoreRadio.Left := ScaleX(12);
    RestoreRadio.Top := ExistingDetail.Top + ExistingDetail.Height + ScaleY(22);
    RestoreRadio.Width := DataChoicePage.SurfaceWidth - ScaleX(24);
    RestoreRadio.Height := ScaleY(24);
    RestoreRadio.Font.Name := 'Segoe UI';
    RestoreRadio.Font.Size := 11;
    RestoreRadio.Font.Style := [fsBold];
    RestoreRadio.Caption := 'Restore from a verified DairyOS backup';

    RestoreDetail := TNewStaticText.Create(DataChoicePage);
    RestoreDetail.Parent := DataChoicePage.Surface;
    RestoreDetail.Left := ScaleX(34);
    RestoreDetail.Top := RestoreRadio.Top + RestoreRadio.Height + ScaleY(4);
    RestoreDetail.Width := DataChoicePage.SurfaceWidth - ScaleX(48);
    RestoreDetail.AutoSize := False;
    RestoreDetail.WordWrap := True;
    RestoreDetail.Font.Name := 'Segoe UI';
    RestoreDetail.Font.Size := 10;
    RestoreDetail.Caption :=
      'After installation, Administration automatically lists verified backups. ' +
      'Choose a full farm snapshot or a clearly labelled database-only backup.';
    RestoreDetail.AdjustHeight();
  end;

  Caution := TNewStaticText.Create(DataChoicePage);
  Caution.Parent := DataChoicePage.Surface;
  Caution.Left := ScaleX(12);
  Caution.Top := RestoreDetail.Top + RestoreDetail.Height + ScaleY(28);
  Caution.Width := DataChoicePage.SurfaceWidth - ScaleX(24);
  Caution.AutoSize := False;
  Caution.WordWrap := True;
  Caution.Font.Name := 'Segoe UI';
  Caution.Font.Size := 10;
  Caution.Font.Style := [fsBold];
  Caution.Caption :=
    'IMPORTANT' + #13#10 +
    'The installer will not delete or overwrite an existing DairyOS farm database. ' +
    'Permanent data deletion is available only through authenticated DairyOS Administration.';
  Caution.AdjustHeight();
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (DataChoicePage <> nil) and (CurPageID = DataChoicePage.ID) then
    RestoreRequested := (RestoreRadio <> nil) and RestoreRadio.Checked;
end;

function ShouldLaunchDairyOS(): Boolean;
begin
  Result := not RestoreRequested;
end;

function ShouldLaunchAdminAfterInstall(): Boolean;
begin
  Result := RestoreRequested;
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

  { Stop only DairyOS-owned executable images after PostgreSQL has shut down.
    This releases the frozen runtime files before Inno Setup begins deletion. }
  Exec(
    ExpandConstant('{sys}\taskkill.exe'),
    '/F /T /IM DairyOS.exe',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );
  Exec(
    ExpandConstant('{sys}\taskkill.exe'),
    '/F /T /IM DairyOS-Admin.exe',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );
  Exec(
    ExpandConstant('{sys}\taskkill.exe'),
    '/F /T /IM DairyOSBackup.exe',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

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

  Sleep(1000);
  Result := True;
end;

function InitializeUninstall(): Boolean;
var
  Choice: Integer;
  AdminExe: String;
  ResultCode: Integer;
begin
  Result := True;

  if IsSilentUninstall() then
  begin
    Result := StopInstalledDairyOSForUninstall();
    exit;
  end;

  Choice := MsgBox(
    'Choose how to proceed with DairyOS uninstall:' + #13#10 + #13#10 +
    'YES - KEEP DATA AND UNINSTALL' + #13#10 +
    'Removes the DairyOS application but keeps the farm database and backups.' + #13#10 + #13#10 +
    'NO - CREATE VERIFIED BACKUP FIRST' + #13#10 +
    'Cancels uninstall and opens DairyOS Administration.' + #13#10 + #13#10 +
    'CANCEL - DO NOT UNINSTALL' + #13#10 + #13#10 +
    'Permanent data deletion is available only through authenticated DairyOS Administration.',
    mbConfirmation,
    MB_YESNOCANCEL
  );

  if Choice = IDYES then
  begin
    Result := StopInstalledDairyOSForUninstall();
    exit;
  end;

  Result := False;

  if Choice = IDNO then
  begin
    AdminExe := ExpandConstant('{app}\DairyOS-Admin.exe');
    if FileExists(AdminExe) then
    begin
      if not Exec(AdminExe, '', ExpandConstant('{app}'), SW_SHOWNORMAL, ewNoWait, ResultCode) then
        MsgBox('DairyOS Administration could not be opened. Uninstall has been cancelled.', mbError, MB_OK);
    end
    else
      MsgBox(
        'DairyOS Administration is not installed. Uninstall has been cancelled so data remains untouched.',
        mbError,
        MB_OK
      );
  end;
end;
