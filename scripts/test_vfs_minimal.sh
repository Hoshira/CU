#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m src.emulator \
  --vfs ./vfs_samples/minimal \
  --script ./scripts/demo_commands.txt