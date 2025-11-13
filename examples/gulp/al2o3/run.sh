#!/bin/bash
#
# Run Al2O3 corundum crystal optimization example
#
# This script:
# 1. Starts the gulp-mlips-host server with FairChem backend
# 2. Runs GULP with the optimize.gin input file
# 3. Cleans up the server on exit
#

set -e  # Exit on error

echo "=================================================================="
echo "Al2O3 Corundum Crystal Optimization Example"
echo "=================================================================="
echo "Backend: FairChem UMA (Universal Materials Accelerator)"
echo "System:  Al2O3 corundum (rhombohedral R-3c space group)"
echo "=================================================================="
echo ""

# =============================================================================
# Configuration
# =============================================================================

BACKEND="fairchem"
MODEL="${MODEL:-uma-s-1p1}"       # FairChem model: uma-s-1p1 (small, fast)
TASK="${TASK:-omat}"              # Task type: omat (Open Materials)
DEVICE="${DEVICE:-cpu}"           # Override with: DEVICE=cuda ./run.sh
PORT="${PORT:-8193}"              # Override with: PORT=8194 ./run.sh
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
echo "  Backend: $BACKEND"
echo "  Model:   $MODEL"
echo "  Task:    $TASK"
echo "  Device:  $DEVICE"
echo "  Port:    $PORT"
echo ""

gulp-mlips-host --backend "$BACKEND" --model "$MODEL" --task "$TASK" \
    --device "$DEVICE" --port "$PORT" > host.log 2>&1 &
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

# Wait for server to start (FairChem takes longer to load)
echo "Waiting for server to initialize (FairChem model loading may take 10-30 seconds)..."
sleep 10

# Test server health
if ! curl -s http://127.0.0.1:$PORT/health > /dev/null 2>&1; then
    echo ""
    echo "ERROR: Server not responding at http://127.0.0.1:$PORT" >&2
    echo "FairChem models require more time to load. Waiting additional 10 seconds..." >&2
    sleep 10
    if ! curl -s http://127.0.0.1:$PORT/health > /dev/null 2>&1; then
        echo "ERROR: Server still not responding" >&2
        echo "Check host.log for details:" >&2
        tail -20 host.log >&2
        exit 1
    fi
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
    echo "Output files:"
    ls -lh *.gout *.xyz *.cif *.res 2>/dev/null || echo "  (no output files found)"
    echo ""
    echo "View results:"
    echo "  Full output:     cat $OUTPUT_FILE"
    echo "  Final structure: cat al2o3.xyz"
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
