"""File format readers for gulp-mlips.

Supports reading structure files in various formats that Fortran/GULP can easily write.
"""

from typing import Optional, Tuple
import numpy as np
from ase import Atoms
from ase.io import read as ase_read


def read_xyz(filepath: str) -> Atoms:
    """Read XYZ file and return ASE Atoms object.

    Supports both standard XYZ and extended XYZ formats.
    Extended XYZ (used by GULP) includes cell info and PBC in the comment line.

    Standard XYZ format:
        Line 1: Number of atoms
        Line 2: Comment (often contains energy or other info)
        Lines 3+: Element X Y Z (in Angstroms)

    Extended XYZ format:
        Line 1: Number of atoms
        Line 2: Lattice="..." Properties="..." pbc="T T T" ...
        Lines 3+: Element X Y Z (in Angstroms)

    Args:
        filepath: Path to XYZ file

    Returns:
        ASE Atoms object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    try:
        # Try extended XYZ first (GULP uses this format)
        atoms = ase_read(filepath, format='extxyz')
        return atoms
    except Exception:
        # Fall back to standard XYZ
        try:
            atoms = ase_read(filepath, format='xyz')
            return atoms
        except Exception as e:
            raise ValueError(f"Failed to read XYZ file {filepath}: {e}")


def read_structure(filepath: str, format: Optional[str] = None) -> Atoms:
    """Read structure file in various formats.

    Auto-detects format from file extension if not specified.
    Supported formats: xyz, cssr, cif

    Args:
        filepath: Path to structure file
        format: Optional format specifier ('xyz', 'cssr', 'cif')
                If None, infers from file extension

    Returns:
        ASE Atoms object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format is unsupported or file is invalid
    """
    if format is None:
        # Infer format from extension
        ext = filepath.lower().split('.')[-1]
        if ext not in ['xyz', 'cssr', 'cif']:
            raise ValueError(f"Unknown file extension: {ext}. Specify format explicitly.")
        format = ext

    # Map format to ASE format string
    format_map = {
        'xyz': 'extxyz',  # Use extended XYZ for GULP compatibility
        'cssr': 'cssr',
        'cif': 'cif',
    }

    if format not in format_map:
        raise ValueError(f"Unsupported format: {format}")

    ase_format = format_map[format]

    try:
        atoms = ase_read(filepath, format=ase_format)
        return atoms
    except Exception:
        # For XYZ, fallback to standard format if extended fails
        if format == 'xyz':
            try:
                atoms = ase_read(filepath, format='xyz')
                return atoms
            except Exception as e:
                raise ValueError(f"Failed to read {format} file {filepath}: {e}")
        else:
            raise ValueError(f"Failed to read {format} file {filepath}")


def extract_cell_info(atoms: Atoms) -> Tuple[bool, Optional[np.ndarray]]:
    """Extract cell information from Atoms object.

    Args:
        atoms: ASE Atoms object

    Returns:
        Tuple of (is_periodic, cell_matrix)
        - is_periodic: True if any dimension is periodic
        - cell_matrix: 3x3 cell matrix in Angstroms, or None if non-periodic
    """
    pbc = atoms.get_pbc()
    is_periodic = any(pbc)

    if is_periodic:
        cell = atoms.get_cell()
        return True, np.array(cell)
    else:
        return False, None
