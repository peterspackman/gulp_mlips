"""GULP backend for gulp-mlips using GULP's own force fields.

This backend allows using GULP itself as a calculator, which is useful for:
1. Testing the .drv file format (round-trip validation)
2. Using GULP's built-in force fields and potentials
3. Comparing ML potentials against traditional force fields

The backend uses a modified GULP calculator that reads from .drv files
for more reliable access to forces and stress.
"""

from typing import Optional, List, Dict, Any
import numpy as np
import os
import tempfile
import shutil
import logging

from gulp_mlips.backends.base import CalculatorBackend

logger = logging.getLogger(__name__)


class GULPBackend(CalculatorBackend):
    """GULP calculator backend using GULP's own potentials.

    This backend runs GULP as a subprocess and reads results from the
    .drv (derivative) file. It supports GULP's built-in potentials and
    force fields.

    Args:
        keywords: GULP keywords (e.g., 'opti conp', 'gradient', etc.)
        library: GULP library file to use
        options: Additional GULP options
        gulp_command: Command to run GULP (default: 'gulp')
    """

    def __init__(
        self,
        keywords: str = "conp gradient",
        library: Optional[str] = None,
        options: Optional[List[str]] = None,
        gulp_command: str = "gulp-6.3",
        **kwargs
    ):
        """Initialize GULP backend.

        Args:
            keywords: GULP calculation keywords
            library: Path to GULP library file
            options: List of additional GULP options
            gulp_command: Command to run GULP
            **kwargs: Additional arguments passed to base class
        """
        super().__init__(**kwargs)
        self.keywords = keywords
        self.library = library
        self.options = options or []
        self.gulp_command = gulp_command
        self._loaded = False
        self._temp_dir = None

    def load(self) -> None:
        """Load the GULP calculator."""
        if self._loaded:
            return

        # Check if GULP is available
        gulp_path = shutil.which(self.gulp_command)
        if gulp_path is None:
            raise RuntimeError(
                f"GULP not found. Please install GULP and ensure '{self.gulp_command}' "
                "is in your PATH."
            )

        logger.info(f"Loading GULP calculator")
        logger.info(f"  GULP executable: {gulp_path}")
        logger.info(f"  Keywords: {self.keywords}")
        if self.library:
            logger.info(f"  Library: {self.library}")

        # Set GULP_LIB environment variable if not set
        # This is needed for ASE's GULP calculator to work
        if 'GULP_LIB' not in os.environ:
            # Create an empty dummy library file
            os.environ['GULP_LIB'] = ""
            logger.info("  Note: GULP_LIB not set, using empty value")

        # Import here to avoid requiring gulp_drv_calculator at import time
        import sys
        import importlib.util

        # Load gulp_drv_calculator from the project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        gulp_drv_path = os.path.join(project_root, "gulp_drv_calculator.py")

        if not os.path.exists(gulp_drv_path):
            raise FileNotFoundError(
                f"gulp_drv_calculator.py not found at {gulp_drv_path}"
            )

        spec = importlib.util.spec_from_file_location("gulp_drv_calculator", gulp_drv_path)
        gulp_drv_module = importlib.util.module_from_spec(spec)
        sys.modules["gulp_drv_calculator"] = gulp_drv_module
        spec.loader.exec_module(gulp_drv_module)

        GULPDrvCalculator = gulp_drv_module.GULPDrvCalculator

        # Create temporary directory for GULP calculations
        self._temp_dir = tempfile.mkdtemp(prefix="gulp_backend_")

        # Create calculator
        self.calculator = GULPDrvCalculator(
            label=os.path.join(self._temp_dir, "gulp"),
            keywords=self.keywords,
            library=self.library,
            options=self.options,
        )

        # Set the command to use the specified GULP version
        # Expand ~ to home directory if present
        gulp_path_expanded = os.path.expanduser(gulp_path)
        self.calculator.command = f"{gulp_path_expanded} < PREFIX.gin > PREFIX.got"

        self._loaded = True
        logger.info(f"GULP calculator loaded successfully")

    def calculate(
        self,
        atoms,
        properties: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calculate properties for given structure.

        Args:
            atoms: ASE Atoms object
            properties: List of properties to calculate
                       Options: 'energy', 'forces', 'stress'

        Returns:
            Dictionary with calculated properties:
                - energy: Total energy in eV
                - forces: Forces on atoms in eV/Ang (Nx3 array)
                - stress: Stress tensor in eV/Ang^3 (6-component Voigt notation)
        """
        if not self._loaded:
            raise RuntimeError("Backend not loaded. Call load() first.")

        if properties is None:
            properties = ['energy', 'forces']

        # Attach calculator to atoms
        atoms.calc = self.calculator

        # Calculate requested properties
        results = {}

        if 'energy' in properties:
            results['energy'] = atoms.get_potential_energy()

        if 'forces' in properties:
            results['forces'] = atoms.get_forces()

        if 'stress' in properties:
            # Check if system is periodic and if stress is in keywords
            if any(atoms.get_pbc()) and 'stress' in self.keywords.lower():
                try:
                    results['stress'] = atoms.get_stress(voigt=True)
                except Exception as e:
                    logger.warning(f"Could not calculate stress: {e}")
                    # Return zero stress if calculation fails
                    results['stress'] = np.zeros(6)
            else:
                # Non-periodic system or stress not requested, return zero
                results['stress'] = np.zeros(6)

        return results

    def get_name(self) -> str:
        """Get backend name."""
        return "GULP"

    def get_version(self) -> str:
        """Get GULP version."""
        try:
            import subprocess
            result = subprocess.run(
                [self.gulp_command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Parse version from output
                for line in result.stdout.split('\n'):
                    if 'Version' in line or 'version' in line:
                        return line.strip()
                return result.stdout.split('\n')[0].strip()
            return "unknown"
        except:
            return "unknown"

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except:
                pass
        self.calculator = None
        self._loaded = False
        self._temp_dir = None

    def __repr__(self) -> str:
        """String representation."""
        status = "loaded" if self._loaded else "not loaded"
        return (
            f"GULPBackend(keywords='{self.keywords}', "
            f"library={self.library}, {status})"
        )

    def __del__(self):
        """Destructor to clean up temp directory."""
        self.cleanup()
