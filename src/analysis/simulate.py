from __future__ import annotations

import datetime
import itertools
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimulateConfig:
    benchmark: str
    executable: Path
    options_files: list[Path]
    simulation_files: list[Path]
    run_dir: Path
    parameters: dict[str, list[Any]]


def run_simulations(*, cfg: SimulateConfig) -> Path:
    cfg.run_dir.mkdir(parents=True, exist_ok=True)

    metadata_file = cfg.run_dir / "simulation_metadata.json"
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    metadata: dict[str, Any] = {
        "timestamp": timestamp,
        "benchmark": cfg.benchmark,
        "runs": [],
    }

    param_names = list(cfg.parameters.keys())
    param_values = [cfg.parameters[k] for k in param_names]
    param_combinations = list(itertools.product(*param_values))

    total = len(param_combinations) * len(cfg.simulation_files)
    completed = 0
    logger.info("Running %s simulations", total)

    for param_combo in param_combinations:
        param_dict = dict(zip(param_names, param_combo))

        for sim_file in cfg.simulation_files:
            completed += 1
            logger.info("Simulation %s/%s: %s (%s)", completed, total, sim_file.name, param_dict)

            success, log_rel, root_rels, execution_time = _run_one(
                executable=cfg.executable,
                options_files=cfg.options_files,
                simulation_file=sim_file,
                run_dir=cfg.run_dir,
                param_dict=param_dict,
            )

            metadata["runs"].append(
                {
                    "simulation_file": str(sim_file),
                    "parameters": param_dict,
                    "output_path": str(log_rel) if log_rel else None,
                    "root_files": [str(p) for p in root_rels],
                    "execution_time": execution_time,
                    "success": success,
                    "with_adept": sim_file.stem == "adept_simulation",
                }
            )

            metadata_file.write_text(json.dumps(metadata, indent=2))

    logger.info("Wrote %s", metadata_file)
    return metadata_file


def _run_one(
    *,
    executable: Path,
    options_files: list[Path],
    simulation_file: Path,
    run_dir: Path,
    param_dict: dict[str, Any],
) -> tuple[bool, Path | None, list[Path], float]:
    env = dict(os.environ)
    for k, v in param_dict.items():
        env[str(k)] = str(v)

    param_str = "_".join([f"{k}={v}" for k, v in param_dict.items()])
    output_base = f"{simulation_file.stem}_{param_str}" if param_str else simulation_file.stem

    log_name = f"{output_base}.log"
    log_path = run_dir / log_name

    # Snapshot root files before
    cwd = Path.cwd()
    before = {p.resolve() for p in cwd.glob("*.root")}

    cmd = (
        [str(executable), "env"]
        + [f"{k}={v}" for k, v in param_dict.items()]
        + ["gaudirun.py"]
        + [str(p) for p in options_files]
        + [str(simulation_file)]
    )

    start = time.time()
    try:
        with log_path.open("w") as f:
            f.write(f"# Command: {' '.join(cmd)}\n")
            f.write(f"# Timestamp: {datetime.datetime.now(datetime.UTC).isoformat()}\n\n")
            proc = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.STDOUT, text=True)
    except Exception:
        execution_time = time.time() - start
        logger.exception("Error running simulation")
        return False, None, [], execution_time

    execution_time = time.time() - start
    with log_path.open("a") as f:
        f.write(f"\n# Execution time: {execution_time:.2f} seconds\n")

    after = {p.resolve() for p in cwd.glob("*.root")}
    new_roots = sorted(after - before)

    moved: list[Path] = []
    for idx, src in enumerate(new_roots):
        # If multiple roots produced, keep all of them.
        suffix = f"_{idx}" if len(new_roots) > 1 else ""
        dst = run_dir / f"{output_base}{suffix}.root"
        try:
            src.rename(dst)
            moved.append(dst.relative_to(run_dir))
        except Exception:
            logger.exception("Failed moving root file %s -> %s", src, dst)

    if not moved:
        logger.warning("No .root output detected for %s", output_base)

    return proc.returncode == 0, log_path.relative_to(run_dir), moved, execution_time
