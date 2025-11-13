# Silicon Diamond Optimization

Elemental crystal optimization with PET-MAD or FairChem.

## What This Does

- **Outer GULP**: Performs geometry optimization
- **Inner Calculator**: PET-MAD or FairChem UMA via gulp-mlips-host
- **System**: Silicon diamond structure (8 atoms)

## Usage

```bash
./run.sh
```

## Configuration

```bash
# Use FairChem backend instead of PET-MAD
BACKEND=fairchem ./run.sh

# Use GPU
DEVICE=cuda ./run.sh

# Combine options
BACKEND=fairchem DEVICE=cuda ./run.sh
```

## Files

- `optimize.gin` - Structure and cell optimization (starts compressed, should expand)
- `run.sh` - Runs the example (starts server, runs GULP, cleans up)
- `gulp_mlips_wrapper.sh` - Interface between GULP and gulp-mlips-client
