from __future__ import annotations

from pathlib import Path

import pytest

from analysis.params import LoadedParams, load_params


def _write_params(tmp_path: Path, text: str, name: str = "params.yaml") -> Path:
    path = tmp_path / name
    path.write_text(text)
    return path


def test_load_params_and_basic_properties(tmp_path: Path) -> None:
    params_path = _write_params(
        tmp_path,
        """
benchmarks_selected:
  - bench1
gaussino_executable: ./bin/gaussino
benchmarks:
  bench1:
    options_files: ["opts.py"]
    simulation_files: ["sim.py"]
""",
    )

    lp = load_params(params_path)

    assert isinstance(lp, LoadedParams)
    assert lp.path == params_path
    assert lp.benchmarks_selected == ["bench1"]
    assert lp.gaussino_executable == "./bin/gaussino"
    assert "bench1" in lp.benchmarks
    assert lp.get_benchmark("bench1")["options_files"] == ["opts.py"]


def test_benchmarks_selected_validation(tmp_path: Path) -> None:
    # Non-list value
    params_path = _write_params(
        tmp_path,
        """
benchmarks_selected: invalid
""",
    )
    lp = load_params(params_path)
    with pytest.raises(TypeError, match="benchmarks_selected must be a list\[str\]"):
        _ = lp.benchmarks_selected

    # List with non-string entries
    params_path2 = _write_params(
        tmp_path,
        """
benchmarks_selected: [1, "ok"]
""",
        name="params2.yaml",
    )
    lp2 = load_params(params_path2)
    with pytest.raises(TypeError, match="benchmarks_selected must be a list\[str\]"):
        _ = lp2.benchmarks_selected


def test_gaussino_executable_validation(tmp_path: Path) -> None:
    params_path = _write_params(
        tmp_path,
        """
benchmarks_selected: []
gaussino_executable: 123
""",
    )
    lp = load_params(params_path)
    with pytest.raises(TypeError, match="gaussino_executable must be a string"):
        _ = lp.gaussino_executable


def test_benchmarks_mapping_and_get_benchmark(tmp_path: Path) -> None:
    params_path = _write_params(
        tmp_path,
        """
benchmarks:
  bench1:
    value: 1
  bench2: 42
""",
    )
    lp = load_params(params_path)

    # Root benchmarks must be a mapping
    assert isinstance(lp.benchmarks, dict)

    # Existing benchmark returns mapping
    b1 = lp.get_benchmark("bench1")
    assert b1["value"] == 1

    # Missing benchmark raises KeyError with a helpful message
    with pytest.raises(KeyError, match="benchmark 'missing' not found"):
        lp.get_benchmark("missing")

    # Non-mapping entry under benchmarks raises TypeError
    with pytest.raises(TypeError, match="benchmarks.bench2 must be a mapping"):
        lp.get_benchmark("bench2")


def test_load_params_root_must_be_mapping(tmp_path: Path) -> None:
    # YAML list at the root should fail
    list_path = _write_params(tmp_path, "- 1\n- 2\n", name="list.yaml")
    with pytest.raises(TypeError, match="root must be a mapping"):
        load_params(list_path)

    # YAML null / empty should be treated as empty mapping
    null_path = _write_params(tmp_path, "null\n", name="null.yaml")
    lp = load_params(null_path)
    assert lp.raw == {}
    assert lp.benchmarks_selected == []
    assert lp.gaussino_executable is None
