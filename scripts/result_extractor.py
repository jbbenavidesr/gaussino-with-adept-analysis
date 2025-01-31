from __future__ import annotations

import re
import csv
from dataclasses import dataclass
from typing import Generic, TypeVar, Iterable, Any
from pathlib import Path
import argparse
import sys


SimulationData = TypeVar("SimulationData")


class BaseSimulationLogParser(Generic[SimulationData]):
    """Base class that has the main logic for specific simulation parsers"""

    EVENT_PATTERN: str
    RESULT_LINE_PATTERN: str
    CSV_HEADERS: list[str]

    def __init__(self, input_file: Path, output_file: Path):
        self.input_file = input_file
        self.output_file = output_file
        self.current_event: str | None = None

    def parse_event_line(self, line: str) -> str | None:
        """Extract event ID from event line if present."""
        event_match = re.search(self.EVENT_PATTERN, line)
        return event_match.group(1) if event_match else None

    def parse_result_line(self, line: str) -> SimulationData | None:
        """Extract necessary data from a line of results"""
        raise NotImplementedError

    def write_result_line(self, line: SimulationData) -> Iterable[Any]:
        """Convert a data line into an iterable that can be turned into a csv"""
        raise NotImplementedError

    def write_to_csv(self, data_list: list[SimulationData]):
        """Write parsed data to CSV file."""
        with open(self.output_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(self.CSV_HEADERS)

            for data_line in data_list:
                writer.writerow(self.write_result_line(data_line))

    def parse(self):
        """Main parsing method to process the log file."""
        data_list = []

        with open(self.input_file, "r") as f:
            for line in f:
                # Check for event line
                event_id = self.parse_event_line(line)
                if event_id:
                    self.current_event = event_id
                    continue

                # Check for result data line
                result_data = self.parse_result_line(line)
                if result_data:
                    data_list.append(result_data)

        self.write_to_csv(data_list)


@dataclass
class ChamberData:
    event_id: str
    chamber_id: str
    hits: int
    energy: float
    particles: int


class GaussinoB2aSimulationLogParser(BaseSimulationLogParser[ChamberData]):
    # Class constants for regex patterns
    EVENT_PATTERN = r"GenRndInit.*Evt\s+(\d+)"
    RESULT_LINE_PATTERN = (
        r"GiGaMT.*SUCCESS.*"
        r"#Hits=\s*(\d+)\s+"
        r"Energy=\s*([0-9.e+-]+)\[GeV\]\s+"
        r"#Particles=\s*(\d+)\s+"
        r"in\s+(ExternalDetectorEmbedder_Chamber_\d+SDet)"
    )

    CSV_HEADERS = ["Event ID", "Chamber ID", "# Hits", "Energy [GeV]", "# Particles"]

    def parse_result_line(self, line: str) -> ChamberData | None:
        """Extract chamber data from chamber line if present."""
        if not self.current_event:
            return None

        chamber_match = re.search(self.RESULT_LINE_PATTERN, line)
        if not chamber_match:
            return None

        return ChamberData(
            event_id=self.current_event,
            chamber_id=chamber_match.group(4),
            hits=chamber_match.group(1),
            energy=chamber_match.group(2),
            particles=chamber_match.group(3),
        )

    def write_result_line(self, line: ChamberData) -> list[Any]:
        return [
            line.event_id,
            line.chamber_id,
            line.hits,
            line.energy,
            line.particles,
        ]


def get_parser(
    simulation_name: str, input_file: Path, output_file: Path
) -> BaseSimulationLogParser:
    parsers = {
        "gaussinoB2a": GaussinoB2aSimulationLogParser,
    }

    try:
        return parsers[simulation_name](input_file, output_file)
    except KeyError as e:
        raise ValueError(
            f"Simulation with name {simulation_name} has no parser defined"
        )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Parse simulation log file and extract chamber data to CSV."
    )
    parser.add_argument(
        "-i", "--input", type=Path, required=True, help="Path to the input log file"
    )
    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="Path for the output CSV file"
    )
    parser.add_argument(
        "-s", "--simulation", type=str, required=True, help="Name of the simulation."
    )
    return parser.parse_args()


def main():
    try:
        args = parse_arguments()
        parser = get_parser(args.simulation, args.input, args.output)
        parser.parse()
        print(f"Successfully parsed {args.input} and saved results to {args.output}")
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
