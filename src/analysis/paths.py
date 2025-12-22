from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunPaths:
    benchmark: str
    run_id: str
    repo_root: Path

    @property
    def run_dir(self) -> Path:
        return self.repo_root / "runs" / self.benchmark / self.run_id

    @property
    def derived_dir(self) -> Path:
        return self.repo_root / "derived" / self.benchmark / self.run_id

    @property
    def reports_dir(self) -> Path:
        return self.repo_root / "reports" / self.benchmark / self.run_id
