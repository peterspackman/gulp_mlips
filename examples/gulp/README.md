# GULP Integration Examples

This directory contains examples demonstrating how to use gulp-mlips with GULP's external program interface for machine learning interatomic potential calculations.

## Directory Structure

Each example is self-contained in its own directory with all necessary files:

```
examples/gulp/
├── benzene/          # Organic molecular crystal with PET-MAD
│   ├── README.md
│   ├── run.sh
│   ├── optimize.gin
│   ├── single_point.gin
│   └── gulp_mlips_wrapper.sh
│
├── al2o3/            # Inorganic crystal with FairChem
│   ├── README.md
│   ├── run.sh
│   ├── optimize.gin
│   └── gulp_mlips_wrapper.sh
│
└── si_diamond/       # Simple elemental crystal (works with both backends)
    ├── README.md
    ├── run.sh
    ├── optimize.gin
    └── gulp_mlips_wrapper.sh
```

## Available Examples

### 1. Benzene Crystal ([benzene/](benzene/))

**System**: Organic molecular crystal (C₆H₆)
**Backend**: PET-MAD (Pre-trained Equivariant Transformer)
**Demonstrates**: Molecular crystal optimization, organic materials

```bash
cd benzene
./run.sh
```

PET-MAD is optimized for organic molecules and molecular dynamics. This example shows:
- Full structure and cell optimization
- Orthorhombic crystal system
- 72 atoms (4 benzene molecules)
- Good convergence properties

**See**: [benzene/README.md](benzene/README.md) for details

### 2. Al₂O₃ Corundum ([al2o3/](al2o3/))

**System**: Inorganic ionic crystal (alumina)
**Backend**: FairChem UMA (Universal Materials Accelerator)
**Demonstrates**: Symmetry handling, inorganic materials, DFT-quality predictions

```bash
cd al2o3
./run.sh
```

FairChem is trained on large-scale DFT datasets and excels at inorganic materials. This example shows:
- GULP symmetry operations (R-3c space group)
- Asymmetric unit (2 atoms) expanded by symmetry
- Constant pressure optimization
- DFT-level accuracy

**See**: [al2o3/README.md](al2o3/README.md) for details

### 3. Silicon Diamond ([si_diamond/](si_diamond/))

**System**: Elemental crystal (Si)
**Backend**: PET-MAD or FairChem (configurable)
**Demonstrates**: Cell parameter optimization, simple test case

```bash
cd si_diamond
./run.sh                    # Uses PET-MAD
BACKEND=fairchem ./run.sh   # Uses FairChem
```

Silicon diamond is an excellent test case with:
- Simple cubic structure (8 atoms)
- Well-known experimental value (a = 5.431 Å)
- Starts compressed (a = 5.0 Å) and optimizes to near-experimental
- Fast convergence
- Works well with both backends

**See**: [si_diamond/README.md](si_diamond/README.md) for details

## Quick Start

### Simplest Usage

```bash
# 1. Choose an example
cd benzene/  # or al2o3/ or si_diamond/

# 2. Run it
./run.sh

# Done! The script handles everything automatically.
```

Each `run.sh` script will:
1. Check prerequisites (GULP, gulp-mlips installed)
2. Start the appropriate ML potential server
3. Run GULP optimization
4. Display results
5. Clean up automatically on exit

### Customization

All examples support environment variables:

```bash
# Use GPU instead of CPU
DEVICE=cuda ./run.sh

# Change port (if 8193 is already in use)
PORT=8194 ./run.sh

# Combine multiple options
DEVICE=cuda PORT=8194 ./run.sh
```

For si_diamond, you can also change the backend:

```bash
cd si_diamond/
BACKEND=fairchem MODEL=uma-m-1p1 ./run.sh
```

## How It Works

### GULP's External Program Interface

GULP supports calling external programs for energy/force calculations:

```
.gin file contains:
  external_call
  ./gulp_mlips_wrapper.sh
  end
  external_drv gulp_mlip.drv
```

### The Workflow

