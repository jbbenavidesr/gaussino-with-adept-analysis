"""Result extraction for Gaussino simulation test runs"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
import csv
import logging
from pathlib import Path

from analysis.extractors import get_extractor


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    args = parse_args()

    logger.info(args)

    try:
        extract_results(args.benchmark, args.iteration, args.extract)
    except Exception as e:
        logger.exception(f"There was an error in the extraction: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract results from Gaussino simulation test runs."
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        required=True,
        help="Benchmark name (e.g. B4LayeredCalorimeter)",
    )
    parser.add_argument(
        "--iteration",
        type=str,
        required=True,
        help="ID number of the iteration within a benchmark to be extracted",
    )
    parser.add_argument(
        "--extract",
        type=str,
        required=False,
        choices=["performance", "physics"],
        default="performance",
        help="Type of extraction",
    )

    return parser.parse_args()


def extract_results(
    benchmark_name: str,
    iteration_id: str,
    extract_type: str,
):
    # Step 1: Load run_config.json
    config = load_run_config(benchmark_name)
    output_dir = Path(benchmark_name) / config["output_dir"]

    # Step 2: Find the iteration folder
    iteration_folder = find_iteration_folder(output_dir, iteration_id)

    # Step 3: Load simulation_metadata.json
    metadata = load_simulation_metadata(iteration_folder)

    # Step 4: Get extractor
    extractor = get_extractor(benchmark_name, extract_type)

    # Step 5: Process logs
    results = process_logs(iteration_folder, metadata, extractor)

    # Step 6: Export results to CSV
    export_to_csv(results, iteration_folder, extract_type)


def load_run_config(benchmark_name: str) -> dict:
    """
    Load the run_config.json file for the given benchmark.
    """
    config_path = Path(benchmark_name) / "run_config.json"
    if not config_path.exists():
        logger.debug(f"Config searched in path: {config_path}")
        raise FileNotFoundError(
            f"run_config.json not found for benchmark: {benchmark_name}"
        )
    with config_path.open() as f:
        return json.load(f)


def find_iteration_folder(output_dir: Path, iteration_id: str):
    """
    Find the iteration folder matching the given iteration_id in the output directory.
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        raise FileNotFoundError(f"Output directory not found: {output_dir}")

    # Match folders like {id}_{date}
    iteration_folders = list(output_path.glob(f"{iteration_id}_*"))
    if not iteration_folders:
        raise FileNotFoundError(f"No iteration folder found for ID: {iteration_id}")
    if len(iteration_folders) > 1:
        raise ValueError(f"Multiple iteration folders found for ID: {iteration_id}")

    return iteration_folders[0]


def load_simulation_metadata(iteration_folder):
    """
    Load the simulation_metadata.json file from the iteration folder.
    """
    metadata_path = iteration_folder / "simulation_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"simulation_metadata.json not found in: {iteration_folder}"
        )

    with metadata_path.open() as f:
        return json.load(f)


def process_logs(iteration_folder, metadata, extractor):
    """
    Process log files based on the metadata and extract relevant data.
    """
    results = []

    for run in metadata["runs"]:
        log_path = Path(run["output_path"])
        if not log_path.exists():
            logger.warn(f"Warning: Log file not found: {log_path}")
            continue

        with log_path.open() as f:
            log_data = f.read()

        results.append(
            {
                "log_file": run["output_path"],
                "parameters": run["parameters"],
                "execution_time": run["execution_time"],
                "with_adept": run["with_adept"],
                "results": extractor(log_data),
            }
        )

    return results


def export_to_csv(results, output_path, extract_type):
    """
    Export the processed results to a CSV file without using Pandas.
    Dynamically creates columns for parameters, execution time, and extracted fields.
    """
    # Dynamically determine the column names
    if not results:
        raise ValueError("No results to write to CSV.")

    # Extract all parameter keys and result keys dynamically
    parameter_keys = set()
    result_keys = set()
    for result in results:
        parameter_keys.update(result["parameters"].keys())

        if isinstance(result["results"], Mapping):
            result_keys.update(result["results"].keys())
        elif isinstance(result["results"], Sequence):
            for line in result["results"]:
                result_keys.update(line.keys())
        else:
            raise ValueError("Results are not a dict or list of dicts.")

    # Define the CSV header
    header = (
        ["log_file", "execution_time", "with_adept"]
        + list(parameter_keys)
        + list(result_keys)
    )

    # Write the CSV file
    csv_path = output_path / f"{extract_type}-results.csv"
    with csv_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()

        for result in results:
            # Flatten the parameters and results into a single row
            if isinstance(result["results"], Mapping):
                row = {
                    "log_file": result["log_file"],
                    "execution_time": result["execution_time"],
                    "with_adept": result["with_adept"],
                    **result["parameters"],  # Add parameter columns
                    **result["results"],  # Add extracted result columns
                }
                writer.writerow(row)
            elif isinstance(result["results"], Sequence):
                for line in result["results"]:
                    row = {
                        "log_file": result["log_file"],
                        "execution_time": result["execution_time"],
                        "with_adept": result["with_adept"],
                        **result["parameters"],  # Add parameter columns
                        **line,  # Add extracted result columns
                    }
                    writer.writerow(row)

    logger.info(f"Results exported to: {csv_path}")


if __name__ == "__main__":
    main()
