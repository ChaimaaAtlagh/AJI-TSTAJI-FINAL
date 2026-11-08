[CmdletBinding()]
param(
    [string]$Version,
    [string]$ApiBaseUrl = $env:AJI_PUBLIC_API_BASE_URL,
    [switch]$SkipInstaller,
    [switch]$AllowEmptyApiUrlForTests
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$spec = Join-Path $root "AJI_TSTAJI.spec"
$installerSpec = Join-Path $root "deployment\AJI_TSTAJI.iss"
$versionFile = Join-Path $root "deployment\VERSION"
$readme = Join-Path $root "deployment\README_WINDOWS.md"
$envExample = Join-Path $root "deployment\AJI_TSTAJI.env.example"

if (-not $Version) {
    $Version = (Get-Content -LiteralPath $versionFile -Raw).Trim()
}
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Version invalide '$Version'. Utilisez le format numérique X.Y.Z."
}
if (-not [string]::IsNullOrWhiteSpace($ApiBaseUrl)) {
    $apiUri = $null
    if (-not [Uri]::TryCreate($ApiBaseUrl, [UriKind]::Absolute, [ref]$apiUri)) {
        throw "AJI_PUBLIC_API_BASE_URL doit être une URL absolue HTTPS terminant par /api/v1."
    }
    $apiHost = $apiUri.Host.ToLowerInvariant()
    $parsedIp = $null
    $isIpLiteral = [System.Net.IPAddress]::TryParse($apiHost, [ref]$parsedIp)
    if (
        $apiUri.Scheme -ne "https" -or
        -not $apiUri.AbsolutePath.TrimEnd('/').EndsWith('/api/v1', [StringComparison]::OrdinalIgnoreCase) -or
        $apiUri.IsLoopback -or
        $apiUri.UserInfo -or $apiUri.Query -or $apiUri.Fragment -or
        $isIpLiteral -or
        $apiHost -in @("example.com", "example.org", "example.net") -or
        $apiHost.EndsWith(".localhost") -or $apiHost.EndsWith(".local") -or
        $apiHost.EndsWith(".example") -or $apiHost.EndsWith(".example.com") -or
        $apiHost.EndsWith(".example.org") -or $apiHost.EndsWith(".example.net") -or
        $apiHost.EndsWith(".test") -or $apiHost.EndsWith(".invalid")
    ) {
        throw "L'URL de l'API doit être une URL HTTPS publique réelle se terminant par /api/v1."
    }
}
else {
    if (-not $AllowEmptyApiUrlForTests) {
        throw "Renseignez AJI_PUBLIC_API_BASE_URL. L'option -AllowEmptyApiUrlForTests est réservée aux tests locaux/CI non distribuables."
    }
    Write-Warning "Aucune URL publique fournie : le paquet de test refusera toute connexion locale et ne peut pas être publié."
}

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python de l'environnement .venv introuvable : $python"
}
if (-not (Test-Path -LiteralPath $spec)) {
    throw "Fichier PyInstaller introuvable : $spec"
}
if (-not (Test-Path -LiteralPath (Join-Path $root "data\cleaned\data_nettoyee.xlsx"))) {
    throw "Le dataset nettoyé data\cleaned\data_nettoyee.xlsx est absent."
}

