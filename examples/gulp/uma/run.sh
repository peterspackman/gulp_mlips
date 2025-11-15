#!/usr/bin/env bash
#
# Run silicon optimization example with FairChem UMA
#
# Backend: FairChem UMA (state-of-the-art universal model)
# System:  Silicon diamond structure
#
# Environment variables:
#   MODEL  - FairChem model (default: uma-s-1p1)
#   TASK   - Task type (default: omat)
#   DEVICE - Device: cpu or cuda (default: cpu)
#   PORT   - Server port (default: 8193)
#
# Note: First run will download the model (~100MB for uma-s-1p1)
#

set -e

# Configuration
BACKEND="fairchem"
MODEL="${MODEL:-uma-s-1p1}"
TASK="${TASK:-omat}"
DEVICE="${DEVICE:-cpu}"
PORT="${PORT:-8193}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec python3 "$SCRIPT_DIR/../run_example.py" \
    --backend "$BACKEND" \
    --model "$MODEL" \
    --task "$TASK" \
    --device "$DEVICE" \
    --port "$PORT" \
    --input optimize.gin
