#define MyAppName "ScreenChurch"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Jânio Anselmo, Eng. Me"
#define MyAppURL "mailto:janio@ensa.com.br"
#define MyAppExeName "ScreenChurch.exe"

[Setup]
AppId={{6F56E12E-9913-4ED4-9146-DF771C06F393}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\ScreenChurch
DefaultGroupName=ScreenChurch
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=ScreenChurch_Setup_v1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "..\dist\ScreenChurch\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{userdocs}\ScreenChurchData"
Name: "{userdocs}\ScreenChurchData\bibles"
Name: "{userdocs}\ScreenChurchData\songs"
Name: "{userdocs}\ScreenChurchData\media"
Name: "{userdocs}\ScreenChurchData\media\images"
Name: "{userdocs}\ScreenChurchData\media\videos"
Name: "{userdocs}\ScreenChurchData\media\backgrounds"
Name: "{userdocs}\ScreenChurchData\media\backgrounds\images"
Name: "{userdocs}\ScreenChurchData\media\backgrounds\videos"
Name: "{userdocs}\ScreenChurchData\config"
Name: "{userdocs}\ScreenChurchData\database"
Name: "{userdocs}\ScreenChurchData\themes"
Name: "{userdocs}\ScreenChurchData\services"
Name: "{userdocs}\ScreenChurchData\exports"
Name: "{userdocs}\ScreenChurchData\backups"

[Icons]
Name: "{autoprograms}\ScreenChurch"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\ScreenChurch"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir o ScreenChurch"; Flags: nowait postinstall skipifsilent

[Code]
function VlcInstalled(): Boolean;
begin
  Result := RegKeyExists(HKLM64, 'SOFTWARE\VideoLAN\VLC')
    or RegKeyExists(HKLM32, 'SOFTWARE\VideoLAN\VLC')
    or RegKeyExists(HKCU, 'SOFTWARE\VideoLAN\VLC');
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not VlcInstalled() then begin
    MsgBox(
      'Atenção: o VLC Media Player 64-bit não foi encontrado.' + #13#10 + #13#10 +
      'O ScreenChurch usa o VLC para reproduzir vídeos. Instale o VLC 64-bit nesta máquina para garantir a reprodução de MP4, MOV, MKV, AVI, WMV e FLV.',
      mbInformation,
      MB_OK
    );
  end;
end;
