from __future__ import annotations

import pytest

from analysis.run_id import RunIds, compute_run_ids


def test_compute_run_ids_deterministic() -> None:
    params = {"a": 1, "b": [1, 2, 3]}

    ids1 = compute_run_ids(benchmark="bench", repo_sha="1234567890abcdef", params_for_hash=params)
    ids2 = compute_run_ids(benchmark="bench", repo_sha="1234567890abcdef", params_for_hash=params)

    assert ids1 == ids2
    assert isinstance(ids1, RunIds)


def test_compute_run_ids_stable_across_dict_order() -> None:
    params_a = {"x": 1, "y": 2}
    params_b = {"y": 2, "x": 1}  # same logical contents, different insertion order

    ids_a = compute_run_ids(benchmark="bench", repo_sha="abcdef123456", params_for_hash=params_a)
    ids_b = compute_run_ids(benchmark="bench", repo_sha="abcdef123456", params_for_hash=params_b)

    assert ids_a.params_hash8 == ids_b.params_hash8
    assert ids_a.params_hash4 == ids_b.params_hash4


def test_repo_sha_is_truncated_to_8_chars() -> None:
    ids = compute_run_ids(benchmark="bench", repo_sha="1234567890abcdef", params_for_hash={})
    assert ids.repo_sha8 == "12345678"


def test_run_id_and_slug_format() -> None:
    params = {"key": "value"}
    ids = compute_run_ids(benchmark="bmark", repo_sha="deadbeefcafebabe", params_for_hash=params)

    # run_id is benchmark-repo_sha8-params_hash8
    assert ids.run_id.startswith("bmark-")
    assert ids.run_id.split("-")[1] == ids.repo_sha8
    assert ids.run_id.endswith(ids.params_hash8)

    summary = "t4-ppe1000"
    slug = ids.run_slug(summary=summary)

    # run_slug is benchmark-summary-params_hash4
    assert slug == f"bmark-{summary}-{ids.params_hash4}"
