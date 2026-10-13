#!/usr/bin/env bash
set +e
cd "$(dirname "$0")/.."
python3 -m src.emulator --vfs ./no_such_vfs
echo "exit code: $?"