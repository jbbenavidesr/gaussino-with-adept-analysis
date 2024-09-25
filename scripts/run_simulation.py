"""Run a specified Gaussino Simulation and store results"""
import logging
import subprocess
from argparse import ArgumentParser
from pathlib import Path


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    
    parser = ArgumentParser()

    parser.add_argument("name", type=str)
    args = parser.parse_args()

    simulation_root = Path(__file__).parent / "simulations" # TODO: Remove Hardcoding

    simulation_build = simulation_root / args.name / "build.sh"
    simulation_run = simulation_root / args.name / "run.sh"


    if simulation_run.is_file():
        logger.info(f"Simulation {args.name} found. Running now...")

        subprocess.run(["bash", simulation_run])

    else:
        logger.info(f"Simulation {args.name} not found.")
        logger.info(simulation_run)


if __name__ == "__main__":
    main()
