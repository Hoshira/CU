@echo off
cd /d "%~dp0.."
python -m src.emulator --script .\scripts\no_such_file.txt
echo exit code: %ERRORLEVEL%