#define AppName "AJI TSTAJI"
#define AppVersion GetEnv("AJI_INSTALLER_VERSION")
#define AppSourceDir GetEnv("AJI_INSTALLER_SOURCE")
#define OutputDir GetEnv("AJI_INSTALLER_OUTPUT")

[Setup]
AppId={{3A1BEA82-30BB-4B6A-8F9C-8D98A2694B9C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=AJI TSTAJI
DefaultDirName={localappdata}\Programs\AJI TSTAJI
DefaultGroupName=AJI TSTAJI
UninstallDisplayIcon={app}\AJI_TSTAJI.exe
PrivilegesRequired=lowest
UsePreviousAppDir=yes
DisableProgramGroupPage=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir={#OutputDir}
OutputBaseFilename=AJI_TSTAJI_Setup-v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
CloseApplications=yes
RestartApplications=yes
VersionInfoVersion={#AppVersion}.0
VersionInfoProductName=AJI TSTAJI
VersionInfoProductVersion={#AppVersion}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"; Flags: unchecked

[Files]
Source: "{#AppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\AJI TSTAJI"; Filename: "{app}\AJI_TSTAJI.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\AJI TSTAJI"; Filename: "{app}\AJI_TSTAJI.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\AJI_TSTAJI.exe"; Description: "Lancer AJI TSTAJI"; Flags: postinstall nowait skipifsilent
