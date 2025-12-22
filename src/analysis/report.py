from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import matplotlib

# Use non-interactive backend for batch runs.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

logger = logging.getLogger(__name__)


PERF_VARS = ["time_per_event", "execution_time", "throughput", "event_loop_time"]


@dataclass(frozen=True)
class ReportOutputs:
    metrics_path: Path
    plots_dir: Path


def generate_performance_report(*, performance_csv: Path, out_dir: Path) -> ReportOutputs:
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(performance_csv)

    # Compute a simple metrics.json suitable for dvc metrics.
    metrics = {
        "n_rows": int(df.shape[0]),
    }

    if "with_adept" in df.columns and "time_per_event" in df.columns:
        with_df = df[df["with_adept"] == True]  # noqa: E712
        without_df = df[df["with_adept"] == False]  # noqa: E712

        # Rough global summaries (not physics-specific):
        if not with_df.empty:
            metrics["time_per_event_with_adept_mean"] = float(with_df["time_per_event"].mean())
        if not without_df.empty:
            metrics["time_per_event_without_adept_mean"] = float(without_df["time_per_event"].mean())

    # Plots: for each variable, one figure grouped by with_adept.
    for var in PERF_VARS:
        if var not in df.columns:
            continue
        _plot_perf(df=df, var=var, out_path=plots_dir / f"{var}.png")

    metrics_path = out_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True))
    logger.info("Wrote %s", metrics_path)

    return ReportOutputs(metrics_path=metrics_path, plots_dir=plots_dir)


def _plot_perf(*, df: pd.DataFrame, var: str, out_path: Path) -> None:
    x = None
    if "PARTICLES_PER_EVENT" in df.columns:
        x = "PARTICLES_PER_EVENT"

    fig, ax = plt.subplots(figsize=(10, 6))

    if "with_adept" in df.columns:
        for label, sub in [("with_adept", df[df["with_adept"] == True]), ("without_adept", df[df["with_adept"] == False])]:  # noqa: E712
            if sub.empty:
                continue
            if x:
                ax.plot(sub[x], sub[var], marker="o", linestyle="-", label=label)
            else:
                ax.plot(sub[var].values, marker="o", linestyle="-", label=label)
    else:
        if x:
            ax.plot(df[x], df[var], marker="o")
        else:
            ax.plot(df[var].values, marker="o")

    ax.set_title(var)
    ax.set_xlabel(x or "index")
    ax.set_ylabel(var)
    if x == "PARTICLES_PER_EVENT":
        ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True)
    ax.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
