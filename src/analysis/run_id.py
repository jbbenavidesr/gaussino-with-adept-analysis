from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash8(obj: Any) -> str:
    h = hashlib.sha256(_stable_json(obj).encode("utf-8")).hexdigest()
    return h[:8]


def _hash4(obj: Any) -> str:
    h = hashlib.sha256(_stable_json(obj).encode("utf-8")).hexdigest()
    return h[:4]


@dataclass(frozen=True)
class RunIds:
    benchmark: str
    repo_sha8: str
    params_hash8: str
    params_hash4: str

    @property
    def run_id(self) -> str:
        return f"{self.benchmark}-{self.repo_sha8}-{self.params_hash8}"

    def run_slug(self, *, summary: str) -> str:
        # Summary is caller-provided (benchmark-specific), deterministic, and should be filesystem-safe.
        return f"{self.benchmark}-{summary}-{self.params_hash4}"


def compute_run_ids(*, benchmark: str, repo_sha: str, params_for_hash: Any) -> RunIds:
    repo_sha8 = repo_sha[:8]
    params_hash8 = _hash8(params_for_hash)
    params_hash4 = _hash4(params_for_hash)
    return RunIds(
        benchmark=benchmark,
        repo_sha8=repo_sha8,
        params_hash8=params_hash8,
        params_hash4=params_hash4,
    )
