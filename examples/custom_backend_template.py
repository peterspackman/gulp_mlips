"""Template for creating a custom calculator backend for gulp-mlips.

This file shows how to create a custom backend for your own MLIP calculator.

To use:
1. Copy this file to src/gulp_mlips/backends/my_backend.py
2. Rename MyCustomBackend to your backend name
3. Implement the load() method to initialize your calculator
4. Register it in src/gulp_mlips/host.py
5. Test with: gulp-mlips-host --backend my_backend

Example backends to reference:
- src/gulp_mlips/backends/petmad.py (simple backend)
- src/gulp_mlips/backends/fairchem.py (complex backend with multiple models)
"""

from typing import Optional
from gulp_mlips.backends.base import CalculatorBackend


class MyCustomBackend(CalculatorBackend):
    """Custom calculator backend.

    Replace this docstring with a description of your calculator.
    """

    def __init__(
        self,
        model: str = "default",
        device: str = "cpu",
        # Add any other configuration options your backend needs
        **kwargs
    ):
        """Initialize custom backend.

        Args:
            model: Model name or path
            device: Device to use ("cpu", "cuda", etc.)
            **kwargs: Additional configuration options
        """
        super().__init__(model=model, device=device, **kwargs)
        self.model_name = model
        self.device = device

    def load(self) -> None:
        """Load your calculator.

        This method must:
        1. Import your calculator package
        2. Initialize the calculator
        3. Set self.calculator to your ASE-compatible calculator

        Raises:
            ImportError: If your calculator package is not installed
            RuntimeError: If loading fails
        """
        # Example implementation:
        try:
            # Import your calculator
            # from my_calculator_package import MyCalculator
            raise ImportError("Replace this with your calculator import")

        except ImportError as e:
            raise ImportError(
                "my-calculator package not installed. "
                "Install with: pip install my-calculator"
            ) from e

        try:
            print(f"Loading MyCalculator model: {self.model_name}")
            print(f"  Device: {self.device}")

            # Initialize your calculator
            # self.calculator = MyCalculator(
            #     model=self.model_name,
            #     device=self.device,
            #     **self.config  # Pass additional config options
            # )

            # For this template, we'll use a dummy calculator
            # Replace this with your actual calculator!
            raise NotImplementedError("Implement your calculator loading here")

            print("MyCalculator loaded successfully")

        except Exception as e:
            raise RuntimeError(f"Failed to load MyCalculator: {e}") from e

    def get_name(self) -> str:
        """Get backend name.

        Returns:
            Name to display in logs and responses
        """
        return f"MyCustom-{self.model_name}"

    def get_version(self) -> str:
        """Get backend version.

        Returns:
            Version string
        """
        return self.model_name


# ============================================================================
# Example: Simple wrapper around existing ASE calculator
# ============================================================================

class SimpleASEBackend(CalculatorBackend):
    """Example: Wrap an existing ASE calculator.

    This shows how to use any ASE calculator with gulp-mlips.
    """

    def __init__(self, calculator_name: str = "EMT", **kwargs):
        """Initialize with ASE calculator name.

        Args:
            calculator_name: Name of ASE calculator ("EMT", "LJ", etc.)
            **kwargs: Calculator-specific arguments
        """
        super().__init__(calculator_name=calculator_name, **kwargs)
        self.calculator_name = calculator_name

    def load(self) -> None:
        """Load ASE calculator."""
        try:
            from ase.calculators.emt import EMT
            from ase.calculators.lj import LennardJones

        except ImportError as e:
            raise ImportError("ASE not installed") from e

        try:
            print(f"Loading ASE calculator: {self.calculator_name}")

            # Simple example: EMT calculator
            if self.calculator_name == "EMT":
                self.calculator = EMT()

            # Example with LJ parameters
            elif self.calculator_name == "LJ":
                # You can pass parameters from config
                epsilon = self.config.get('epsilon', 1.0)
                sigma = self.config.get('sigma', 1.0)
                self.calculator = LennardJones(epsilon=epsilon, sigma=sigma)

            else:
                raise ValueError(f"Unknown calculator: {self.calculator_name}")

            print(f"ASE {self.calculator_name} calculator loaded")

        except Exception as e:
            raise RuntimeError(f"Failed to load calculator: {e}") from e

    def get_name(self) -> str:
        return f"ASE-{self.calculator_name}"

    def get_version(self) -> str:
        return "ASE"


# ============================================================================
# Example: Backend with model file loading
# ============================================================================

class FileBasedBackend(CalculatorBackend):
    """Example: Backend that loads a model from a file."""

    def __init__(
        self,
        model_path: str,
        device: str = "cpu",
        **kwargs
    ):
        """Initialize with path to model file.

        Args:
            model_path: Path to model checkpoint file
            device: Device to use
            **kwargs: Additional options
        """
        super().__init__(model_path=model_path, device=device, **kwargs)
        self.model_path = model_path
        self.device = device

    def load(self) -> None:
        """Load calculator from file."""
        from pathlib import Path

        # Validate file exists
        model_file = Path(self.model_path)
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        print(f"Loading model from: {self.model_path}")

        try:
            # Your code to load the model
            # self.calculator = load_my_calculator(self.model_path, device=self.device)
            raise NotImplementedError("Implement model loading from file")

        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}") from e

    def get_name(self) -> str:
        from pathlib import Path
        return f"Custom-{Path(self.model_path).stem}"

    def get_version(self) -> str:
        return str(self.model_path)


# ============================================================================
# How to register your backend
# ============================================================================

"""
To use your custom backend:

1. Save your backend class in: src/gulp_mlips/backends/my_backend.py

2. Add import in src/gulp_mlips/backends/__init__.py:
   ```python
   from gulp_mlips.backends.my_backend import MyCustomBackend

   __all__ = [
       "CalculatorBackend",
       "PETMADBackend",
       "FairChemBackend",
       "MyCustomBackend",  # Add here
   ]
   ```

3. Register in src/gulp_mlips/host.py:
   ```python
   from gulp_mlips.backends.my_backend import MyCustomBackend

   def load_backend(backend_name: str, **config) -> CalculatorBackend:
       backend_map = {
           'petmad': PETMADBackend,
           'fairchem': FairChemBackend,
           'mycustom': MyCustomBackend,  # Add here
       }
       ...
   ```

4. Use it:
   ```bash
   gulp-mlips-host --backend mycustom --device cpu
   ```
"""
