from __future__ import annotations

import json
from pathlib import Path

import pytest

import analysis.simulate as simulate
from analysis.simulate import SimulateConfig


def test_run_simulations_writes_metadata_and_calls_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """run_simulations should invoke the runner for each combination and write metadata JSON.

    We patch the internal runner to avoid actually running subprocesses and to focus on
    observable behavior: number of runs and metadata structure.
    """
    run_dir = tmp_path / "run"

    # Two simulation files, one of them named adept_simulation to exercise with_adept flag.
    sim1 = tmp_path / "sim1.py"
    sim1.write_text("# sim1")
    sim2 = tmp_path / "adept_simulation.py"
    sim2.write_text("# adept sim")

    opts = tmp_path / "opts.py"
    opts.write_text("# options")

    calls: list[dict] = []

    def fake_run_one(*, executable: Path, options_files, simulation_file: Path, run_dir: Path, param_dict):  # type: ignore[explicit-any]
        # Record the high-level behavior we care about (what simulations and params were requested).
        calls.append(
            {
                "executable": executable,
                "options_files": list(options_files),
                "simulation_file": simulation_file,
                "run_dir": run_dir,
                "param_dict": dict(param_dict),
            }
        )
        # Simulate a successful run; details are not important for run_simulations.
        return True, Path("logs/run.log"), [Path("out.root")], 1.0

    monkeypatch.setattr(simulate, "_run_one", fake_run_one)

    cfg = SimulateConfig(
        benchmark="bench",
        executable=Path("/bin/gaussino"),
        options_files=[opts],
        simulation_files=[sim1, sim2],
        run_dir=run_dir,
        parameters={"A": [1, 2], "B": [10]},
    )

    metadata_path = simulate.run_simulations(cfg=cfg)
    assert metadata_path.exists()

    data = json.loads(metadata_path.read_text())

    # 2 parameters (A x B) and 2 simulation files => 4 runs
    assert data["benchmark"] == "bench"
    assert len(data["runs"]) == 4
    assert len(calls) == 4

    # Ensure with_adept is set based on simulation file stem for each entry.
    with_adept_values = {entry["with_adept"] for entry in data["runs"]}
    assert with_adept_values == {True, False}


def test_run_one_writes_log_and_moves_root_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_run_one should write a log, expose execution time, and move new .root files.

    We mock subprocess.run and create a .root file in the working directory to verify
    that it is relocated into the run directory with a derived name.
    """
    workdir = tmp_path / "work"
    workdir.mkdir()
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    monkeypatch.chdir(workdir)

    sim_file = tmp_path / "mysim.py"
    sim_file.write_text("# sim")

    executable = tmp_path / "gaussino"
    executable.write_text("#!/bin/sh\n")

    seen: dict = {}

    def fake_run(cmd, env, stdout, stderr, text):  # type: ignore[explicit-any]
        # Record the command and environment passed to subprocess.run
        seen["cmd"] = list(cmd)
        seen["env"] = dict(env)
        # Produce a new .root file in the current working directory
        root_path = workdir / "result.root"
        root_path.write_text("root-data")

        class Dummy:
            returncode = 0

        return Dummy()

    monkeypatch.setattr(simulate.subprocess, "run", fake_run)

    success, log_rel, root_files, elapsed = simulate._run_one(  # type: ignore[attr-defined]
        executable=executable,
        options_files=[tmp_path / "opts.py"],
        simulation_file=sim_file,
        run_dir=run_dir,
        param_dict={"FOO": "bar"},
    )

    assert success is True
    assert isinstance(log_rel, Path)
    assert log_rel.suffix == ".log"
    assert elapsed >= 0.0

    # Log file is written under run_dir and contains expected headers.
    log_path = run_dir / log_rel
    assert log_path.exists()
    log_text = log_path.read_text()
    assert "# Command:" in log_text
    assert "# Execution time:" in log_text

    # Environment should include parameter values as strings.
    assert seen["env"]["FOO"] == "bar"

    # Root file produced in workdir should be moved into run_dir.
    assert root_files
    moved_rel = root_files[0]
    moved_abs = run_dir / moved_rel
    assert moved_abs.exists()
    # After the move, there should be no .root files left in the working directory.
    assert not list(workdir.glob("*.root"))
