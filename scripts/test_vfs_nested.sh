#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m src.emulator \
  --vfs ./vfs_samples/nested \
  --script ./scripts/demo_commands.txt