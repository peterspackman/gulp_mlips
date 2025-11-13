#!/bin/bash
#
# GULP-MLIPS Wrapper Script
#
# This script connects GULP to the gulp-mlips-client for external ML potential calculations.
#
# HOW IT WORKS:
# 1. GULP writes structure → gulpext.xyz (hardcoded filename by GULP)
# 2. GULP calls this wrapper script
# 3. This script calls gulp-mlips-client
# 4. gulp-mlips-client sends structure to server and receives energy/forces
# 5. gulp-mlips-client writes → gulp_mlip.drv (must match external_drv in .gin file)
# 6. GULP reads energy/forces from gulp_mlip.drv
#
# CONFIGURATION:
# Set these environment variables before running GULP:
#   HOST=127.0.0.1  (default: localhost)
#   PORT=8193       (default: 8193)
#   DEBUG=1         (optional: enable debug output)
#
# Example:
#   export PORT=8193
#   gulp < optimize.gin > optimize.gout
#

set -e  # Exit immediately if any command fails

# =============================================================================
# Configuration - Override via environment variables
# =============================================================================

# Server connection
if [ -z "$HOST" ]; then
    HOST="127.0.0.1"
fi

if [ -z "$PORT" ]; then
    PORT="8193"
fi

# File names - These MUST match GULP's expectations
INPUT_FILE="gulpext.xyz"      # GULP always writes this name (hardcoded in GULP)
OUTPUT_FILE="gulp_mlip.drv"    # Must match "external_drv" directive in your .gin file

# Debug output
if [ -z "$DEBUG" ]; then
    DEBUG=0
fi

# =============================================================================
# Main execution
# =============================================================================

if [ "$DEBUG" = "1" ]; then
    echo "===========================================" >&2
    echo "GULP-MLIPS Wrapper" >&2
    echo "===========================================" >&2
    echo "Input file:  $INPUT_FILE" >&2
    echo "Output file: $OUTPUT_FILE" >&2
    echo "Server:      $HOST:$PORT" >&2
    echo "===========================================" >&2
fi

# Verify GULP wrote the input file
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: GULP did not write $INPUT_FILE" >&2
    echo "This file should be created by GULP before calling this script" >&2
    exit 1
fi

# Call the gulp-mlips-client to get energy and forces
if [ "$DEBUG" = "1" ]; then
    echo "Calling gulp-mlips-client..." >&2
fi

gulp-mlips-client "$INPUT_FILE" "$OUTPUT_FILE" \
    --host "$HOST" \
    --port "$PORT" \
    --timeout 300

# Verify output file was created
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "ERROR: gulp-mlips-client did not create $OUTPUT_FILE" >&2
    echo "Check that the server is running and accessible" >&2
    exit 1
fi

if [ "$DEBUG" = "1" ]; then
    echo "Success! Energy and forces written to $OUTPUT_FILE" >&2
    echo "===========================================" >&2
fi

exit 0
