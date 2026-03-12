#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --name "interface-amd" \
  --add-data "icon.png:." \
  --add-data "logo.png:." \
  --add-data "alert.wav:." \
  main.py

echo "Build concluída. Veja a pasta dist/interface-amd/"

