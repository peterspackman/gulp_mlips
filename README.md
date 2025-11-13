# gulp-mlips

GULP-compatible interface for Machine Learning Interatomic Potentials (MLIPs).

## What This Does

Allows GULP to use ML potentials (PET-MAD, FairChem UMA) via a client-server architecture:
- Server keeps ML model loaded in memory
- Client handles communication with GULP
- Efficient: model loaded once, used for many calculations

## Installation

```bash
# Basic install
uv pip install -e .

# With PET-MAD backend (for organic molecules)
uv pip install -e ".[petmad]"

# With FairChem backend (for materials)
uv pip install -e ".[fairchem]"
huggingface-cli login  # Required for FairChem
```

## Quick Start

```bash
# 1. Start server (PET-MAD example)
gulp-mlips-host --backend petmad --device cpu --port 8193 &

# 2. Test client
gulp-mlips-client structure.xyz output.drv --port 8193

# 3. Use with GULP - see examples below
```

## Examples

Complete working examples with GULP:

- **[examples/gulp/benzene](examples/gulp/benzene)** - Organic crystal with PET-MAD
- **[examples/gulp/uma](examples/gulp/uma)** - Inorganic crystal with FairChem UMA
- **[examples/gulp/si_diamond](examples/gulp/si_diamond)** - Simple test system
- **[examples/gulp/gfnff](examples/gulp/gfnff)** - .drv format validation test

Each example has a `run.sh` script that handles everything automatically:

```bash
cd examples/gulp/benzene
./run.sh
```

## Available Backends

### PET-MAD
Organic molecule potential, good for molecular systems.

```bash
gulp-mlips-host --backend petmad --device cpu
```

### FairChem UMA
Universal model for materials and molecules.

```bash
# For materials/crystals
gulp-mlips-host --backend fairchem --model uma-s-1p1 --task omat

# For molecules
gulp-mlips-host --backend fairchem --model uma-s-1p1 --task omol
```

Models: `uma-s-1p1` (fast), `uma-m-1p1` (more accurate)

## GULP Integration

GULP input file (`.gin`):

```
opti conp nosym

cell
5.5 5.5 5.5 90.0 90.0 90.0

fractional
Si core 0.00 0.00 0.00 0.0
Si core 0.25 0.25 0.25 0.0

# Use external calculator
external_call
./gulp_mlips_wrapper.sh
end

# Read forces from .drv file
external_drv gulp_mlip.drv
```

The wrapper script (`gulp_mlips_wrapper.sh`) calls `gulp-mlips-client` to get forces from the server.

See `examples/gulp/` for complete examples.

## Commands

```bash
# Start server
gulp-mlips-host --backend BACKEND [--device cpu|cuda] [--port 8193]

# Calculate forces
gulp-mlips-client INPUT.xyz OUTPUT.drv [--port 8193]

# Initialize models (optional, downloads models)
gulp-mlips-init --backend BACKEND
```

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest
```
