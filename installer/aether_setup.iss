; Aether AI Assistant Installer Script
; Generated for Inno Setup Compiler

[Setup]
AppName=Aether AI Assistant
AppVersion=1.0.0
DefaultDirName={autopf}\Aether
DefaultGroupName=Aether
OutputBaseFilename=Aether-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\aether.ico
SetupIconFile=aether.ico
LicenseFile=LICENSE.txt
InfoBeforeFile=README.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Languages\English.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"
Name: "quicklaunchicon"; Description: "Create a quick launch icon"; GroupDescription: "Additional icons:"
Name: "autostart"; Description: "Start Aether with Windows"; GroupDescription: "Additional options:"

[Files]
; Main application files
Source: "..\assistant\planner\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assistant\planner\pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assistant\planner\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: ignoreversion
Source: "..\assistant\docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; DestName: "README.txt"; Flags: ignoreversion
Source: "aether.ico"; DestDir: "{app}"; Flags: ignoreversion

; Python virtual environment (if pre-built)
; Source: ".venv\*"; DestDir: "{app}\.venv"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Aether Dashboard"; Filename: "http://127.0.0.1:8001"; IconFilename: "{app}\aether.ico"
Name: "{group}\Start Aether"; Filename: "{app}\start_aether.bat"; IconFilename: "{app}\aether.ico"
Name: "{group}\Stop Aether"; Filename: "{app}\stop_aether.bat"; IconFilename: "{app}\aether.ico"
Name: "{group}\Uninstall Aether"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Aether"; Filename: "{app}\start_aether.bat"; Tasks: desktopicon; IconFilename: "{app}\aether.ico"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Aether"; Filename: "{app}\start_aether.bat"; Tasks: quicklaunchicon; IconFilename: "{app}\aether.ico"

[Run]
Filename: "{app}\start_aether.bat"; Description: "Start Aether after installation"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\.venv"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\data"

[Code]
function IsPythonInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if not RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', Result) then
  begin
    if not RegQueryStringValue(HKLM, 'SOFTWARE\Python\PythonCore\3.12\InstallPath', '', Result) then
    begin
      Result := False;
    end;
  end;
end;

function IsOllamaInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  Result := FileExists(ExpandConstant('{pf)}\Ollama\ollama.exe')) or
            FileExists(ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe'));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Install Python if not present
    if not IsPythonInstalled then
    begin
      if MsgBox('Python 3.11+ is required for Aether to function. Would you like to download and install it now?', mbConfirmation, MB_YESNO) = IDYES then
      begin
        ShellExec('open', 'https://www.python.org/downloads/', '', '', SW_SHOW, ewNoWait, ResultCode);
      end;
    end;

    // Install Ollama if not present
    if not IsOllamaInstalled then
    begin
      if MsgBox('Ollama is required for Aether to function. Would you like to download and install it now?', mbConfirmation, MB_YESNO) = IDYES then
      begin
        ShellExec('open', 'https://ollama.com/download', '', '', SW_SHOW, ewNoWait, ResultCode);
      end;
    end;

    // Set up auto-start if selected
    if WizardIsTaskSelected('autostart') then
    begin
      RegWriteStringValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'Aether', ExpandConstant('"{app}\start_aether.bat"'));
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Remove auto-start
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'Aether');
  end;
end;
