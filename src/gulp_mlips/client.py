"""Client script for gulp-mlips.

This script is called by GULP to perform calculations:
1. Read structure file (XYZ, CSSR, CIF)
2. Send to host server via HTTP
3. Receive energy and forces
4. Write .drv output file

Usage:
    gulp-mlips-client input.xyz output.drv [--port 8193]
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
import requests
import numpy as np

from gulp_mlips.formats.readers import read_structure
from gulp_mlips.formats.drv import write_drv

# Set up logger
logger = logging.getLogger(__name__)


def calculate_via_host(
    input_file: str,
    output_file: str,
    port: int = 8193,
    host: str = "127.0.0.1",
    timeout: int = 300,
    format: Optional[str] = None,
) -> bool:
    """Perform calculation via host server.

    Args:
        input_file: Path to input structure file
        output_file: Path to output .drv file
        port: Host server port
        host: Host server address
        timeout: Request timeout in seconds
        format: Input file format (None = auto-detect)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read structure
        logger.info(f"Reading structure from {input_file}")
        atoms = read_structure(input_file, format=format)
        logger.info(f"  {len(atoms)} atoms: {atoms.get_chemical_formula()}")

        # Prepare request
        # For periodic systems, also request stress for strain gradients
        is_periodic = any(atoms.get_pbc())
        properties = ["energy", "forces"]
        if is_periodic:
            properties.append("stress")

        request_data = {
            "structure": {
                "symbols": atoms.get_chemical_symbols(),
                "positions": atoms.get_positions().tolist(),
            },
            "properties": properties,
        }

        # Add cell and PBC if periodic
        if is_periodic:
            request_data["structure"]["cell"] = atoms.get_cell().tolist()
            request_data["structure"]["pbc"] = atoms.get_pbc().tolist()
            logger.info(f"  Periodic: {atoms.get_pbc()}")

        # Send request to host
        server_url = f"http://{host}:{port}"
        logger.info(f"Sending request to {server_url}/calculate")

        try:
            response = requests.post(
                f"{server_url}/calculate",
                json=request_data,
                timeout=timeout,
            )

            if response.status_code != 200:
                error_msg = response.json().get("detail", "Unknown error") if response.headers.get("content-type") == "application/json" else response.text
                logger.error(f"Server returned status {response.status_code}")
                logger.error(f"  {error_msg}")
                return False

            result = response.json()

        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to server at {host}:{port}")
            logger.error(f"  Make sure the host server is running:")
            logger.error(f"    gulp-mlips-host --backend petmad --port {port}")
            return False

        except requests.exceptions.Timeout:
            logger.error(f"Request timed out after {timeout} seconds")
            return False

        # Extract results
        energy = result["energy"]
        forces = np.array(result["forces"])
        stress = np.array(result["stress"]) if result.get("stress") else None

        logger.info(f"Calculation complete:")
        logger.info(f"  Energy: {energy:.6f} eV")
        logger.info(f"  Backend: {result['backend']} {result['version']}")

        # Write .drv file
        logger.info(f"Writing output to {output_file}")
        write_drv(output_file, atoms, energy, forces, stress)
        logger.info("Done!")

        return True

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return False

    except ValueError as e:
        logger.error(f"{e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for client script."""
    parser = argparse.ArgumentParser(
        description="gulp-mlips client - Calculate energy and forces via host server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (auto-detect format from extension)
  gulp-mlips-client input.xyz output.drv

  # Specify port if host is running on non-default port
  gulp-mlips-client input.xyz output.drv --port 8194

  # Specify input format explicitly
  gulp-mlips-client structure.in output.drv --format cssr

  # Use with GULP
  In your GULP input file:
    external petmad gulp-mlips-client
    output drv structure.drv
        """
    )

    parser.add_argument(
        'input',
        help='Input structure file (XYZ, CSSR, CIF)'
    )
    parser.add_argument(
        'output',
        help='Output .drv file'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8193,
        help='Host server port (default: 8193)'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host server address (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Request timeout in seconds (default: 300)'
    )
    parser.add_argument(
        '--format',
        choices=['xyz', 'cssr', 'cif'],
        help='Input file format (default: auto-detect from extension)'
    )
    parser.add_argument(
        '--verbosity', '-v',
        default='WARNING',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging verbosity (default: WARNING)'
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.verbosity),
        format='%(levelname)s: %(message)s'
    )

    # Validate input file exists
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Perform calculation
    success = calculate_via_host(
        input_file=args.input,
        output_file=args.output,
        port=args.port,
        host=args.host,
        timeout=args.timeout,
        format=args.format,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
