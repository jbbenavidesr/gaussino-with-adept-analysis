"""Run Gaussino simulation benchmarks for systematic performance testing"""

from __future__ import annotations

import os
import subprocess
import itertools
import datetime
import json
import argparse
import logging
import time
import dataclasses
from pathlib import Path


# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    # Parse arguments and load configuration
    args = parse_args()
    config = load_config(args)

    # Print configuration
    logger.info("Starting simulation runs with configuration:")
    logger.info(config)

    # Run all simulations
    run_all_simulations(config)


def parse_args():
    """Parse command-line arguments or use a configuration file."""
    parser = argparse.ArgumentParser(
        description="Run Gaussino simulations with various parameters."
    )
    parser.add_argument(
        "--config", type=Path, help="Path to JSON configuration file", required=True
    )
    parser.add_argument(
        "--executable", type=Path, help="Path to Gaussino executable", required=True
    )

    return parser.parse_args()


def load_config(args):
    """Load configuration from args or config file."""
    config_file = (
        args.config if args.config.is_file() else args.config / "run_config.json"
    )
    with config_file.open("r") as f:
        simulation_config = json.load(f)

    base_path = config_file.parent

    config = RunnerConfig(
        simulation_name=simulation_config["benchmark"],
        executable=args.executable or os.environ.get("GAUSSINO_EXECUTABLE"),
        options_files=[base_path / file for file in simulation_config["options_files"]],
        simulation_files=[
            base_path / file for file in simulation_config["simulation_files"]
        ],
        output_dir=base_path / simulation_config["output_dir"],
        parameters=simulation_config["parameters"],
    )

    return config


@dataclasses.dataclass(frozen=True)
class RunnerConfig:
    """Configurations for running simulations of a specific benchmark"""

    simulation_name: str
    executable: Path
    options_files: list[Path]
    simulation_files: list[Path]
    output_dir: Path
    parameters: dict[str, list]


def run_all_simulations(config: RunnerConfig):
    """
    Run all simulation combinations based on the provided configuration.

    Args:
        config (dict): Configuration dictionary with parameters
    """

    output_dir = config.output_dir
    timestamp = datetime.datetime.now().isoformat()

    simulation_output = create_run_directory(output_dir)

    # Create a metadata file to track all runs
    metadata_file = simulation_output / "simulation_metadata.json"

    metadata = {
        "timestamp": timestamp,
        "runs": [],
    }

    # Generate all parameter combinations
    param_names = config.parameters.keys()
    param_values = config.parameters.values()
    param_combinations = list(itertools.product(*param_values))

    total_simulations = len(param_combinations) * len(config.simulation_files)
    completed_simulations = 0

    logger.info(f"Preparing to run {total_simulations} simulations...")

    # Run each combination
    for param_combo in param_combinations:
        param_dict = dict(zip(param_names, param_combo))

        for sim_file in config.simulation_files:
            completed_simulations += 1
            logger.info(
                f"Running simulation {completed_simulations}/{total_simulations}"
            )
            logger.info(f"Parameters: {param_dict}")
            logger.info(f"Simulation file: {sim_file}")

            success, output_path, execution_time = run_simulation(
                config.executable,
                param_dict,
                config.options_files,
                sim_file,
                simulation_output,
            )

            # Add to metadata
            metadata["runs"].append(
                {
                    "simulation_file": str(sim_file),
                    "parameters": param_dict,
                    "output_path": str(output_path) if output_path else None,
                    "execution_time": execution_time,
                    "success": success,
                    "with_adept": "adept_simulation" == sim_file.stem,
                }
            )

            # Update metadata file after each run
            with metadata_file.open("w") as f:
                json.dump(metadata, f, indent=2)

            if not success:
                logger.warning(f"Simulation failed with parameters: {param_dict}")

    logger.info(f"All simulations completed. Results stored in {output_dir}")
    logger.info(f"Metadata file: {metadata_file}")


def create_run_directory(output_dir: Path) -> Path:
    """Create the directory where to include all result files"""

    timestamp = datetime.date.today()

    try:
        previous_run = max(
            int(dir.name.split("_")[0]) for dir in output_dir.iterdir() if dir.is_dir()
        )
    except ValueError:
        logger.info("First test for this benchmark")
        previous_run = 0

    run_directory = output_dir / f"{(previous_run + 1):03d}_{timestamp}"
    run_directory.mkdir()
    return run_directory


def run_simulation(
    executable, param_dict, options_files, simulation_file, output_dir
) -> tuple[bool, Path, float]:
    """
    Run a single simulation with the specified parameters and measure execution time.

    Args:
        executable (str): Path to the Gaussino executable
        param_dict (dict): Dictionary of environment parameters to set
        options_files (list[str]): Paths to the base options files
        simulation_file (str): Path to the specific simulation configuration
        output_dir (Path): Directory to store the output log

    Returns:
        tuple: (success_bool, output_path, execution_time_seconds)
    """
    # Create environment with parameters
    env = dict(subprocess.os.environ.copy())
    for key, value in param_dict.items():
        env[key] = str(value)

    # Create a descriptive filename based on parameters and simulation type
    param_str = "_".join([f"{k}={v}" for k, v in param_dict.items()])
    output_base = f"{simulation_file.stem}_{param_str}"
    output_filename = f"{output_base}.log"
    output_root_filename = f"{output_base}.root"
    output_path = output_dir / output_filename

    # Build command
    cmd = (
        [str(executable), "env"]
        + [f"{k}={v}" for k, v in param_dict.items()]
        + ["gaudirun.py"]
        + [str(options_file) for options_file in options_files]
        + [str(simulation_file)]
    )

    logger.info(f"Running: {' '.join(cmd)}")
    logger.info(f"Output will be saved to: {output_path}")

    # Execute the command, capture output, and measure time
    start_time = time.time()

    try:
        with open(output_path, "w") as f:
            # Log the command at the top of the file for reference
            f.write(f"# Command: {' '.join(cmd)}\n")
            f.write(f"# Timestamp: {datetime.datetime.now().isoformat()}\n\n")

            # Run the process and capture output
            process = subprocess.run(
                cmd, env=env, stdout=f, stderr=subprocess.STDOUT, text=True
            )

        end_time = time.time()
        execution_time = end_time - start_time

        # Append execution time to the log file
        with open(output_path, "a") as f:
            f.write(f"\n# Execution time: {execution_time:.2f} seconds\n")

    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        logger.error(f"Error running simulation: {e}")
        return False, None, execution_time

    # Move output files to output_dir
    current_dir = Path.cwd()
    root_files = list(current_dir.glob("*.root"))

    if not root_files:
        logger.warn(f"No `.root` file found in {current_dir}")
    elif len(root_files) > 1:
        logger.warn(
            f"Multiple `.root` files found in {current_dir}: {[str(f) for f in root_files]}"
        )
    else:
        original_file = root_files[0]
        destination_file = output_dir / output_root_filename

        original_file.rename(destination_file)

    # Return success status, output path, and execution time
    return process.returncode == 0, output_path, execution_time


if __name__ == "__main__":
    main()
