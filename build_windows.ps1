param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

& $Python -m pip install --upgrade pip
& $Python -m pip install -r "$root\\requirements.txt"
& $Python -m pip install pyinstaller

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --onefile `
  --name "INTERFACE-AMD" `
  --add-data "icon.png;." `
  --add-data "logo.png;." `
  --add-data "alert.wav;." `
  main.py

Write-Host "Build concluída. Veja a pasta dist\\INTERFACE-AMD\\"

