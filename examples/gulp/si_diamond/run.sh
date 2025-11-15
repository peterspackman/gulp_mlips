#!/usr/bin/env bash
#
# Run silicon diamond crystal optimization example
#
# Backend: PET-MAD (default) or FairChem
# System:  Silicon diamond structure (compressed lattice)
#
# Environment variables:
#   BACKEND - Backend to use: petmad or fairchem (default: petmad)
#   MODEL   - Model for fairchem backend (default: uma-s-1p1)
#   TASK    - Task for fairchem backend (default: omat)
#   DEVICE  - Device: cpu or cuda (default: cpu)
#   PORT    - Server port (default: 8193)
#

set -e

# Configuration
BACKEND="${BACKEND:-petmad}"
MODEL="${MODEL:-uma-s-1p1}"
TASK="${TASK:-omat}"
DEVICE="${DEVICE:-cpu}"
PORT="${PORT:-8193}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Build command based on backend
if [ "$BACKEND" = "fairchem" ]; then
    exec python3 "$SCRIPT_DIR/../run_example.py" \
        --backend "$BACKEND" \
        --model "$MODEL" \
        --task "$TASK" \
        --device "$DEVICE" \
        --port "$PORT" \
        --input optimize.gin
else
    exec python3 "$SCRIPT_DIR/../run_example.py" \
        --backend "$BACKEND" \
        --device "$DEVICE" \
        --port "$PORT" \
        --input optimize.gin
fi
