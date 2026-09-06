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
Name: "{autoprograms}\DairyOS Operator Manual"; Filename: "{app}\Documentation\DairyOS-Operator-Manual.html"; WorkingDir: "{app}\Documentation"
Name: "{autodesktop}\DairyOS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"

[Dirs]
Name: "{commonappdata}\DairyOS"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch DairyOS"; Flags: nowait postinstall skipifsilent; Check: ShouldLaunchDairyOS
Filename: "{app}\DairyOS-Admin.exe"; Description: "Open DairyOS Administration to restore verified backup"; Flags: nowait postinstall skipifsilent; Check: ShouldLaunchAdminAfterInstall

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
begin
  ExistingDataDetected := DetectExistingDairyOSData();
  RestoreRequested := False;

  DataChoicePage := CreateCustomPage(
    wpSelectDir,
    'DairyOS Farm Data',
    'Choose how this installation should use DairyOS farm data.'
  );

  Intro := TNewStaticText.Create(DataChoicePage);
  Intro.Parent := DataChoicePage.Surface;
  Intro.Left := 0;
  Intro.Top := 8;
  Intro.Width := DataChoicePage.SurfaceWidth;
  Intro.AutoSize := False;
  Intro.WordWrap := True;
  Intro.Height := 58;

  if ExistingDataDetected then
  begin
    Intro.Caption :=
      'Existing DairyOS data was detected at ' + DairyOSDataRoot() + '. ' +
      'The installer will not delete or replace it. Choose whether to reconnect ' +
      'to that data or open the authenticated Admin Tool after installation to restore a verified backup.';

    UseExistingRadio := TRadioButton.Create(DataChoicePage);
    UseExistingRadio.Parent := DataChoicePage.Surface;
    UseExistingRadio.Left := 0;
    UseExistingRadio.Top := 78;
    UseExistingRadio.Width := DataChoicePage.SurfaceWidth;
    UseExistingRadio.Caption := 'Use existing DairyOS data (recommended)';
    UseExistingRadio.Checked := True;

    RestoreRadio := TRadioButton.Create(DataChoicePage);
    RestoreRadio.Parent := DataChoicePage.Surface;
    RestoreRadio.Left := 0;
    RestoreRadio.Top := 108;
    RestoreRadio.Width := DataChoicePage.SurfaceWidth;
    RestoreRadio.Caption := 'Restore a verified backup using DairyOS Administration after installation';
  end
  else
  begin
    Intro.Caption :=
      'No existing DairyOS farm data was detected at ' + DairyOSDataRoot() + '. ' +
      'Choose a new farm installation or restore a verified DairyOS backup through the authenticated Admin Tool.';

    FreshRadio := TRadioButton.Create(DataChoicePage);
    FreshRadio.Parent := DataChoicePage.Surface;
    FreshRadio.Left := 0;
    FreshRadio.Top := 78;
    FreshRadio.Width := DataChoicePage.SurfaceWidth;
    FreshRadio.Caption := 'Start a new DairyOS farm';
    FreshRadio.Checked := True;

    RestoreRadio := TRadioButton.Create(DataChoicePage);
    RestoreRadio.Parent := DataChoicePage.Surface;
    RestoreRadio.Left := 0;
    RestoreRadio.Top := 108;
    RestoreRadio.Width := DataChoicePage.SurfaceWidth;
    RestoreRadio.Caption := 'Restore a verified backup using DairyOS Administration after installation';
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (DataChoicePage <> nil) and (CurPageID = DataChoicePage.ID) then
  begin
    RestoreRequested := (RestoreRadio <> nil) and RestoreRadio.Checked;
    if ExistingDataDetected and (UseExistingRadio <> nil) and UseExistingRadio.Checked then
    begin
      MsgBox(
        'Existing DairyOS farm data will be retained and reused. The installer will replace application files only.',
        mbInformation,
        MB_OK
      );
    end;
    if RestoreRequested then
    begin
      MsgBox(
        'After installation, DairyOS Administration will open. Authenticate there and use Restore Verified Backup. ' +
        'The installer itself will not overwrite farm data.',
        mbInformation,
        MB_OK
      );
    end;
  end;
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

function InitializeUninstall(): Boolean;
var
  Choice: Integer;
  AdminExe: String;
  ResultCode: Integer;
begin
  Result := True;

  if IsSilentUninstall() then
    exit;

  Choice := MsgBox(
    'DairyOS farm data and the private database are retained by default when the application is uninstalled.' + #13#10 + #13#10 +
    'YES: continue uninstall and KEEP all DairyOS data.' + #13#10 +
    'NO: cancel uninstall and open DairyOS Administration so you can create a verified backup first.' + #13#10 +
    'CANCEL: cancel uninstall.' + #13#10 + #13#10 +
    'Permanent data deletion is available only through the authenticated DairyOS Administration purge operation.',
    mbConfirmation,
    MB_YESNOCANCEL
  );

  if Choice = IDYES then
  begin
    Result := True;
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
