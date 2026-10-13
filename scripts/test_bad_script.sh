#!/usr/bin/env bash
set +e
cd "$(dirname "$0")/.."
python3 -m src.emulator --script ./scripts/no_such_file.txt
echo "exit code: $?"