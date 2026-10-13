@echo off
cd /d "%~dp0.."
python -m src.emulator --vfs .\vfs_samples\minimal --script .\scripts\demo_commands.txt