#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Independent checks continue after failures; JSON records every result.
# Prior reports are never overwritten. Optional arguments follow the run tag:
#   signoff.sh assembly-1350 --output <new-dir> [--collect-only] [--threads 2]
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec python3 "$SCRIPT_DIR/signoff_runner.py" "$@"
