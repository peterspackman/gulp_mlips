# Benzene Crystal Optimization

Organic molecular crystal optimization using PET-MAD.

## What This Does

- **Outer GULP**: Performs geometry optimization
- **Inner Calculator**: PET-MAD via gulp-mlips-host
- **System**: Benzene (C₆H₆) molecular crystal (72 atoms)

## Usage

```bash
./run.sh
```

## Configuration

```bash
# Use GPU
DEVICE=cuda ./run.sh

# Different port
PORT=8194 ./run.sh
```

## Files

- `optimize.gin` - Full structure and cell optimization
- `single_point.gin` - Single point energy calculation only
- `run.sh` - Runs the example (starts server, runs GULP, cleans up)
- `gulp_mlips_wrapper.sh` - Interface between GULP and gulp-mlips-client
