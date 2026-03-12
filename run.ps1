param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

& $Python -m pip install -r "$root\\requirements.txt"
& $Python "$root\\main.py"

