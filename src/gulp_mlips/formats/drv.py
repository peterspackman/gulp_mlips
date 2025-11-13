"""GULP .drv file writer.

The .drv format contains:
1. Energy line
2. Cartesian coordinates section
3. Gradients (forces) section
4. Gradients strain section (for periodic systems)
"""

from typing import Optional
import numpy as np
from ase import Atoms


def write_drv(
    filepath: str,
    atoms: Atoms,
    energy: float,
    forces: np.ndarray,
    stress: Optional[np.ndarray] = None,
) -> None:
    """Write GULP .drv (derivative) file.

    Format:
        energy {value} eV
        coordinates cartesian Angstroms {natoms}
        {index} {atomic_number} {x} {y} {z}
        ...
        gradients cartesian eV/Ang {natoms}
        {index} {fx} {fy} {fz}
        ...
        gradients strain eV
        {sxx} {syy} {szz}
        {syz} {sxz} {sxy}

    Note: GULP expects gradients (not forces), which are the negative of forces.
          drv_gradient = -force

    Args:
        filepath: Output .drv file path
        atoms: ASE Atoms object with structure
        energy: Total energy in eV
        forces: Forces on atoms in eV/Ang (Nx3 array)
        stress: Optional stress tensor in eV/Ang^3 (6-component Voigt notation)

    Raises:
        ValueError: If forces shape doesn't match number of atoms
    """
    natoms = len(atoms)
    if forces.shape != (natoms, 3):
        raise ValueError(
            f"Forces shape {forces.shape} doesn't match number of atoms {natoms}"
        )

    # Get atomic positions and atomic numbers
    positions = atoms.get_positions()  # Already in Angstroms
    atomic_numbers = atoms.get_atomic_numbers()

    # Convert forces to gradients (GULP convention)
    # gradients = -forces
    gradients = -forces

    with open(filepath, 'w') as f:
        # Energy line - Fortran format: 'energy ',f30.10,' eV'
        f.write(f"energy {energy:30.10f} eV\n")

        # Coordinates section
        f.write(f"coordinates cartesian Angstroms {natoms:6d}\n")
        for i, (Z, pos) in enumerate(zip(atomic_numbers, positions), start=1):
            f.write(f"{i:6d} {Z:3d} {pos[0]:15.8f} {pos[1]:15.8f} {pos[2]:15.8f}\n")

        # Gradients section
        f.write(f"gradients cartesian eV/Ang {natoms:6d}\n")
        for i, grad in enumerate(gradients, start=1):
            f.write(f"{i:6d} {grad[0]:15.8f} {grad[1]:15.8f} {grad[2]:15.8f}\n")

        # Gradients strain section (for periodic systems)
        if stress is not None:
            f.write("gradients strain eV\n")
            # GULP expects strain gradients (dE/dstrain) in eV
            # ASE provides stress in eV/Ang^3, so we need to multiply by volume
            # strain_gradient = -stress * volume
            # (Note: negative sign because ASE stress convention is opposite to strain derivative)
            volume = atoms.get_volume()

            # GULP expects strain gradients in two lines:
            # Line 1: diagonal components (xx, yy, zz)
            # Line 2: off-diagonal components (yz, xz, xy)
            # Stress should be in Voigt notation: xx, yy, zz, yz, xz, xy

            if len(stress) == 6:
                # Voigt notation: [xx, yy, zz, yz, xz, xy]
                # Convert stress (eV/Ang^3) to strain gradients (eV)
                strain_grad = -stress * volume
                # Fortran format: 3(1x,f15.8) - each value has 1 space + 15.8 field
                f.write(f" {strain_grad[0]:15.8f} {strain_grad[1]:15.8f} {strain_grad[2]:15.8f}\n")
                f.write(f" {strain_grad[3]:15.8f} {strain_grad[4]:15.8f} {strain_grad[5]:15.8f}\n")
            else:
                # Assume 3x3 matrix, convert to Voigt
                strain_grad = -stress * volume
                sxx, syy, szz = strain_grad[0, 0], strain_grad[1, 1], strain_grad[2, 2]
                syz, sxz, sxy = strain_grad[1, 2], strain_grad[0, 2], strain_grad[0, 1]
                # Fortran format: 3(1x,f15.8)
                f.write(f" {sxx:15.8f} {syy:15.8f} {szz:15.8f}\n")
                f.write(f" {syz:15.8f} {sxz:15.8f} {sxy:15.8f}\n")

        # Ensure all data is written to disk before returning
        f.flush()
        import os
        os.fsync(f.fileno())


def format_drv_string(
    atoms: Atoms,
    energy: float,
    forces: np.ndarray,
    stress: Optional[np.ndarray] = None,
) -> str:
    """Format .drv content as string (useful for testing).

    Args:
        atoms: ASE Atoms object
        energy: Total energy in eV
        forces: Forces on atoms in eV/Ang
        stress: Optional stress tensor

    Returns:
        String with .drv file content
    """
    import io
    from pathlib import Path
    import tempfile

    # Use temporary file approach
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.drv') as f:
        temp_path = f.name

    try:
        write_drv(temp_path, atoms, energy, forces, stress)
        with open(temp_path, 'r') as f:
            content = f.read()
        return content
    finally:
        Path(temp_path).unlink(missing_ok=True)
