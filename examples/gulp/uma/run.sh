#!/bin/bash
#
# Run silicon optimization example with FairChem UMA
#
# This script:
# 1. Starts the gulp-mlips-host server with FairChem UMA backend
# 2. Runs GULP with the optimize.gin input file
# 3. Cleans up the server on exit
#

set -e  # Exit on error

echo "=================================================================="
echo "Silicon Optimization with FairChem UMA"
echo "=================================================================="
echo "Backend: FairChem UMA (state-of-the-art universal model)"
echo "System:  Silicon diamond structure"
echo "=================================================================="
echo ""

# =============================================================================
# Configuration
# =============================================================================

BACKEND="fairchem"
MODEL="${MODEL:-uma-s-1p1}"      # Default: small model (fast)
TASK="${TASK:-omat}"              # Default: materials task
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
echo "  Task:    $TASK (materials/crystals)"
echo "  Device:  $DEVICE"
echo "  Port:    $PORT"
echo ""
echo "Note: First run will download the model (~100MB for uma-s-1p1)"
echo ""

gulp-mlips-host --backend "$BACKEND" --model "$MODEL" --task "$TASK" --device "$DEVICE" --port "$PORT" > host.log 2>&1 &
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

# Wait for server to start (longer for first-time model download)
echo "Waiting for server to initialize..."
echo "(This may take a few minutes on first run while downloading the model)"
sleep 10

# Test server health
MAX_RETRIES=60  # Wait up to 60 seconds for model to load
RETRY_COUNT=0
while ! curl -s http://127.0.0.1:$PORT/health > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo ""
        echo "ERROR: Server not responding at http://127.0.0.1:$PORT" >&2
        echo "Check host.log for details:" >&2
        tail -50 host.log >&2
        exit 1
    fi
    sleep 1
done

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
    ls -lh *.gout *.res 2>/dev/null || echo "  (no output files found)"
    echo ""
    echo "View results:"
    echo "  Full output:     cat $OUTPUT_FILE"
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
