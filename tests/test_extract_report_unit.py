from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd
import pytest

import analysis.extract as extract_mod
from analysis.extract import extract_run
from analysis.report import generate_performance_report


def test_extract_run_writes_csv_with_extractor_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """extract_run should read metadata, apply extractor, and write a CSV.

    We provide a fake extractor that returns a simple mapping so we can easily
    assert on the resulting CSV structure and values.
    """
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    out_dir = tmp_path / "derived"

    # Create two log files referenced from simulation_metadata.json.
    log1 = run_dir / "log1.log"
    log1.write_text("log1 contents")
    log2 = run_dir / "log2.log"
    log2.write_text("log2 contents")

    metadata = {
        "runs": [
            {
                "simulation_file": "sim1.py",
                "parameters": {"A": 1},
                "output_path": str(log1.name),
                "execution_time": 1.0,
                "with_adept": False,
            },
            {
                "simulation_file": "sim2.py",
                "parameters": {"A": 2},
                "output_path": str(log2.name),
                "execution_time": 2.0,
                "with_adept": True,
            },
        ]
    }
    (run_dir / "simulation_metadata.json").write_text(json.dumps(metadata))

    def fake_get_extractor(benchmark: str, extract_type: str):  # type: ignore[explicit-any]
        assert benchmark == "bench"
        assert extract_type == "performance"

        def extractor(log_data: str):  # type: ignore[explicit-any]
            # Encode length of log to make assertions easy.
            return {"metric": float(len(log_data))}

        return extractor

    monkeypatch.setattr(extract_mod, "get_extractor", fake_get_extractor)

    csv_path = extract_run(
        benchmark="bench",
        run_dir=run_dir,
        out_dir=out_dir,
        extract_type="performance",
    )

    assert csv_path.exists()

    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Two runs -> two CSV rows.
    assert len(rows) == 2
    # Base columns plus dynamic parameter and result columns.
    assert "log_file" in reader.fieldnames
    assert "execution_time" in reader.fieldnames
    assert "with_adept" in reader.fieldnames
    assert "A" in reader.fieldnames
    assert "metric" in reader.fieldnames

    # The metric column should reflect log size, demonstrating extractor wiring.
    metrics = {int(row["A"]): float(row["metric"]) for row in rows}
    assert metrics[1] == float(len("log1 contents"))
    assert metrics[2] == float(len("log2 contents"))


def test_extract_run_raises_when_no_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """If no logs can be processed, extract_run should raise a ValueError."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    out_dir = tmp_path / "derived"

    # Metadata references a missing log file.
    metadata = {
        "runs": [
            {
                "simulation_file": "sim1.py",
                "parameters": {},
                "output_path": "missing.log",
                "execution_time": 1.0,
                "with_adept": False,
            }
        ]
    }
    (run_dir / "simulation_metadata.json").write_text(json.dumps(metadata))

    def fake_get_extractor(benchmark: str, extract_type: str):  # type: ignore[explicit-any]
        def extractor(log_data: str):  # type: ignore[explicit-any]
            return {"metric": 1.0}

        return extractor

    monkeypatch.setattr(extract_mod, "get_extractor", fake_get_extractor)

    with pytest.raises(ValueError, match="No results extracted"):
        extract_run(
            benchmark="bench",
            run_dir=run_dir,
            out_dir=out_dir,
            extract_type="performance",
        )


def test_generate_performance_report_writes_metrics_and_plots(tmp_path: Path) -> None:
    """generate_performance_report should write metrics.json and PNG plots.

    We create a tiny performance CSV with with_adept and time_per_event columns
    and assert that aggregate metrics and plots are produced.
    """
    perf_csv = tmp_path / "performance-results.csv"
    df = pd.DataFrame(
        {
            "with_adept": [True, False, True, False],
            "time_per_event": [1.0, 2.0, 3.0, 4.0],
        }
    )
    df.to_csv(perf_csv, index=False)

    out_dir = tmp_path / "reports"
    outputs = generate_performance_report(performance_csv=perf_csv, out_dir=out_dir)

    # Metrics JSON should exist and contain basic metrics.
    assert outputs.metrics_path.exists()
    metrics = json.loads(outputs.metrics_path.read_text())
    assert metrics["n_rows"] == 4
    # Mean over with_adept==True and False, respectively.
    assert metrics["time_per_event_with_adept_mean"] == pytest.approx((1.0 + 3.0) / 2.0)
    assert metrics["time_per_event_without_adept_mean"] == pytest.approx((2.0 + 4.0) / 2.0)

    # A plot for time_per_event should be generated.
    assert outputs.plots_dir.exists()
    assert (outputs.plots_dir / "time_per_event.png").exists()
