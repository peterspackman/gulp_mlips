# gulp-mlips

GULP-compatible interface for Machine Learning Interatomic Potentials (MLIPs).

## What This Does

Allows GULP to use ML potentials (PET-MAD, FairChem UMA) via a client-server architecture:
- Server keeps ML model loaded in memory
- Client handles communication with GULP
- Efficient: model loaded once, used for many calculations

## Installation

### Option 1: From GitHub URL (quick install)

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with PET-MAD backend
uv pip install "gulp-mlips[petmad] @ git+https://github.com/peterspackman/gulp_mlips.git"

# Or install with FairChem backend
uv pip install "gulp-mlips[fairchem] @ git+https://github.com/peterspackman/gulp_mlips.git"
```

### Option 2: Clone repository (recommended for examples)

```bash
git clone https://github.com/peterspackman/gulp_mlips.git
cd gulp_mlips

uv venv
source .venv/bin/activate

# Install with backend
uv pip install -e ".[petmad]"
uv pip install -e ".[fairchem]"
```

## Running Examples

Each example includes a `run.sh` script that automatically starts the server and runs GULP:

```bash
# Benzene with PET-MAD
cd examples/gulp/benzene
./run.sh

# Si diamond with FairChem UMA
cd examples/gulp/uma
./run.sh
```

## Examples

Complete working examples with GULP:

- **[examples/gulp/benzene](examples/gulp/benzene)** - Organic crystal with PET-MAD
- **[examples/gulp/uma](examples/gulp/uma)** - Inorganic crystal with FairChem UMA
- **[examples/gulp/si_diamond](examples/gulp/si_diamond)** - Simple test system
- **[examples/gulp/gfnff](examples/gulp/gfnff)** - .drv format validation test

## Available Backends

### PET-MAD
Organic molecule potential, good for molecular systems.

```bash
gulp-mlips-host --backend petmad --device cpu
```

### FairChem UMA
Universal model for materials and molecules. Requires HuggingFace authentication (`huggingface-cli login`).

See [FairChem documentation](https://fair-chem.github.io/core/install.html) for details.

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
