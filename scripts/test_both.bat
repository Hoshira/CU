@echo off
cd /d "%~dp0.."
python -m src.emulator --vfs .\data --script .\scripts\demo_commands.txt