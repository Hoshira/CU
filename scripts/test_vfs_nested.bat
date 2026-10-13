@echo off
cd /d "%~dp0.."
python -m src.emulator --vfs .\vfs_samples\nested --script .\scripts\demo_commands.txt