$compiler = (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source
if (-not $compiler) {
    foreach ($candidate in @(
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 7\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe")
    )) {
        if (Test-Path -LiteralPath $candidate) {
            $compiler = $candidate
            break
        }
    }
}
if (-not $SkipInstaller -and (-not $compiler -or -not (Test-Path -LiteralPath $installerSpec))) {
    throw "Inno Setup (ISCC.exe) est requis pour produire l'installateur. Utilisez -SkipInstaller uniquement pour un build portable local."
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputRoot = Join-Path $root "release\windows-v$Version-$stamp"
$distRoot = Join-Path $outputRoot "dist"
$workRoot = Join-Path $outputRoot "work"
$configRoot = Join-Path $outputRoot "build-config"
$packageDir = Join-Path $distRoot "AJI_TSTAJI"
$zipPath = Join-Path $outputRoot "AJI_TSTAJI-Windows-v$Version.zip"
$clientConfigPath = Join-Path $configRoot "client_api.json"

New-Item -ItemType Directory -Path $distRoot,$workRoot,$configRoot | Out-Null
$clientConfig = @{ api_base_url = $ApiBaseUrl }
$json = $clientConfig | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText(
    $clientConfigPath,
    $json,
    [System.Text.UTF8Encoding]::new($false)
)

$oldApiConfigPath = [Environment]::GetEnvironmentVariable("AJI_API_CONFIG_FILE", "Process")
$oldInstallerSource = [Environment]::GetEnvironmentVariable("AJI_INSTALLER_SOURCE", "Process")
$oldInstallerOutput = [Environment]::GetEnvironmentVariable("AJI_INSTALLER_OUTPUT", "Process")
$oldInstallerVersion = [Environment]::GetEnvironmentVariable("AJI_INSTALLER_VERSION", "Process")

Push-Location $root
try {
    $env:AJI_API_CONFIG_FILE = $clientConfigPath
    & $python -m PyInstaller --noconfirm --clean `
        --distpath $distRoot --workpath $workRoot $spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller a échoué avec le code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
    if ($null -eq $oldApiConfigPath) { Remove-Item Env:AJI_API_CONFIG_FILE -ErrorAction SilentlyContinue }
    else { $env:AJI_API_CONFIG_FILE = $oldApiConfigPath }
}

$exePath = Join-Path $packageDir "AJI_TSTAJI.exe"
if (-not (Test-Path -LiteralPath $exePath)) {
    throw "La compilation est terminée mais l'exécutable est absent : $exePath"
}
Copy-Item -LiteralPath $readme -Destination (Join-Path $packageDir "LISEZ-MOI.md")
Copy-Item -LiteralPath $envExample -Destination (Join-Path $packageDir "AJI_TSTAJI.env.example")

$forbiddenFiles = @(
    Get-ChildItem -LiteralPath $packageDir -Recurse -File | Where-Object {
        $_.Name -eq ".env" -or
        $_.Name -match '(?i)\.(db|sqlite|sqlite3)$' -or
        $_.Name -match '(?i)^(utilisateurs\.json|.*secret.*|.*password.*)$'
    }
)
if ($forbiddenFiles.Count -gt 0) {
    throw "Fichier privé détecté dans le paquet : $($forbiddenFiles[0].FullName)"
}
if (-not (Test-Path -LiteralPath (Join-Path $packageDir "_internal\config\client_api.json"))) {
    throw "La configuration publique de l'API n'a pas été intégrée au build."
}

Compress-Archive -LiteralPath $packageDir -DestinationPath $zipPath -CompressionLevel Optimal
Get-FileHash -LiteralPath $zipPath -Algorithm SHA256 |
    ForEach-Object { "$($_.Hash)  $([IO.Path]::GetFileName($zipPath))" } |
    Set-Content -LiteralPath "$zipPath.sha256" -Encoding ascii

$installerPath = $null
if (-not $SkipInstaller) {
    try {
        $env:AJI_INSTALLER_SOURCE = $packageDir
        $env:AJI_INSTALLER_OUTPUT = $outputRoot
        $env:AJI_INSTALLER_VERSION = $Version
        & $compiler $installerSpec
        if ($LASTEXITCODE -ne 0) {
            throw "La compilation Inno Setup a échoué avec le code $LASTEXITCODE."
        }
        $installerPath = Join-Path $outputRoot "AJI_TSTAJI_Setup-v$Version.exe"
        if (-not (Test-Path -LiteralPath $installerPath)) {
            throw "L'installateur attendu est absent : $installerPath"
        }
        Get-FileHash -LiteralPath $installerPath -Algorithm SHA256 |
            ForEach-Object { "$($_.Hash)  $([IO.Path]::GetFileName($installerPath))" } |
            Set-Content -LiteralPath "$installerPath.sha256" -Encoding ascii
    }
    finally {
        if ($null -eq $oldInstallerSource) { Remove-Item Env:AJI_INSTALLER_SOURCE -ErrorAction SilentlyContinue }
        else { $env:AJI_INSTALLER_SOURCE = $oldInstallerSource }
        if ($null -eq $oldInstallerOutput) { Remove-Item Env:AJI_INSTALLER_OUTPUT -ErrorAction SilentlyContinue }
        else { $env:AJI_INSTALLER_OUTPUT = $oldInstallerOutput }
        if ($null -eq $oldInstallerVersion) { Remove-Item Env:AJI_INSTALLER_VERSION -ErrorAction SilentlyContinue }
        else { $env:AJI_INSTALLER_VERSION = $oldInstallerVersion }
    }
}

Write-Host "Version       : $Version"
Write-Host "Application   : $exePath"
Write-Host "Paquet ZIP    : $zipPath"
Write-Host "Empreinte ZIP : $zipPath.sha256"
if ($installerPath) {
    Write-Host "Installateur  : $installerPath"
    Write-Host "Empreinte EXE : $installerPath.sha256"
}
