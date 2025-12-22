from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from analysis.extract import extract_run
from analysis.report import generate_performance_report


def test_extract_and_report_smoke(tmp_path: Path) -> None:
    fixture_dir = Path("tests/fixtures/b4_layered_calorimeter/demo_run")
    run_dir = tmp_path / "run"
    shutil.copytree(fixture_dir, run_dir)

    derived_dir = tmp_path / "derived"
    reports_dir = tmp_path / "reports"

    perf_csv = extract_run(
        benchmark="b4_layered_calorimeter",
        run_dir=run_dir,
        out_dir=derived_dir,
        extract_type="performance",
    )

    df = pd.read_csv(perf_csv)
    assert df.shape[0] == 2
    assert "time_per_event" in df.columns

    outputs = generate_performance_report(performance_csv=perf_csv, out_dir=reports_dir)
    assert outputs.metrics_path.exists()
    assert outputs.plots_dir.exists()
    assert (outputs.plots_dir / "time_per_event.png").exists()
