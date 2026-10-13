@echo off
cd /d "%~dp0.."
python -m src.emulator --vfs .\no_such_vfs
echo exit code: %ERRORLEVEL%