# FairChem UMA Example

This example demonstrates using GULP with UMA as the force calculator.

## What This Does

- **Outer GULP**: Performs geometry optimization
- **Inner Calculator**: FairChem UMA-S model via gulp-mlips-host
- **System**: Silicon diamond structure (bulk material)

This example uses:
- Model: `uma-s-1p1` (small, 'fast')
- Task: `omat` (materials/crystals)
- Device: `cpu`

## Requirements

1. Install FairChem backend:
   ```bash
   uv pip install 'gulp-mlips[fairchem]'
   # or 
   uv pip install fairchem-core
   ```

2. Authenticate with HuggingFace:
   ```bash
   huggingface-cli login
   ```

3. Request access to UMA models:
   https://huggingface.co/facebook/UMA

## Usage

Simply run the example script:

```bash
./run.sh
```

This will:
1. Start the UMA backend server in the background
2. Download the model on first run (~100MB for uma-s-1p1)
3. Run the GULP optimization
4. Clean up and stop the server when done

All output is saved to `optimize.gout` and server logs to `host.log`.

## Configuration

The `run.sh` script accepts environment variables:

```bash
# Use GPU
DEVICE=cuda ./run.sh

# Use larger model (more accurate, slower)
MODEL=uma-m-1p1 ./run.sh

# Different port
PORT=8194 ./run.sh
```
