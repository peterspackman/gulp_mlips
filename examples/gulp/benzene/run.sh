#!/usr/bin/env bash
#
# Run benzene crystal optimization example
#
# Backend: PET-MAD (optimized for organic molecules)
# System:  Benzene (C6H6) molecular crystal
#
# Environment variables:
#   BACKEND - Backend to use (default: petmad)
#   DEVICE  - Device: cpu or cuda (default: cpu)
#   PORT    - Server port (default: 8193)
#

set -e

# Configuration
BACKEND="${BACKEND:-petmad}"
DEVICE="${DEVICE:-cpu}"
PORT="${PORT:-8193}"

# Get script directory and run Python runner
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec python3 "$SCRIPT_DIR/../run_example.py" \
    --backend "$BACKEND" \
    --device "$DEVICE" \
    --port "$PORT" \
    --input optimize.gin
