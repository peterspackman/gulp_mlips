#!/usr/bin/env bash
#
# Run Al2O3 corundum crystal optimization example
#
# Backend: FairChem UMA (Universal Materials Accelerator)
# System:  Al2O3 corundum (rhombohedral R-3c space group)
#
# Environment variables:
#   MODEL  - FairChem model (default: uma-s-1p1)
#   TASK   - Task type (default: omat)
#   DEVICE - Device: cpu or cuda (default: cpu)
#   PORT   - Server port (default: 8193)
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
