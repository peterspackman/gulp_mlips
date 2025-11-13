"""Model initialization script for gulp-mlips.

Pre-downloads and initializes MLIP models to avoid delays during first use.
This is especially useful for FairChem UMA models which can be large.
"""

import sys
import logging
import argparse
from typing import Optional

logger = logging.getLogger(__name__)


def init_petmad(version: str = "latest", device: str = "cpu") -> bool:
    """Initialize PET-MAD model.

    Args:
        version: Model version
        device: Device to use

    Returns:
        True if successful
    """
    logger.info("\n" + "=" * 80)
    logger.info("Initializing PET-MAD Model")
    logger.info("=" * 80)

    try:
        from gulp_mlips.backends.petmad import PETMADBackend

        logger.info(f"Version: {version}")
        logger.info(f"Device: {device}")
        logger.info("\nLoading model (this may take a while on first run)...")

        backend = PETMADBackend(version=version, device=device)
        backend.load()

        logger.info(f"\n✓ PET-MAD model initialized successfully!")
        logger.info(f"  Backend: {backend.get_name()}")
        logger.info(f"  Version: {backend.get_version()}")

        backend.cleanup()
        return True

    except ImportError as e:
        logger.error(f"\n✗ Error: {e}")
        logger.info("\nInstall PET-MAD with: uv pip install 'gulp-mlips[petmad]'")
        return False
    except Exception as e:
        logger.error(f"\n✗ Failed to initialize PET-MAD: {e}")
        return False


def init_fairchem(
    model: str = "uma-s-1p1",
    task: str = "omat",
    device: str = "cpu"
) -> bool:
    """Initialize FairChem UMA model.

    Args:
        model: Model name
        task: Task name
        device: Device to use

    Returns:
        True if successful
    """
    logger.info("\n" + "=" * 80)
    logger.info("Initializing FairChem UMA Model")
    logger.info("=" * 80)

    try:
        from gulp_mlips.backends.fairchem import FairChemBackend

        logger.info(f"Model: {model}")
        logger.info(f"Task: {task}")
        logger.info(f"Device: {device}")
        logger.info("\nChecking HuggingFace authentication...")

        backend = FairChemBackend(model=model, task=task, device=device)

        logger.info("\nLoading model (first download may take several minutes)...")
        logger.info("Model will be cached for future use.")

        backend.load()

        logger.info(f"\n✓ FairChem UMA model initialized successfully!")
        logger.info(f"  Backend: {backend.get_name()}")
        logger.info(f"  Version: {backend.get_version()}")

        backend.cleanup()
        return True

    except ImportError as e:
        logger.error(f"\n✗ Error: {e}")
        logger.info("\nInstall FairChem with: uv pip install 'gulp-mlips[fairchem]'")
        return False
    except RuntimeError as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower():
            logger.error(f"\n✗ HuggingFace Authentication Required")
            logger.info("\nPlease follow these steps:")
            logger.info("  1. Create a HuggingFace account: https://huggingface.co/join")
            logger.info("  2. Request access to UMA models: https://huggingface.co/facebook/UMA")
            logger.info("  3. Create an access token: https://huggingface.co/settings/tokens")
            logger.info("  4. Login with: huggingface-cli login")
            logger.info("\nThen run this script again.")
        else:
            logger.error(f"\n✗ Failed to initialize FairChem: {e}")
        return False
    except Exception as e:
        logger.error(f"\n✗ Failed to initialize FairChem: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_available_models() -> None:
    """List all available models for all backends."""
    logger.info("\n" + "=" * 80)
    logger.info("Available Models")
    logger.info("=" * 80)

    # PET-MAD
    logger.info("\nPET-MAD:")
    logger.info("  Models: latest, v1.0, etc.")
    logger.info("  Install: uv pip install 'gulp-mlips[petmad]'")
    logger.info("  Init: gulp-mlips-init --backend petmad")

    # FairChem
    logger.info("\nFairChem UMA:")
    try:
        from gulp_mlips.backends.fairchem import FairChemBackend
        FairChemBackend.list_models()
    except ImportError:
        logger.info("  Not installed. Install with: uv pip install 'gulp-mlips[fairchem]'")

    logger.info("")


def main():
    """Main entry point for model initialization."""
    parser = argparse.ArgumentParser(
        description="Initialize and download MLIP models for gulp-mlips",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize PET-MAD (default)
  gulp-mlips-init --backend petmad

  # Initialize FairChem UMA for materials
  gulp-mlips-init --backend fairchem --model uma-s-1p1 --task omat

  # Initialize FairChem UMA medium model for molecules on GPU
  gulp-mlips-init --backend fairchem --model uma-m-1p1 --task omol --device cuda

  # List available models
  gulp-mlips-init --list

Note:
  FairChem models require HuggingFace authentication.
  Run 'huggingface-cli login' before initializing.
        """
    )

    parser.add_argument(
        '--backend',
        choices=['petmad', 'fairchem'],
        help='Backend to initialize'
    )
    parser.add_argument(
        '--version',
        default='latest',
        help='Model version (for PET-MAD)'
    )
    parser.add_argument(
        '--model',
        default='uma-s-1p1',
        help='Model name (for FairChem: uma-s-1p1, uma-m-1p1)'
    )
    parser.add_argument(
        '--task',
        default='omat',
        help='Task name (for FairChem: omat, omol, oc20, odac, omc)'
    )
    parser.add_argument(
        '--device',
        default='cpu',
        choices=['cpu', 'cuda'],
        help='Device to use (default: cpu)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available models'
    )

    args = parser.parse_args()

    # Configure logging for this CLI script
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    if args.list:
        list_available_models()
        return

    if not args.backend:
        logger.error("Error: --backend required (or use --list)")
        parser.print_help()
        sys.exit(1)

    logger.info("\ngulp-mlips Model Initialization")
    logger.info("This will download and cache the model for future use.")

    success = False

    if args.backend == 'petmad':
        success = init_petmad(
            version=args.version,
            device=args.device
        )
    elif args.backend == 'fairchem':
        success = init_fairchem(
            model=args.model,
            task=args.task,
            device=args.device
        )

    logger.info("\n" + "=" * 80)
    if success:
        logger.info("Initialization Complete!")
        logger.info("\nYou can now start the host server with:")
        if args.backend == 'petmad':
            logger.info(f"  gulp-mlips-host --backend petmad --device {args.device}")
        elif args.backend == 'fairchem':
            logger.info(f"  gulp-mlips-host --backend fairchem --model {args.model} --task {args.task} --device {args.device}")
    else:
        logger.error("Initialization Failed")
        logger.error("Please check the error messages above.")
        sys.exit(1)

    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    main()