```
GULP              Wrapper              Client            Server            MLIP
  |                  |                    |                 |                 |
  |-- gulpext.xyz -->|                    |                 |                 |
  |                  |-- HTTP request --->|                 |                 |
  |                  |                    |-- structure --->|                 |
  |                  |                    |                 |-- compute ----->|
  |                  |                    |<-- E,F,stress --|                 |
  |<- gulp_mlip.drv -|                    |                 |                 |
  |                  |                    |                 |                 |
  └─ next step
```

1. **GULP writes** structure to `gulpext.xyz`
2. **Wrapper calls** `gulp-mlips-client`
3. **Client sends** HTTP request to server
4. **Server** runs ML potential calculation
5. **Client writes** energy/forces to `gulp_mlip.drv`
6. **GULP reads** results and continues optimization

### File Format

The `.drv` file format GULP expects:

```
energy                  -944.0943568110 eV
coordinates cartesian Angstroms     30
     1  13      0.00000000      0.00000000      4.57572053
     2  13      2.38010000      1.37415138      8.90682053
     ...
gradients cartesian eV/Ang     30
     1     -0.00000000      0.00000000     -1.96906188
     2     -0.00000000      0.00000000     -1.96906188
     ...
gradients strain eV
    -15.58105869    -15.58105874    -22.54759060
      0.00000000     -0.00000001     -0.00000004
```

- **Coordinates**: Atomic number + Cartesian positions
- **Gradients**: Forces in eV/Å (note: gradients = -forces in GULP)
- **Strain gradients**: Stress × volume (for cell optimization)

## Choosing a Backend

### PET-MAD

**Best for**:
- Organic molecules
- Molecular crystals
- Molecular dynamics
- Systems with H, C, N, O, S, F, Cl, Br, I

**Characteristics**:
- Fast loading (~5 seconds)
- Fast inference
- Trained on molecular dynamics trajectories
- Good for dynamics properties

**Example systems**: benzene, aspirin, DNA, proteins, organic semiconductors

### FairChem UMA

**Best for**:
- Inorganic crystals
- Metals and alloys
- Oxides, nitrides, carbides
- Catalysis and surfaces

**Characteristics**:
- Slower loading (~10-30 seconds, model download on first use)
- Fast inference
- Trained on large-scale DFT calculations
- DFT-quality predictions

**Model sizes**:
- `uma-s-1p1`: Small, fast (~2M parameters)
- `uma-m-1p1`: Medium, balanced (~8M parameters)
- `uma-l-1p1`: Large, most accurate (~32M parameters)

**Task types**:
- `omat`: Open Materials (bulk inorganics)
- `omol`: Open Molecules (organic molecules)
- `oc20`: Catalysis (OC20 dataset)

**Example systems**: Si, Al₂O₃, TiO₂, ZnO, catalytic surfaces

## Manual Usage (Without run.sh)

If you prefer more control or want to understand the process:

### Step 1: Start the Server

For PET-MAD:
```bash
gulp-mlips-host --backend petmad --device cpu --port 8193 &
```

For FairChem:
```bash
gulp-mlips-host --backend fairchem --model uma-s-1p1 --task omat \
    --device cpu --port 8193 &
```

### Step 2: Set Environment Variables

```bash
export HOST=127.0.0.1
export PORT=8193
```

### Step 3: Run GULP

```bash
cd benzene/  # or whichever example
gulp < optimize.gin > optimize.gout
```

### Step 4: Stop the Server

```bash
killall gulp-mlips-host
```

## Troubleshooting

### Server Issues

**Error: "Cannot connect to server"**
- Check if server is running: `curl http://127.0.0.1:8193/health`
- Verify port matches in wrapper and server
- Check `host.log` for server errors

**Error: "Port already in use"**
- Find process: `lsof -i :8193`
- Kill it: `kill <PID>` or use different port: `PORT=8194 ./run.sh`

**Server won't start**
- Check `host.log` for error messages
- For FairChem: May need to download model on first use (~100-500 MB)
- Try with CPU first: `DEVICE=cpu ./run.sh`

