"""FairChem UMA (Universal Model for Atoms) calculator backend for gulp-mlips.

FairChem UMA models are state-of-the-art universal models trained on billions of atoms
across multiple FAIR Chemistry datasets (OC20, ODAC23, OMat24, OMC25, OMol25).

Requirements:
- fairchem-core package
- HuggingFace account with access to facebook/UMA models
- HuggingFace authentication (huggingface-cli login)
"""

import logging
from typing import Optional
from .base import CalculatorBackend

logger = logging.getLogger(__name__)


class FairChemBackend(CalculatorBackend):
    """FairChem UMA calculator backend.

    Uses the fairchem-core package with UMA models via ASE FAIRChemCalculator interface.
    """

    AVAILABLE_MODELS = {
        "uma-s-1p1": {
            "description": "UMA Small v1.1 (recommended small model)",
            "size": "~100M parameters",
        },
        "uma-m-1p1": {
            "description": "UMA Medium v1.1 (larger, more accurate)",
            "size": "~300M parameters",
        },
        # uma-l coming soon
    }

    AVAILABLE_TASKS = {
        "oc20": "Catalysis (surfaces with adsorbates)",
        "omat": "Inorganic materials (bulk crystals)",
        "omol": "Molecules (small organic molecules)",
        "odac": "MOFs (metal-organic frameworks)",
        "omc": "Molecular crystals",
    }

    def __init__(
        self,
        model: str = "uma-s-1p1",
        task: str = "omat",
        device: str = "cpu",
        **kwargs
    ):
        """Initialize FairChem UMA backend.

        Args:
            model: Model variant ('uma-s-1p1', 'uma-m-1p1')
            task: Task name for domain-specific prediction:
                  - 'oc20': catalysis (surfaces/adsorbates)
                  - 'omat': inorganic materials (bulk crystals)
                  - 'omol': molecules
                  - 'odac': MOFs
                  - 'omc': molecular crystals
            device: Device to use ("cpu", "cuda", etc.)
            **kwargs: Additional arguments

        Note:
            Requires HuggingFace authentication. Run:
                huggingface-cli login
            and request access at: https://huggingface.co/facebook/UMA
        """
        super().__init__(model=model, task=task, device=device, **kwargs)
        self.model_name = model
        self.task_name = task
        self.device = device

        # Validate model choice
        if model not in self.AVAILABLE_MODELS:
            available = ", ".join(self.AVAILABLE_MODELS.keys())
            raise ValueError(
                f"Unknown model: {model}. "
                f"Available models: {available}"
            )

        # Validate task choice
        if task not in self.AVAILABLE_TASKS:
            available = ", ".join(self.AVAILABLE_TASKS.keys())
            raise ValueError(
                f"Unknown task: {task}. "
                f"Available tasks: {available}. "
                f"Use 'omat' for bulk materials, 'oc20' for catalysis, 'omol' for molecules."
            )

    def load(self) -> None:
        """Load FairChem UMA calculator.

        Raises:
            ImportError: If fairchem-core is not installed
            RuntimeError: If loading fails (e.g., HuggingFace auth issues)
        """
        try:
            from fairchem.core import pretrained_mlip, FAIRChemCalculator
        except ImportError as e:
            raise ImportError(
                "fairchem-core package not installed. "
                "Install with: pip install 'gulp-mlips[fairchem]' or pip install fairchem-core\n"
                "Also requires HuggingFace authentication: huggingface-cli login"
            ) from e

        try:
            model_info = self.AVAILABLE_MODELS[self.model_name]
            task_desc = self.AVAILABLE_TASKS[self.task_name]

            logger.info(f"Loading FairChem UMA model: {self.model_name}")
            logger.info(f"  Description: {model_info['description']}")
            logger.info(f"  Size: {model_info['size']}")
            logger.info(f"  Task: {self.task_name} ({task_desc})")
            logger.info(f"  Device: {self.device}")
            logger.info("Note: First-time download may take a few minutes...")

            # Load the predictor unit
            predictor = pretrained_mlip.get_predict_unit(
                self.model_name,
                device=self.device
            )

            # Create calculator with task-specific settings
            self.calculator = FAIRChemCalculator(
                predictor,
                task_name=self.task_name
            )

            logger.info("FairChem UMA calculator loaded successfully")

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "authentication" in error_msg.lower():
                raise RuntimeError(
                    "HuggingFace authentication failed. "
                    "Please run: huggingface-cli login\n"
                    "And request access at: https://huggingface.co/facebook/UMA"
                ) from e
            else:
                raise RuntimeError(f"Failed to load FairChem UMA calculator: {e}") from e

    def get_name(self) -> str:
        """Get backend name.

        Returns:
            "FairChem-UMA-{model}-{task}"
        """
        return f"FairChem-UMA-{self.model_name}-{self.task_name}"

    def get_version(self) -> str:
        """Get FairChem model version.

        Returns:
            Model name string
        """
        return self.model_name

    @classmethod
    def list_models(cls) -> None:
        """Print available FairChem UMA models and tasks."""
        logger.info("\n" + "=" * 80)
        logger.info("FairChem UMA (Universal Model for Atoms)")
        logger.info("=" * 80)

        logger.info("\nAvailable Models:")
        logger.info("-" * 80)
        for name, info in cls.AVAILABLE_MODELS.items():
            logger.info(f"\n  {name}:")
            logger.info(f"    Description: {info['description']}")
            logger.info(f"    Size: {info['size']}")

        logger.info("\n\nAvailable Tasks:")
        logger.info("-" * 80)
        for task, desc in cls.AVAILABLE_TASKS.items():
            logger.info(f"  {task:8s} - {desc}")

        logger.info("\n" + "=" * 80)
        logger.info("Usage Examples:")
        logger.info("  # For bulk materials (default)")
        logger.info("  gulp-mlips-host --backend fairchem --model uma-s-1p1 --task omat")
        logger.info("\n  # For molecules")
        logger.info("  gulp-mlips-host --backend fairchem --model uma-s-1p1 --task omol")
        logger.info("\n  # For catalysis (surfaces)")
        logger.info("  gulp-mlips-host --backend fairchem --model uma-m-1p1 --task oc20")
        logger.info("=" * 80)
        logger.info("\nRequirements:")
        logger.info("  1. Install: pip install fairchem-core")
        logger.info("  2. Login: huggingface-cli login")
        logger.info("  3. Request access: https://huggingface.co/facebook/UMA")
        logger.info("=" * 80 + "\n")
