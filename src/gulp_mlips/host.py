"""Host server for gulp-mlips.

Runs a FastAPI server that:
1. Loads a calculator backend once (keeps it in memory)
2. Accepts calculation requests via HTTP
3. Returns energies and forces

This avoids repeatedly loading the MLIP model for each calculation.
"""

import sys
import argparse
import logging
from typing import List, Optional, Dict, Any
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from gulp_mlips.backends.base import CalculatorBackend
from gulp_mlips.backends.petmad import PETMADBackend
from gulp_mlips.backends.fairchem import FairChemBackend
from gulp_mlips.backends.gfnff import GFNFFBackend
from gulp_mlips.backends.gulp import GULPBackend

logger = logging.getLogger(__name__)


# Global calculator backend
backend: Optional[CalculatorBackend] = None

app = FastAPI(
    title="gulp-mlips Host Server",
    description="Calculator server for GULP with MLIP backends",
    version="0.1.0"
)


# Pydantic models for API
class AtomicStructure(BaseModel):
    """Atomic structure specification."""
    symbols: List[str] = Field(..., description="Chemical symbols (e.g., ['C', 'H', 'H'])")
    positions: List[List[float]] = Field(..., description="Atomic positions in Angstroms (Nx3)")
    cell: Optional[List[List[float]]] = Field(None, description="Cell matrix in Angstroms (3x3)")
    pbc: Optional[List[bool]] = Field(None, description="Periodic boundary conditions [x, y, z]")


class CalculationRequest(BaseModel):
    """Request for energy/force calculation."""
    structure: AtomicStructure
    properties: List[str] = Field(
        default=["energy", "forces"],
        description="Properties to calculate: 'energy', 'forces', 'stress'"
    )


class CalculationResponse(BaseModel):
    """Response with calculated properties."""
    energy: float = Field(..., description="Total energy in eV")
    forces: Optional[List[List[float]]] = Field(None, description="Forces in eV/Ang (Nx3)")
    stress: Optional[List[float]] = Field(None, description="Stress in eV/Ang^3 (6-component Voigt)")
    backend: str = Field(..., description="Calculator backend name")
    version: str = Field(..., description="Backend version")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    backend_loaded: bool
    backend_name: Optional[str] = None
    backend_version: Optional[str] = None


def load_backend(backend_name: str, **config) -> CalculatorBackend:
    """Load a calculator backend.

    Args:
        backend_name: Name of backend ('petmad', 'fairchem', etc.)
        **config: Backend-specific configuration

    Returns:
        Loaded CalculatorBackend instance

    Raises:
        ValueError: If backend_name is unknown
        RuntimeError: If loading fails
    """
    backend_map = {
        'petmad': PETMADBackend,
        'fairchem': FairChemBackend,
        'gfnff': GFNFFBackend,
        'xtb': GFNFFBackend,  # Alias for gfnff
        'gulp': GULPBackend,
    }

    if backend_name.lower() not in backend_map:
        raise ValueError(
            f"Unknown backend: {backend_name}. "
            f"Available: {', '.join(backend_map.keys())}"
        )

    BackendClass = backend_map[backend_name.lower()]
    backend_instance = BackendClass(**config)
    backend_instance.load()

    return backend_instance


