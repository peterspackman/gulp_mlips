# Al₂O₃ Corundum Optimization

Inorganic crystal optimization with FairChem UMA.

## What This Does

- **Outer GULP**: Performs geometry optimization
- **Inner Calculator**: FairChem UMA via gulp-mlips-host
- **System**: Al₂O₃ corundum crystal (R-3c space group)

This example uses:
- Model: `uma-s-1p1` (small, fast)
- Task: `omat` (materials/crystals)
- Device: `cpu`

## Usage

```bash
./run.sh
```

## Configuration

```bash
# Use GPU (much faster)
DEVICE=cuda ./run.sh

# Use larger model (more accurate)
MODEL=uma-m-1p1 ./run.sh

# Different port
PORT=8194 ./run.sh
```

## Files

- `optimize.gin` - Structure optimization with symmetry (R-3c)
- `run.sh` - Runs the example (starts server, runs GULP, cleans up)
- `gulp_mlips_wrapper.sh` - Interface between GULP and gulp-mlips-client
