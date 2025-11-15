#!/usr/bin/env python3
"""
Unified runner for gulp-mlips examples with robust server startup.

This script:
1. Starts gulp-mlips-host server with exponential backoff health checks
2. Runs GULP with the specified input file
3. Cleans up the server on exit

Usage:
    python run_example.py --backend petmad --input optimize.gin
    python run_example.py --backend fairchem --model uma-s-1p1 --task omat --input optimize.gin
    python run_example.py --backend gulp --keywords "conp gradient gfnff" --input optimize.gin
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests


class ServerManager:
    """Manages gulp-mlips-host server lifecycle with exponential backoff."""

    def __init__(
        self,
        backend: str,
        port: int = 8193,
        device: str = "cpu",
        model: Optional[str] = None,
        task: Optional[str] = None,
        keywords: Optional[str] = None,
        max_wait: int = 120,
    ):
        self.backend = backend
        self.port = port
        self.device = device
        self.model = model
        self.task = task
        self.keywords = keywords
        self.max_wait = max_wait
        self.process: Optional[subprocess.Popen] = None
        self.log_file = Path("host.log")

    def start(self) -> bool:
        """Start the server and wait for it to become healthy."""
        # Build command
        cmd = ["gulp-mlips-host", "--backend", self.backend, "--port", str(self.port)]

        if self.backend == "fairchem":
            if not self.model:
                raise ValueError("Model required for fairchem backend")
            if not self.task:
                raise ValueError("Task required for fairchem backend")
            cmd.extend(
                ["--model", self.model, "--task", self.task, "--device", self.device]
            )
        elif self.backend == "gulp":
            if self.keywords:
                cmd.extend(["--keywords", self.keywords])
        else:
            cmd.extend(["--device", self.device])

        # Start server
        print(f"Starting gulp-mlips-host server...")
        print(f"  Backend: {self.backend}")
        if self.backend == "fairchem":
            print(f"  Model:   {self.model}")
            print(f"  Task:    {self.task}")
        if self.keywords:
            print(f"  Keywords: {self.keywords}")
        print(f"  Device:  {self.device}")
        print(f"  Port:    {self.port}")
        print()

        with open(self.log_file, "w") as log:
            self.process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid if sys.platform != "win32" else None,
            )

        # Wait for health check with exponential backoff
        if not self._wait_for_health():
            return False

        print("Server is ready!")
        print()
        return True

    def _wait_for_health(self) -> bool:
        """Wait for server health endpoint with exponential backoff."""
        url = f"http://127.0.0.1:{self.port}/health"
        elapsed = 0
        attempt = 0
        backoff = 0.5  # Start with 0.5 seconds
        max_backoff = 8  # Cap at 8 seconds

        print(f"Waiting for server at {url}...")

        while elapsed < self.max_wait:
            attempt += 1

            # Check if process died
            if self.process and self.process.poll() is not None:
                print()
                print(
                    f"ERROR: Server process died (exit code: {self.process.returncode})"
                )
                self._show_log_tail()
                return False

            # Try health check
            try:
                response = requests.get(url, timeout=2)
                if response.ok:
                    print(
                        f"Server is healthy! (took {elapsed:.1f}s, {attempt} attempts)"
                    )
                    return True
            except (requests.ConnectionError, requests.Timeout):
                pass

            # Show progress
            if attempt == 1:
                print(f"  Attempt {attempt}: waiting {backoff:.1f}s...")
            elif attempt <= 5:
                print(
                    f"  Attempt {attempt}: waiting {backoff:.1f}s (elapsed: {elapsed:.1f}s)"
                )
            else:
                # After 5 attempts, only show every few attempts to reduce noise
                if attempt % 3 == 0:
                    print(
                        f"  Attempt {attempt}: still waiting (elapsed: {elapsed:.1f}s / {self.max_wait}s)"
                    )

            # Sleep and update elapsed time
            time.sleep(backoff)
            elapsed += backoff

            # Increase backoff exponentially, capped at max_backoff
            backoff = min(backoff * 1.5, max_backoff)

        print()
        print(f"ERROR: Server failed to become healthy after {self.max_wait}s")
        self._show_log_tail()
        return False

    def _show_log_tail(self, lines: int = 20):
        """Show the last N lines of the server log."""
        print(f"Check {self.log_file} for details:", file=sys.stderr)
        if self.log_file.exists():
            with open(self.log_file) as f:
                all_lines = f.readlines()
                tail_lines = all_lines[-lines:]
                for line in tail_lines:
                    print(line, end="", file=sys.stderr)

    def stop(self):
        """Stop the server."""
        if self.process:
            print()
            print("Cleaning up...")
            print(f"Stopping server (PID {self.process.pid})...")

            # Try graceful shutdown first
            if sys.platform != "win32":
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            else:
                self.process.terminate()

            # Wait for process to exit
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't exit
                if sys.platform != "win32":
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    self.process.kill()
                self.process.wait()

            print("Done!")


def run_gulp(input_file: Path, output_file: Path, port: int) -> bool:
    """Run GULP with the specified input file, streaming output in real-time."""
    print("Running GULP optimization...")
    print(f"  Input:  {input_file}")
    print(f"  Output: {output_file}")
    print()
    print("-" * 66)

    # Set environment variables for wrapper script
    env = os.environ.copy()
    env["HOST"] = "127.0.0.1"
    env["PORT"] = str(port)

    # Run GULP with streaming output
    with open(input_file) as stdin, open(output_file, "w") as outfile:
        process = subprocess.Popen(
            ["gulp"],
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            text=True,
            bufsize=1,  # Line buffered
        )

        # Stream output to both stdout and file
        for line in process.stdout:
            print(line, end="")  # Print to console
            outfile.write(line)  # Write to file
            outfile.flush()  # Ensure it's written immediately

        # Wait for process to complete
        returncode = process.wait()

    print("-" * 66)

    if returncode == 0:
        print()
        print("=" * 66)
        print("SUCCESS!")
        print("=" * 66)
        print("GULP optimization completed successfully")
        print()
        return True
    else:
        print()
        print("=" * 66)
        print("GULP FAILED")
        print("=" * 66)
        print(f"Check {output_file} for errors")
        print()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run gulp-mlips example with robust server startup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # PET-MAD backend (fast, for organic molecules)
  %(prog)s --backend petmad --input optimize.gin

  # FairChem backend with UMA model
  %(prog)s --backend fairchem --model uma-s-1p1 --task omat --input optimize.gin

  # GULP backend with GFN-FF
  %(prog)s --backend gulp --keywords "conp gradient gfnff" --input optimize.gin
        """,
    )

    parser.add_argument(
        "--backend", required=True, help="Backend: petmad, fairchem, or gulp"
    )
    parser.add_argument(
        "--input", required=True, type=Path, help="GULP input file (.gin)"
    )
    parser.add_argument(
        "--output", type=Path, help="GULP output file (.gout, default: <input>.gout)"
    )
    parser.add_argument(
        "--port", type=int, default=8193, help="Server port (default: 8193)"
    )
    parser.add_argument(
        "--device", default="cpu", help="Device: cpu or cuda (default: cpu)"
    )
    parser.add_argument("--model", help="Model for fairchem backend (e.g., uma-s-1p1)")
    parser.add_argument("--task", help="Task for fairchem backend (e.g., omat)")
    parser.add_argument(
        "--keywords", help="Keywords for gulp backend (e.g., 'conp gradient gfnff')"
    )
    parser.add_argument(
        "--max-wait",
        type=int,
        default=120,
        help="Max wait time for server startup (default: 120s)",
    )

    args = parser.parse_args()

    # Set default output file
    if not args.output:
        args.output = args.input.with_suffix(".gout")

    # Validate backend-specific args
    if args.backend == "fairchem":
        if not args.model:
            parser.error("--model required for fairchem backend")
        if not args.task:
            parser.error("--task required for fairchem backend")
        # FairChem models may need more time
        if args.max_wait == 120:  # User didn't override
            args.max_wait = 180

    # Check prerequisites
    for cmd in ["gulp", "gulp-mlips-host", "gulp-mlips-client"]:
        if not subprocess.run(["which", cmd], capture_output=True).returncode == 0:
            print(f"ERROR: {cmd} not found in PATH", file=sys.stderr)
            if cmd == "gulp":
                print("Please install GULP or add it to your PATH", file=sys.stderr)
            else:
                print("Please install gulp-mlips: pip install -e .", file=sys.stderr)
            return 1

    # Create server manager
    server = ServerManager(
        backend=args.backend,
        port=args.port,
        device=args.device,
        model=args.model,
        task=args.task,
        keywords=args.keywords,
        max_wait=args.max_wait,
    )

    # Ensure cleanup happens on exit
    import atexit

    atexit.register(server.stop)

    # Also handle Ctrl-C gracefully
    def signal_handler(sig, frame):
        print()
        print("Interrupted by user")
        server.stop()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)

    # Start server
    if not server.start():
        print()
        print("Last 20 lines of server log:")
        server._show_log_tail(20)
        return 1

    # Run GULP
    success = run_gulp(args.input, args.output, args.port)

    # Show output files
    if success:
        print("Output files:")
        for pattern in ["*.gout", "*.xyz", "*.cif", "*.res", "*.drv"]:
            for f in Path.cwd().glob(pattern):
                size = f.stat().st_size
                print(f"  {f.name} ({size:,} bytes)")
        print()
        print("View results:")
        print(f"  Full output: cat {args.output}")
        print(f"  Server log:  cat host.log")
        return 0
    else:
        print()
        print("Last 20 lines of server log:")
        server._show_log_tail(20)
        return 1


if __name__ == "__main__":
    sys.exit(main())
