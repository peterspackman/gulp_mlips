#!/bin/bash
#
# Run benzene crystal optimization with GULP's GFN-FF force field
#
# This example demonstrates:
# - Using gulp-mlips with the GULP backend
# - GULP backend runs inner GULP with gfnff keyword
# - Tests round-trip .drv file format (write → read → use)
# - Two GULP instances: outer (optimizer) and inner (force calculator)
#

set -e  # Exit on error

echo "=================================================================="
echo "Benzene Crystal Optimization with GULP GFN-FF Backend"
echo "=================================================================="
echo "Backend: GULP with GFN-FF force field"
echo "System:  Benzene (C6H6) molecular crystal"
echo "Test:    Round-trip .drv file format validation"
echo "=================================================================="
echo ""

# =============================================================================
# Configuration
# =============================================================================

BACKEND="gulp"
KEYWORDS="${KEYWORDS:-conp gradient gfnff}"  # GULP keywords for inner GULP
PORT="${PORT:-8193}"                         # Override with: PORT=8194 ./run.sh
INPUT_FILE="optimize.gin"
OUTPUT_FILE="optimize.gout"

# =============================================================================
# Check prerequisites
# =============================================================================

if ! command -v gulp &> /dev/null; then
    echo "ERROR: GULP not found in PATH" >&2
    echo "Please install GULP or add it to your PATH" >&2
    exit 1
fi

if ! command -v gulp-mlips-host &> /dev/null; then
    echo "ERROR: gulp-mlips-host not found in PATH" >&2
    echo "Please install gulp-mlips: pip install -e ." >&2
    exit 1
fi

if ! command -v gulp-mlips-client &> /dev/null; then
    echo "ERROR: gulp-mlips-client not found in PATH" >&2
    echo "Please install gulp-mlips: pip install -e ." >&2
    exit 1
fi

# =============================================================================
# Start the server
# =============================================================================

echo "Starting gulp-mlips-host server..."
echo "  Backend:  $BACKEND"
echo "  Keywords: $KEYWORDS"
echo "  Port:     $PORT"
echo ""
echo "Architecture:"
echo "  Outer GULP (optimizer) → gulp-mlips-client → gulp-mlips-host"
echo "                           ↓"
echo "  Inner GULP (GFN-FF) writes .drv → gulp_drv_calculator reads it"
echo "                           ↓"
echo "  Forces go back → Outer GULP uses them for optimization"
echo ""

gulp-mlips-host --backend "$BACKEND" --keywords "$KEYWORDS" --port "$PORT" > host.log 2>&1 &
SERVER_PID=$!

# Cleanup function - stops server on exit
cleanup() {
    echo ""
    echo "Cleaning up..."
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "Stopping server (PID $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
    echo "Done!"
}
trap cleanup EXIT

# Wait for server to start
echo "Waiting for server to initialize..."
sleep 3

# Test server health
if ! curl -s http://127.0.0.1:$PORT/health > /dev/null 2>&1; then
    echo ""
    echo "ERROR: Server not responding at http://127.0.0.1:$PORT" >&2
    echo "Check host.log for details:" >&2
    tail -20 host.log >&2
    exit 1
fi

echo "Server is ready!"
echo ""

# =============================================================================
# Run GULP
# =============================================================================

echo "Running GULP optimization..."
echo "  Input:  $INPUT_FILE"
echo "  Output: $OUTPUT_FILE"
echo ""

# Set environment variables for the wrapper script
export HOST="127.0.0.1"
export PORT="$PORT"

# Run GULP
if gulp < "$INPUT_FILE" > "$OUTPUT_FILE" 2>&1; then
    echo ""
    echo "=================================================================="
    echo "SUCCESS!"
    echo "=================================================================="
    echo "GULP optimization completed successfully"
    echo ""
    echo "This validates:"
    echo "  ✓ Our .drv file writing (in gulp-mlips-client)"
    echo "  ✓ GULP's .drv file writing (inner GULP with GFN-FF)"
    echo "  ✓ Our .drv file reading (gulp_drv_calculator)"
    echo "  ✓ Round-trip conversion (ASE ↔ GULP ↔ ASE)"
    echo ""
    echo "Output files:"
    ls -lh *.gout *.xyz *.drv 2>/dev/null || echo "  (no output files found)"
    echo ""
    echo "View results:"
    echo "  Full output:     cat $OUTPUT_FILE"
    echo "  Final structure: cat benzene.xyz"
    echo "  Server log:      cat host.log"
else
    echo ""
    echo "=================================================================="
    echo "GULP FAILED"
    echo "=================================================================="
    echo "Check $OUTPUT_FILE for errors"
    echo ""
    echo "Last 50 lines of output:"
    tail -50 "$OUTPUT_FILE"
    echo ""
    echo "Last 20 lines of server log:"
    tail -20 host.log
    exit 1
fi

# Cleanup happens automatically via trap
