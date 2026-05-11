param(
    [string]$ExeName = "StatisticApp",
    [switch]$SkipExeBuild
)

$ErrorActionPreference = "Stop"

if (-not $SkipExeBuild) {
    & "$PSScriptRoot\build_exe.ps1" -ExeName $ExeName
}

$isccCmd = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $isccCmd) {
    Write-Host "Inno Setup bulunamadi. Winget ile kuruluyor..."
    winget install --id JRSoftware.InnoSetup --exact --accept-package-agreements --accept-source-agreements
    $isccCmd = Get-Command iscc -ErrorAction SilentlyContinue
}

if (-not $isccCmd) {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    )
    $isccPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $isccPath) {
        throw "ISCC bulunamadi. Inno Setup kurulumunu kontrol edin."
    }
} else {
    $isccPath = $isccCmd.Source
}

& $isccPath "$PSScriptRoot\installer.iss"

Write-Host ""
Write-Host "Setup tamamlandi: installer-dist\StatisticApp-Setup.exe"
