[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath
)

$ErrorActionPreference = "Stop"
$installer = (Resolve-Path -LiteralPath $InstallerPath).Path
$testRoot = Join-Path $env:TEMP "AJI-TSTAJI-installer-smoke-$PID"
$installRoot = Join-Path $testRoot "installed-app"
$profileRoot = Join-Path $testRoot "isolated-localappdata"
$appDataRoot = Join-Path $profileRoot "AJI TSTAJI"
$dataRoot = Join-Path $appDataRoot "data"
$sentinel = Join-Path $dataRoot "persistence-check.txt"

New-Item -ItemType Directory -Path $testRoot | Out-Null
New-Item -ItemType Directory -Path $dataRoot,$installRoot | Out-Null
Set-Content -LiteralPath $sentinel -Value "Keep this test profile" -Encoding ascii

function Install-TestBuild {
    $arguments = @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/DIR=$installRoot"
    )
    $result = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru
    if ($result.ExitCode -ne 0) {
        throw "L'installateur a échoué (code $($result.ExitCode))."
    }
}

function Assert-TestProfile {
    if (-not (Test-Path -LiteralPath $sentinel)) {
        throw "Le profil de test a été supprimé : $sentinel"
    }
    if ((Get-Content -LiteralPath $sentinel -Raw).Trim() -ne "Keep this test profile") {
        throw "Le contenu du profil de test a été modifié."
    }
}

Install-TestBuild
$exe = Join-Path $installRoot "AJI_TSTAJI.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    throw "L'exécutable installé est absent : $exe"
}
if (-not (Test-Path -LiteralPath (Join-Path $installRoot "_internal\config\client_api.json"))) {
    throw "La configuration API intégrée n'est pas présente après installation."
}
Assert-TestProfile

# Relaunching the same AppId into the same directory simulates an in-place update.
Install-TestBuild
Assert-TestProfile

$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $exe
$startInfo.WorkingDirectory = $installRoot
$startInfo.UseShellExecute = $false
$startInfo.EnvironmentVariables["LOCALAPPDATA"] = $profileRoot
$process = [System.Diagnostics.Process]::Start($startInfo)
try {
    $deadline = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $deadline) {
        $process.Refresh()
        if ($process.HasExited) {
            throw "AJI_TSTAJI.exe s'est fermé au démarrage (code $($process.ExitCode))."
        }
        if ($process.MainWindowTitle -eq "AJI TSTAJI") {
            break
        }
        Start-Sleep -Seconds 1
    }
    if ($process.MainWindowTitle -ne "AJI TSTAJI") {
        throw "La fenêtre AJI TSTAJI n'est pas apparue dans les 90 secondes."
    }
}
finally {
    if ($process -and -not $process.HasExited) {
        if (-not $process.CloseMainWindow()) {
            $process.Kill()
        }
        if (-not $process.WaitForExit(10000)) {
            $process.Kill()
        }
    }
}

$uninstaller = Get-ChildItem -LiteralPath $installRoot -Filter "unins*.exe" -File |
    Select-Object -First 1
if (-not $uninstaller) {
    throw "Le désinstalleur Inno Setup est absent du dossier de test."
}
$uninstall = Start-Process -FilePath $uninstaller.FullName `
    -ArgumentList @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART") -Wait -PassThru
if ($uninstall.ExitCode -ne 0) {
    throw "La désinstallation de test a échoué (code $($uninstall.ExitCode))."
}
if (Test-Path -LiteralPath $exe) {
    throw "Les fichiers du programme sont encore présents après désinstallation."
}
Assert-TestProfile

Write-Host "Installateur vérifié : installation, mise à jour, lancement et désinstallation."
Write-Host "Le profil de test a été conservé dans : $appDataRoot"
