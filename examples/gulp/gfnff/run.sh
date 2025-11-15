#!/usr/bin/env bash
#
# Run benzene crystal optimization with GULP's GFN-FF force field
#
# This example demonstrates:
# - Using gulp-mlips with the GULP backend
# - GULP backend runs inner GULP with gfnff keyword
# - Tests round-trip .drv file format (write → read → use)
# - Two GULP instances: outer (optimizer) and inner (force calculator)
#
# Backend: GULP with GFN-FF force field
# System:  Benzene (C6H6) molecular crystal
#
# Environment variables:
#   KEYWORDS - GULP keywords for inner GULP (default: "conp gradient gfnff")
#   PORT     - Server port (default: 8193)
#

set -e

# Configuration
BACKEND="gulp"
KEYWORDS="${KEYWORDS:-conp gradient gfnff}"
PORT="${PORT:-8193}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec python3 "$SCRIPT_DIR/../run_example.py" \
    --backend "$BACKEND" \
    --keywords "$KEYWORDS" \
    --port "$PORT" \
    --input optimize.gin
