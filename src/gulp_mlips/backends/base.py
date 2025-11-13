"""Base calculator backend interface for gulp-mlips.

All calculator backends should inherit from CalculatorBackend.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ase import Atoms
from ase.calculators.calculator import Calculator


class CalculatorBackend(ABC):
    """Abstract base class for calculator backends.

    Each backend (e.g., PET-MAD, MACE, etc.) should implement this interface.
    """

    def __init__(self, **kwargs):
        """Initialize the calculator backend.

        Args:
            **kwargs: Backend-specific configuration options
        """
        self.config = kwargs
        self.calculator: Optional[Calculator] = None

    @abstractmethod
    def load(self) -> None:
        """Load the calculator/model.

        This is called once when the host server starts.
        The calculator should be stored in self.calculator.

        Raises:
            RuntimeError: If loading fails
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this calculator backend.

        Returns:
            Name string (e.g., "PET-MAD", "MACE", etc.)
        """
        pass

    def get_version(self) -> str:
        """Get version information for this backend.

        Returns:
            Version string
        """
        return "unknown"

    def is_loaded(self) -> bool:
        """Check if calculator is loaded.

        Returns:
            True if calculator is ready to use
        """
        return self.calculator is not None

    def calculate(
        self,
        atoms: Atoms,
        properties: list[str] = ["energy", "forces"],
    ) -> Dict[str, Any]:
        """Calculate properties for given atoms.

        Args:
            atoms: ASE Atoms object
            properties: List of properties to calculate
                       Typical values: ["energy", "forces", "stress"]

        Returns:
            Dictionary with calculated properties:
            - "energy": float (in eV)
            - "forces": np.ndarray (Nx3, in eV/Ang)
            - "stress": np.ndarray (6-component Voigt, in eV/Ang^3) [optional]

        Raises:
            RuntimeError: If calculator is not loaded or calculation fails
        """
        if not self.is_loaded():
            raise RuntimeError("Calculator not loaded. Call load() first.")

        if self.calculator is None:
            raise RuntimeError("Calculator is None")

        # Attach calculator to atoms
        atoms.calc = self.calculator

        # Calculate requested properties
        results = {}

        if "energy" in properties:
            results["energy"] = atoms.get_potential_energy()

        if "forces" in properties:
            results["forces"] = atoms.get_forces()

        if "stress" in properties:
            # Only calculate stress for periodic systems
            if any(atoms.get_pbc()):
                results["stress"] = atoms.get_stress(voigt=True)
            else:
                results["stress"] = None

        return results

    def cleanup(self) -> None:
        """Clean up resources.

        Override this if your backend needs cleanup (e.g., closing files, etc.)
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.get_name()}, loaded={self.is_loaded()})"
