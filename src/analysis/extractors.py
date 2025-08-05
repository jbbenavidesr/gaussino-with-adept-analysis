"""
Collection of log file extractor functions for different physics benchmarks.
"""

import re
from collections.abc import Callable
from typing import Final


def performance_extractor(log_data: str) -> dict[str, float]:
    """
    Extracts general performance metrics from log data.

    Args:
        log_data: The content of the log file as a string.

    Returns:
        A dictionary containing the extracted performance metrics.
    """
    patterns = {
        "event_loop_time": r"Measured event loop time \[ns\]: ([\d.e+-]+)",
        "time_per_event": r"Time per event \[s\]: ([\d.e+-]+)",
        "throughput": r"Throughput \[1/s\]: ([\d.e+-]+)",
    }
    results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, log_data)
        if match:
            results[key] = float(match.group(1))
    return results


def b4layeredcalorimeter_physics_extractor(log_data: str) -> list[dict]:
    """
    Extracts physics results from B4LayeredCalorimeter log data.
    """
    pattern = re.compile(
        r"Edep:\s*([\d.eE+-]+)\s*([a-zA-Z]+)\s*track length:\s*([\d.eE+-]+)\s*([a-zA-Z]+)\s+"
        r"sensitive detector:\s*(B4Calorimeter_Layer_AbsorberSDet|B4Calorimeter_Layer_GapSDet)\s+"
        r"layer number:\s*(-?\d+)\s*eventID:\s*(\d+)"
    )
    results = []
    for line in log_data.splitlines():
        m = pattern.search(line)
        if m:
            results.append(
                {
                    "edep_value": float(m.group(1)),
                    "edep_unit": m.group(2),
                    "track_length_value": float(m.group(3)),
                    "track_length_unit": m.group(4),
                    "detector": m.group(5),
                    "layer_number": int(m.group(6)),
                    "event_id": int(m.group(7)),
                }
            )
    return results


def b2chambertracker_physics_extractor(log_data: str) -> list[dict]:
    """
    Extracts physics results from B2ChamberTracker log data.
    """
    pattern = re.compile(
        r"SUCCESS\s*\[\s*Worker\s*#(\d+)\s*\]\s*#Hits=\s*(\d+)\s*Energy=\s*([\d.eE+-]+)\[(\w+)\]\s*#Particles=\s*(\d+)\s*in\s*(ExternalDetectorEmbedder_Chamber_\d+SDet)\s*for\s*event\s*with\s*id:\s*(\d+)"
    )
    results = []
    for line in log_data.splitlines():
        m = pattern.search(line)
        if m:
            results.append(
                {
                    "worker_id": int(m.group(1)),
                    "number_of_hits": int(m.group(2)),
                    "energy_value": float(m.group(3)),
                    "energy_unit": m.group(4),
                    "number_of_particles": int(m.group(5)),
                    "detector": m.group(6),
                    "event_id": int(m.group(7)),
                }
            )
    return results


Extractor = Callable[[str], list[dict] | dict]

EXTRACTORS: Final[dict[tuple[str, str], Extractor]] = {
    ("B4LayeredCalorimeter", "performance"): performance_extractor,
    ("B4LayeredCalorimeter", "physics"): b4layeredcalorimeter_physics_extractor,
    ("B2ChamberTracker", "performance"): performance_extractor,
    ("B2ChamberTracker", "physics"): b2chambertracker_physics_extractor,
}


def get_extractor(benchmark: str, extractor_type: str) -> Extractor:
    """
    Retrieves the correct extractor function from the registry.

    Args:
        benchmark: The name of the benchmark (e.g., 'B4LayeredCalorimeter').
        extractor_type: The type of data to extract ('performance' or 'physics').

    Returns:
        The corresponding extractor function.

    Raises:
        ValueError if the corresponding extractor is not found
    """
    try:
        return EXTRACTORS[(benchmark, extractor_type)]
    except KeyError as err:
        raise ValueError(
            f"Extractor of type {extractor_type} for benchmark {benchmark}  was not found"
        ) from err
