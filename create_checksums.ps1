$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$files = @()

$exePath = Join-Path $root 'dist\imprimir_gui.exe'
if (Test-Path $exePath) {
    $files += Get-Item $exePath
}

$latestInstaller = Get-ChildItem -Path (Join-Path $root 'installer\Setup-Bunker-Print-Master-GUI-*.exe') -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($latestInstaller) {
    $files += $latestInstaller
}

if (-not $files) {
    throw 'No hay archivos para hashear.'
}

$lines = foreach ($file in $files) {
    $hash = (Get-FileHash -Algorithm SHA256 -Path $file.FullName).Hash.ToLower()
    '{0} *{1}' -f $hash, $file.Name
}

$outFile = Join-Path $root 'installer\SHA256SUMS.txt'
$lines | Set-Content -Path $outFile -Encoding ascii
Write-Output "Checksums generados en: $outFile"
