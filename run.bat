@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"

python -m pip install -r "%ROOT%requirements.txt"
python "%ROOT%main.py"

endlocal