@app.post("/calculate", response_model=CalculationResponse)
async def calculate(request: CalculationRequest):
    """Calculate energy and forces for given structure.

    Args:
        request: Calculation request with structure and properties

    Returns:
        CalculationResponse with results

    Raises:
        HTTPException: If calculation fails
    """
    if backend is None:
        raise HTTPException(status_code=500, detail="Backend not loaded")

    try:
        # Convert to ASE Atoms
        from ase import Atoms

        atoms = Atoms(
            symbols=request.structure.symbols,
            positions=np.array(request.structure.positions),
        )

        # Set cell and PBC if provided
        if request.structure.cell is not None:
            atoms.set_cell(request.structure.cell)

        if request.structure.pbc is not None:
            atoms.set_pbc(request.structure.pbc)
        elif request.structure.cell is not None:
            # If cell is provided but PBC not specified, assume periodic
            atoms.set_pbc(True)

        # Calculate properties
        results = backend.calculate(atoms, properties=request.properties)

        # Format response
        response = CalculationResponse(
            energy=results["energy"],
            forces=results.get("forces").tolist() if "forces" in results else None,
            stress=results.get("stress").tolist() if results.get("stress") is not None else None,
            backend=backend.get_name(),
            version=backend.get_version(),
        )

        # Log calculation
        logger.info(f"Calculated {request.structure.symbols}")
        logger.info(f"  Energy: {results['energy']:.6f} eV")
        if "forces" in results:
            forces_norm = np.linalg.norm(results["forces"], axis=1)
            logger.info(f"  Max force: {forces_norm.max():.6f} eV/Ang")

        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint.

    Returns:
        HealthResponse with server status
    """
    return HealthResponse(
        status="healthy",
        backend_loaded=backend is not None,
        backend_name=backend.get_name() if backend else None,
        backend_version=backend.get_version() if backend else None,
    )


@app.on_event("shutdown")
def shutdown_event():
    """Clean up on server shutdown."""
    if backend is not None:
        backend.cleanup()


def main():
    """Main entry point for host server."""
    parser = argparse.ArgumentParser(
        description="gulp-mlips host server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # PET-MAD backend
  gulp-mlips-host --backend petmad --device cpu

  # FairChem UMA for materials
  gulp-mlips-host --backend fairchem --model uma-s-1p1 --task omat

  # FairChem UMA for molecules
  gulp-mlips-host --backend fairchem --model uma-m-1p1 --task omol --device cuda

  # GFN-FF force field (very fast, good for organic molecules)
  gulp-mlips-host --backend gfnff

  # GFN2-xTB (semi-empirical tight-binding)
  gulp-mlips-host --backend xtb --method GFN2-xTB

  # GULP with its own force fields
  gulp-mlips-host --backend gulp --keywords "gradient" --library lib.lib
        """
    )

    parser.add_argument(
        '--backend',
        default='petmad',
        choices=['petmad', 'fairchem', 'gfnff', 'xtb', 'gulp'],
        help='Calculator backend to use (default: petmad)'
    )
    parser.add_argument(
        '--version',
        default='latest',
        help='Backend model version (for PET-MAD, default: latest)'
    )
    parser.add_argument(
        '--model',
        help='Model name (for FairChem: uma-s-1p1, uma-m-1p1)'
    )
    parser.add_argument(
        '--task',
        help='Task name (for FairChem: omat, omol, oc20, odac, omc)'
    )
    parser.add_argument(
        '--method',
        help='Method (for xTB/GFN-FF: GFN-FF, GFN2-xTB, GFN1-xTB)'
    )
    parser.add_argument(
        '--keywords',
        help='GULP keywords (for GULP backend: e.g., "gradient", "conp gradient")'
    )
    parser.add_argument(
        '--library',
        help='GULP library file (for GULP backend)'
    )
    parser.add_argument(
        '--device',
        default='cpu',
        choices=['cpu', 'cuda'],
        help='Device to use (default: cpu, Note: xTB/GULP always use CPU)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8193,
        help='Port to run server on (default: 8193)'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Prepare backend configuration
    config = {}

    # Add backend-specific arguments
    if args.backend == 'petmad':
        config['device'] = args.device
        config['version'] = args.version
    elif args.backend == 'fairchem':
        config['device'] = args.device
        if args.model:
            config['model'] = args.model
        if args.task:
            config['task'] = args.task
    elif args.backend in ['gfnff', 'xtb']:
        # xTB doesn't use GPU, always CPU
        if args.method:
            config['method'] = args.method
        else:
            config['method'] = 'GFN-FF'  # Default to GFN-FF
    elif args.backend == 'gulp':
        # GULP backend configuration
        if args.keywords:
            config['keywords'] = args.keywords
        if args.library:
            config['library'] = args.library

    # Load backend
    global backend
    logger.info(f"Loading backend: {args.backend}")
    try:
        backend = load_backend(args.backend, **config)
        logger.info(f"Backend loaded: {backend}")
    except Exception as e:
        logger.error(f"Failed to load backend: {e}")
        sys.exit(1)

    # Start server
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"Backend: {backend.get_name()} {backend.get_version()}")
    logger.info(f"Device: {args.device}")
    logger.info("Press Ctrl+C to stop")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
