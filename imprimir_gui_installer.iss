; Inno Setup script para instalar Bunker Print Master GUI

#define MyAppName "Bunker Print Master GUI"
#ifndef MyAppVersion
	#define MyAppVersion "1.0.1"
#endif
#define MyAppPublisher "Bunker"
#define MyAppExeName "imprimir_gui.exe"
#define MyAppIconFile "assets\\app.ico"

[Setup]
AppId={{7F853535-3FC7-4B8A-8A0A-8BFD8E0E6D9B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=Setup-Bunker-Print-Master-GUI-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=yes
#ifexist "assets\\app.ico"
SetupIconFile={#MyAppIconFile}
#endif

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "version.txt"; DestDir: "{app}"; Flags: ignoreversion
#ifexist "assets\\app.ico"
Source: "assets\app.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
#endif

[Icons]
#ifexist "assets\\app.ico"
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconFile}"
#else
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
#endif
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
#ifexist "assets\\app.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppIconFile}"
#else
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
#endif

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent
