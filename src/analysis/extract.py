from __future__ import annotations

import csv
import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from analysis.extractors import get_extractor

logger = logging.getLogger(__name__)


def _load_json(json_path: Path) -> dict[str, Any]:
    return json.loads(json_path.read_text())


def _resolve_log_path(*, run_dir: Path, log_path_value: str) -> Path:
    log_path = Path(log_path_value)
    if log_path.is_absolute():
        return log_path
    return run_dir / log_path


def extract_run(
    *,
    benchmark: str,
    run_dir: Path,
    out_dir: Path,
    extract_type: str,
) -> Path:
    """Extract results for one run directory.

    Contract:
    - Inputs: run_dir contains simulation_metadata.json and referenced log files.
    - Output: out_dir/{extract_type}-results.csv
    """

    simulation_metadata_path = run_dir / "simulation_metadata.json"
    if not simulation_metadata_path.exists():
        raise FileNotFoundError(
            f"Missing simulation metadata: {simulation_metadata_path}"
        )

    simulation_metadata = _load_json(simulation_metadata_path)
    run_entries = simulation_metadata.get("runs", [])
    if not isinstance(run_entries, list):
        raise TypeError("simulation_metadata.json: 'runs' must be a list")

    extractor = get_extractor(benchmark, extract_type)

    extracted_rows: list[dict[str, Any]] = []
    for run_entry in run_entries:
        if not isinstance(run_entry, dict):
            continue

        log_path_value = run_entry.get("output_path")
        if not log_path_value:
            continue

        log_path = _resolve_log_path(run_dir=run_dir, log_path_value=str(log_path_value))
        if not log_path.exists():
            logger.warning("Log file not found: %s", log_path)
            continue

        log_data = log_path.read_text(errors="replace")

        extracted_rows.append(
            {
                "log_file": str(log_path),
                "execution_time": run_entry.get("execution_time"),
                "with_adept": run_entry.get("with_adept"),
                "parameters": run_entry.get("parameters", {}),
                "results": extractor(log_data),
            }
        )

    if not extracted_rows:
        raise ValueError("No results extracted (no logs found or metadata empty).")

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{extract_type}-results.csv"
    _export_to_csv(extracted_rows, csv_path)
    logger.info("Wrote %s", csv_path)
    return csv_path


def _export_to_csv(rows: list[dict[str, Any]], csv_path: Path) -> None:
    # Determine dynamic columns.
    parameter_keys: set[str] = set()
    result_keys: set[str] = set()

    for row in rows:
        parameters = row.get("parameters", {})
        if isinstance(parameters, dict):
            parameter_keys.update(parameters.keys())

        extracted = row.get("results")
        if isinstance(extracted, Mapping):
            result_keys.update(extracted.keys())
        elif isinstance(extracted, Sequence):
            for item in extracted:
                if isinstance(item, Mapping):
                    result_keys.update(item.keys())
        else:
            raise ValueError("Extractor results are not a dict or list[dict].")

    header = (
        ["log_file", "execution_time", "with_adept"]
        + sorted(parameter_keys)
        + sorted(result_keys)
    )

    with csv_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=header)
        writer.writeheader()

        for row in rows:
            base_row: dict[str, Any] = {
                "log_file": row.get("log_file"),
                "execution_time": row.get("execution_time"),
                "with_adept": row.get("with_adept"),
            }

            parameters = row.get("parameters", {})
            if isinstance(parameters, dict):
                base_row.update(parameters)

            extracted = row.get("results")
            if isinstance(extracted, Mapping):
                out_row = dict(base_row)
                out_row.update(extracted)
                writer.writerow(out_row)
            elif isinstance(extracted, Sequence):
                for item in extracted:
                    if not isinstance(item, Mapping):
                        continue
                    out_row = dict(base_row)
                    out_row.update(item)
                    writer.writerow(out_row)
