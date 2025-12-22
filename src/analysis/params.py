from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_PARAMS_PATH = Path("params.yaml")


@dataclass(frozen=True)
class LoadedParams:
    raw: dict[str, Any]
    path: Path

    @property
    def benchmarks_selected(self) -> list[str]:
        value = self.raw.get("benchmarks_selected", [])
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise TypeError("params.yaml: benchmarks_selected must be a list[str]")
        return value

    @property
    def gaussino_executable(self) -> str | None:
        value = self.raw.get("gaussino_executable")
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("params.yaml: gaussino_executable must be a string")
        return value

    @property
    def benchmarks(self) -> dict[str, dict[str, Any]]:
        value = self.raw.get("benchmarks", {})
        if not isinstance(value, dict):
            raise TypeError("params.yaml: benchmarks must be a mapping")
        # Shallow validation only; deeper validation happens per stage.
        return value  # type: ignore[return-value]

    def get_benchmark(self, benchmark: str) -> dict[str, Any]:
        try:
            cfg = self.benchmarks[benchmark]
        except KeyError as err:
            raise KeyError(f"params.yaml: benchmark '{benchmark}' not found under benchmarks") from err
        if not isinstance(cfg, dict):
            raise TypeError(f"params.yaml: benchmarks.{benchmark} must be a mapping")
        return cfg


def load_params(path: Path | None = None) -> LoadedParams:
    path = path or DEFAULT_PARAMS_PATH
    data = yaml.safe_load(path.read_text())
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise TypeError("params.yaml root must be a mapping")
    return LoadedParams(raw=data, path=path)
