; ============================================================ Gamble Game - installer script
;
; Build (needs Inno Setup 6):
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\GambleGame.iss
; Output:
;   installer\Output\GambleGame-1.0.0-Setup.exe
;
; IMPORTANT: the game writes savegame.txt / gamble_meta.txt / gamble_settings.txt NEXT TO THE
; EXECUTABLE, so it must be installed somewhere the user can write to. That is why this installs
; per-user into {localappdata}\Programs and asks for NO administrator rights (PrivilegesRequired
; =lowest). Installing into Program Files would make the game unable to save.
;
; The uninstaller only removes installed files; savegame.txt is created at run time, so the
; player's progress survives an uninstall. Deliberately NO [UninstallDelete] entry for *.txt -
; that would wipe the player's save with the game.
;
; Note: do NOT put "; comment" on the same line as a directive - Inno treats it as part of the value.
; Also: every entry in [Languages]/[Tasks]/[Files]/[Icons]/[Run] must be on ONE line, ";" separates
; its parameters.

#define MyAppName "Gamble Game"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Gamble Game contributors"
#define MyAppURL "https://github.com/"
#define MyAppExeName "GambleGame.exe"
#define MyBuildDir "..\dist\GambleGame"

[Setup]
AppId={{7C4E1B60-52A9-4E3B-9B6F-2D6A6C9E1A41}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
VersionInfoVersion={#MyAppVersion}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
VersionInfoDescription={#MyAppName} - a casino life simulation
VersionInfoCopyright=Free open source game (MIT)
DefaultDirName={localappdata}\Programs\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=GambleGame-{#MyAppVersion}-Setup
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\docs\OKUMA-BENIM.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
