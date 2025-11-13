"""GFN-FF backend for gulp-mlips using xTB force field.

GFN-FF (Geometry, Frequency, Noncovalent, Force Field) is a semi-empirical
force field method from the xTB package. It's very fast and works well for
organic molecules and general chemistry.

References:
    - Spicher & Grimme, Angew. Chem. Int. Ed. 2020, 59, 15665
    - https://xtb-docs.readthedocs.io/
"""

import logging
from typing import Optional, List, Dict, Any
import numpy as np

from gulp_mlips.backends.base import CalculatorBackend

logger = logging.getLogger(__name__)


class GFNFFBackend(CalculatorBackend):
    """GFN-FF calculator backend using xTB.

    This backend uses the GFN-FF force field from the xTB package via ASE.
    GFN-FF is fast, covers the entire periodic table, and works well for:
    - Organic molecules
    - Biomolecules
    - General chemistry applications
    - Geometry optimizations
    - Vibrational frequencies

    Args:
        method: GFN method ('GFN-FF', 'GFN2-xTB', 'GFN1-xTB')
        accuracy: Numerical accuracy (default: 1.0, tighter: 0.1)
        electronic_temperature: Electronic temperature in Kelvin
        max_iterations: Maximum SCF iterations
        solvent: Implicit solvent model (e.g., 'water', 'acetonitrile')
    """

    def __init__(
        self,
        method: str = "GFN-FF",
        accuracy: float = 1.0,
        electronic_temperature: float = 300.0,
        max_iterations: int = 250,
        solvent: Optional[str] = None,
        **kwargs
    ):
        """Initialize GFN-FF backend.

        Args:
            method: xTB method to use (GFN-FF, GFN2-xTB, GFN1-xTB)
            accuracy: Numerical accuracy (lower = tighter)
            electronic_temperature: Electronic temperature in K
            max_iterations: Maximum SCF iterations
            solvent: Implicit solvent (e.g., 'water')
            **kwargs: Additional arguments passed to base class
        """
        super().__init__(**kwargs)
        self.method = method
        self.accuracy = accuracy
        self.electronic_temperature = electronic_temperature
        self.max_iterations = max_iterations
        self.solvent = solvent
        self._calculator = None
        self._loaded = False

    def load(self) -> None:
        """Load the xTB calculator."""
        if self._loaded:
            return

        try:
            from ase.calculators.xtb import XTB
        except ImportError:
            raise ImportError(
                "xTB calculator not available. Install with:\n"
                "  pip install xtb-python\n"
                "Or via conda:\n"
                "  conda install -c conda-forge xtb-python"
            )

        logger.info(f"Loading xTB calculator: method={self.method}")

        # Build calculator kwargs
        calc_kwargs = {
            'method': self.method,
            'accuracy': self.accuracy,
            'electronic_temperature': self.electronic_temperature,
            'max_iterations': self.max_iterations,
        }

        # Add solvent if specified
        if self.solvent:
            calc_kwargs['solvent'] = self.solvent
            logger.info(f"  Using implicit solvent: {self.solvent}")

        self._calculator = XTB(**calc_kwargs)
        self._loaded = True

        logger.info(f"xTB calculator loaded successfully")
        logger.info(f"  Method: {self.method}")
        logger.info(f"  Accuracy: {self.accuracy}")
        logger.info(f"  Electronic T: {self.electronic_temperature} K")

    @property
    def calculator(self):
        """Get the ASE calculator instance."""
        if not self._loaded:
            raise RuntimeError("Backend not loaded. Call load() first.")
        return self._calculator

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
        atoms.calc = self._calculator

        # Calculate requested properties
        results = {}

        if 'energy' in properties:
            results['energy'] = atoms.get_potential_energy()

        if 'forces' in properties:
            results['forces'] = atoms.get_forces()

        if 'stress' in properties:
            # Check if system is periodic
            if any(atoms.get_pbc()):
                try:
                    results['stress'] = atoms.get_stress(voigt=True)
                except Exception as e:
                    logger.warning(f"Could not calculate stress: {e}")
                    # Return zero stress if calculation fails
                    results['stress'] = np.zeros(6)
            else:
                # Non-periodic system, return zero stress
                results['stress'] = np.zeros(6)

        return results

    def get_name(self) -> str:
        """Get backend name."""
        return f"xTB-{self.method}"

    def get_version(self) -> str:
        """Get backend version."""
        try:
            import xtb
            return xtb.__version__
        except:
            return "unknown"

    def cleanup(self) -> None:
        """Clean up resources."""
        self._calculator = None
        self._loaded = False

    def __repr__(self) -> str:
        """String representation."""
        status = "loaded" if self._loaded else "not loaded"
        return (
            f"GFNFFBackend(method={self.method}, "
            f"solvent={self.solvent}, {status})"
        )
