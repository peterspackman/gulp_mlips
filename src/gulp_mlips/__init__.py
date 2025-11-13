"""gulp-mlips: GULP-compatible calculator interface for Machine Learning Interatomic Potentials.

This package provides a client-host architecture for using MLIP calculators with GULP.
The host server keeps the MLIP model loaded in memory, avoiding repeated initialization overhead.

Usage:
    # Start host server
    gulp-mlips-host --backend petmad --device cpu --port 8193

    # Use client to perform calculation
    gulp-mlips-client input.xyz output.drv --port 8193
"""

__version__ = "0.1.0"

from gulp_mlips.formats.readers import read_xyz, read_structure
from gulp_mlips.formats.drv import write_drv
from gulp_mlips.backends.base import CalculatorBackend
from gulp_mlips.backends.petmad import PETMADBackend

__all__ = [
    "read_xyz",
    "read_structure",
    "write_drv",
    "CalculatorBackend",
    "PETMADBackend",
]
