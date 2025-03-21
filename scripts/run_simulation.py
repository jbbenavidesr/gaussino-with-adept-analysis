"""Run a specified Gaussino Simulation and store results"""

import argparse
import subprocess
import time
import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
import logging


@dataclass
class SimulationConfig:
    """Class to store simulation configuration parameters"""

    gaussino_path: Path
    options_file: Path
    config_file: Path
    output_dir: Path
    parameters: dict[str, list[str]]
    num_runs: int


class SimulationRunner:
    """Class to handle simulation execution and result storage"""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.setup_logging()
        self.setup_directories()

    def setup_logging(self):
        """Configure logging for the simulation runs"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(self.config.output_dir / "simulation.log"),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        """Create necessary directories for storing results"""
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        (self.config.output_dir / "logs").mkdir(exist_ok=True)
        (self.config.output_dir / "errors").mkdir(exist_ok=True)
        (self.config.output_dir / "metadata").mkdir(exist_ok=True)

    def collect_metadata(self) -> dict:
        """Collect metadata about the system and libraries"""
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "libraries": self._get_library_versions(),
            "parameters": self.config.parameters,
            "gaussino_path": str(self.config.gaussino_path),
            "options_file": str(self.config.options_file),
            "config_file": str(self.config.config_file),
        }
        return metadata

    def _get_library_versions(self) -> dict[str, str]:
        """Get versions of relevant libraries"""
        # Add commands to get versions of your specific libraries
        versions = {}
        try:
            # Example: Get version of a library using git
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.config.gaussino_path,
            )
            versions["gaussino_commit"] = result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Failed to get library version: {e}")
        return versions

    def run_single_simulation(self, params: dict[str, str], run_id: int) -> None:
        """Execute a single simulation with given parameters"""
        # Construct the command
        env_params = " ".join([f"{k}={v}" for k, v in params.items()])
        command = f"{self.config.gaussino_path}/run env {env_params} gaudirun.py {self.config.options_file} {self.config.config_file}"

        # Create unique identifier for this run
        param_str = "_".join([f"{k}{v}" for k, v in params.items()])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_identifier = f"run{run_id}_{param_str}_{timestamp}"

        # Prepare log files
        log_file = self.config.output_dir / "logs" / f"{run_identifier}.log"
        error_file = self.config.output_dir / "errors" / f"{run_identifier}.err"

        # Execute simulation and measure time
        start_time = time.time()
        self.logger.info(f"Starting simulation: {run_identifier}")

        try:
            with open(log_file, "w") as log, open(error_file, "w") as err:
                subprocess.run(command, shell=True, stdout=log, stderr=err, check=True)
            execution_time = time.time() - start_time

            # Append execution time to log file
            with open(log_file, "a") as log:
                log.write(f"\nExecution Time: {execution_time:.2f} seconds\n")

            self.logger.info(
                f"Completed simulation: {run_identifier} in {execution_time:.2f} seconds"
            )

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Simulation failed: {run_identifier}\nError: {e}")

    def run_all_simulations(self):
        """Execute all simulations with different parameter combinations"""
        # Store metadata
        metadata = self.collect_metadata()
        metadata_file = self.config.output_dir / "metadata" / "simulation_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Run simulations for each parameter combination
        for run_id in range(self.config.num_runs):
            for param_values in self._generate_parameter_combinations():
                self.run_single_simulation(param_values, run_id)

    def _generate_parameter_combinations(self):
        """Generate all parameter combinations from config"""
        # Implement parameter combination generation logic here
        # This is a simplified version
        for param_name, param_values in self.config.parameters.items():
            for value in param_values:
                yield {param_name: value}


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run simulation with parameters")
    parser.add_argument(
        "--gaussino-path", type=Path, required=True, help="Path to gaussino executable"
    )
    parser.add_argument(
        "--options-file", type=Path, required=True, help="Path to options.py file"
    )
    parser.add_argument(
        "--config-file", type=Path, required=True, help="Path to configuration file"
    )
    parser.add_argument(
        "--output-dir", type=Path, required=True, help="Directory to store results"
    )
    parser.add_argument(
        "--num-runs",
        type=int,
        default=1,
        help="Number of times to repeat each simulation",
    )
    parser.add_argument(
        "--parameters",
        type=json.loads,
        required=True,
        help="JSON string of parameters and their values",
    )
    return parser.parse_args()


def main():
    """Main entry point of the script"""
    args = parse_arguments()

    config = SimulationConfig(
        gaussino_path=args.gaussino_path,
        options_file=args.options_file,
        config_file=args.config_file,
        output_dir=args.output_dir,
        parameters=args.parameters,
        num_runs=args.num_runs,
    )

    runner = SimulationRunner(config)
    runner.run_all_simulations()


if __name__ == "__main__":
    main()
