"""PET-MAD calculator backend for gulp-mlips."""

import logging
from typing import Optional
from .base import CalculatorBackend

logger = logging.getLogger(__name__)


class PETMADBackend(CalculatorBackend):
    """PET-MAD calculator backend.

    Uses the pet-mad package via ASE calculator interface.
    """

    def __init__(
        self,
        version: str = "latest",
        device: str = "cpu",
        **kwargs
    ):
        """Initialize PET-MAD backend.

        Args:
            version: PET-MAD model version ("latest", "v1.0", etc.)
            device: Device to use ("cpu", "cuda", etc.)
            **kwargs: Additional arguments passed to PETMADCalculator
        """
        super().__init__(version=version, device=device, **kwargs)
        self.version = version
        self.device = device

    def load(self) -> None:
        """Load PET-MAD calculator.

        Raises:
            ImportError: If pet-mad is not installed
            RuntimeError: If loading fails
        """
        try:
            from pet_mad.calculator import PETMADCalculator
        except ImportError as e:
            raise ImportError(
                "pet-mad package not installed. "
                "Install with: pip install 'gulp-mlips[petmad]' or pip install pet-mad"
            ) from e

        try:
            logger.info(f"Loading PET-MAD calculator: version={self.version}, device={self.device}")
            self.calculator = PETMADCalculator(
                version=self.version,
                device=self.device,
                **{k: v for k, v in self.config.items() if k not in ['version', 'device']}
            )
            logger.info("PET-MAD calculator loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load PET-MAD calculator: {e}") from e

    def get_name(self) -> str:
        """Get backend name.

        Returns:
            "PET-MAD"
        """
        return "PET-MAD"

    def get_version(self) -> str:
        """Get PET-MAD version.

        Returns:
            Version string
        """
        return self.version
