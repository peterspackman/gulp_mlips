# GULP GFN-FF Backend Example

Round-trip validation test for .drv file format using GULP's GFN-FF force field.

## What This Tests

This runs **two GULP instances**:

1. **Outer GULP** (optimizer) - Reads optimize.gin, performs optimization
2. **Inner GULP** (force calculator) - Runs via gulp-mlips-host with `gfnff` keyword

The flow:
```
Outer GULP → gulp_mlips_wrapper.sh → gulp-mlips-client
    → HTTP → gulp-mlips-host (GULP backend)
    → Inner GULP with gfnff → writes .drv file
    → gulp_drv_calculator reads .drv → converts gradients to forces
    → returns via HTTP → gulp-mlips-client writes gulp_mlip.drv
    → Outer GULP reads gulp_mlip.drv → optimization step
```

This validates that our .drv file reader correctly handles:
- Energy values
- Gradient → force conversion (sign flip)
- Stress tensor conversion

## Usage

```bash
./run.sh
```

## Manual Run

```bash
# Start gulp-mlips-host with GULP backend
gulp-mlips-host --backend gulp --keywords "gradient gfnff" --port 8193 &

# Run outer GULP
export HOST=127.0.0.1 PORT=8193
gulp < optimize.gin > optimize.gout

# Stop server
killall gulp-mlips-host
```

## Why This Matters

If this example works, it proves that:
1. Our gulp_drv_calculator correctly reads GULP's .drv format
2. Sign conventions are correct (GULP gradients = -forces)
3. The round-trip conversion is correct
4. Any GULP-compatible force field can be used as a backend