### GULP Issues

**Error: "Input file gulpext.xyz not found"**
- GULP didn't write the structure file
- Check GULP has write permissions
- Check GULP output for earlier errors

**Error: "wrapper not found"**
- Make wrapper executable: `chmod +x gulp_mlips_wrapper.sh`
- Run GULP from same directory as wrapper

**Optimization won't converge**
- Check if structure is reasonable
- Try different backend
- Increase `maxcyc` in .gin file
- See example-specific README for tips

### Results Issues

**Wrong predictions**
- Check backend is appropriate for your system type
- PET-MAD: organics; FairChem omat: inorganics
- Try different FairChem model: `MODEL=uma-m-1p1 ./run.sh`

**"Ill conditioned Hessian" warnings**
- Common for inorganic crystals
- May indicate stress prediction issues
- Try position-only optimization (change `conp` to `conv`)

## Performance Tips

1. **Use GPU**: 10-50× faster than CPU
   ```bash
   DEVICE=cuda ./run.sh
   ```

2. **Keep server running**: Start once, run multiple GULP jobs
   ```bash
   gulp-mlips-host --backend petmad --port 8193 &
   cd benzene && gulp < optimize.gin > optimize.gout
   cd ../si_diamond && gulp < optimize.gin > optimize.gout
   ```

3. **Use appropriate model size**: For FairChem, `uma-s` is often sufficient
   ```bash
   MODEL=uma-s-1p1 ./run.sh  # Fastest
   MODEL=uma-m-1p1 ./run.sh  # Balanced
   MODEL=uma-l-1p1 ./run.sh  # Most accurate
   ```

4. **Profile first**: Test with small system to estimate runtime

## Advanced Usage

### Debug Mode

Enable detailed output:

```bash
export DEBUG=1
./run.sh
```

This shows:
- Wrapper script operations
- File I/O details
- Server communication

### Creating Your Own Example

1. Copy an existing example directory:
   ```bash
   cp -r benzene/ my_system/
   cd my_system/
   ```

2. Modify `optimize.gin` with your structure

3. Update `run.sh` if needed (backend, ports, etc.)

4. Test it:
   ```bash
   ./run.sh
   ```

### Parallel GULP Jobs

Run multiple optimizations with shared server:

```bash
# Start server
gulp-mlips-host --backend petmad --port 8193 &

# Run jobs in parallel
cd benzene && gulp < optimize.gin > optimize.gout &
cd ../si_diamond && gulp < optimize.gin > optimize.gout &
wait

# Clean up
killall gulp-mlips-host
```

### Integration with Workflows

The wrapper can be used in automated workflows:

```bash
#!/bin/bash
# optimize_all.sh

gulp-mlips-host --backend fairchem --model uma-s-1p1 --task omat --port 8193 &
SERVER_PID=$!
sleep 10

for system in system_*.gin; do
    echo "Optimizing $system..."
    export PORT=8193
    gulp < "$system" > "${system%.gin}.gout"
done

kill $SERVER_PID
```

## Output Files

After running an example, you'll see:

- **`optimize.gout`** - Full GULP output log
- **`*.xyz`** - Optimized structure in XYZ format
- **`*.cif`** - Crystallographic information file
- **`*.drv`** - Energy/force trajectory
- **`host.log`** - Server log
- **`gulp_mlip.drv`** - Most recent MLIP calculation
- **`gulpext.xyz`** - Most recent structure sent to MLIP

Generated files are ignored by `.gitignore`.

## References

- **GULP**: https://gulp.curtin.edu.au/
- **PET-MAD**: Pre-trained Equivariant Transformers for Molecular Atomic Dynamics
- **FairChem**: https://fair-chem.github.io/
- **gulp-mlips**: Machine learning interatomic potential server/client

## See Also

- Main gulp-mlips documentation: `../../README.md`
- Python API examples: `../python/`
- Test scripts: `../../test_*.py`

---

**Need Help?** Check the example-specific README files for detailed information and troubleshooting for each system type.
