from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from analysis import cli


def _common_patches(monkeypatch: pytest.MonkeyPatch, called: dict) -> None:
    def fake_build_context(*, params_path: Path, repo_root: Path) -> SimpleNamespace:
        called["params_path"] = params_path
        called["repo_root"] = repo_root
        return SimpleNamespace(params="P", repo_root=repo_root, commit="deadbeef")

    monkeypatch.setattr(cli, "_build_context", fake_build_context)
    # Avoid changing global logging configuration in tests.
    monkeypatch.setattr(cli, "_setup_logging", lambda verbosity: None)


def test_cli_dispatches_to_run_id(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict = {}
    _common_patches(monkeypatch, called)

    def fake_run_id(args, ctx):  # type: ignore[explicit-any]
        called["func"] = "run-id"
        called["args"] = args
        called["ctx"] = ctx
        return 0

    monkeypatch.setattr(cli, "cmd_run_id", fake_run_id)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "analysis",
            "-vv",
            "run-id",
            "--params",
            "custom.yaml",
            "--repo-root",
            "/tmp/repo",
        ],
    )

    exit_code = cli.main()

    assert exit_code == 0
    assert called["func"] == "run-id"
    assert called["params_path"] == Path("custom.yaml")
    assert called["repo_root"] == Path("/tmp/repo")
    assert called["args"].cmd == "run-id"
    # Verbosity flag should be parsed and attached to args
    assert called["args"].verbose == 2


def test_cli_dispatches_to_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict = {}
    _common_patches(monkeypatch, called)

    def fake_manifest(args, ctx):  # type: ignore[explicit-any]
        called["func"] = "manifest"
        called["args"] = args
        called["ctx"] = ctx
        return 0

    monkeypatch.setattr(cli, "cmd_manifest", fake_manifest)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "analysis",
            "manifest",
            "--params",
            "params.yaml",
            "--repo-root",
            "/repo",
            "--out-root",
            "runs-out",
            "--no-patches",
        ],
    )

    exit_code = cli.main()

    assert exit_code == 0
    assert called["func"] == "manifest"
    assert called["params_path"] == Path("params.yaml")
    assert called["repo_root"] == Path("/repo")
    assert called["args"].cmd == "manifest"
    assert called["args"].out_root == "runs-out"
    assert called["args"].no_patches is True


def test_cli_dispatches_to_extract(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict = {}
    _common_patches(monkeypatch, called)

    def fake_extract(args, ctx):  # type: ignore[explicit-any]
        called["func"] = "extract"
        called["args"] = args
        called["ctx"] = ctx
        return 0

    monkeypatch.setattr(cli, "cmd_extract", fake_extract)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "analysis",
            "extract",
            "--params",
            "params.yaml",
            "--repo-root",
            "/repo",
            "--no-physics",
        ],
    )

    exit_code = cli.main()

    assert exit_code == 0
    assert called["func"] == "extract"
    assert called["params_path"] == Path("params.yaml")
    assert called["repo_root"] == Path("/repo")
    assert called["args"].cmd == "extract"
    assert called["args"].no_physics is True


def test_cli_dispatches_to_simulate(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict = {}
    _common_patches(monkeypatch, called)

    def fake_simulate(args, ctx):  # type: ignore[explicit-any]
        called["func"] = "simulate"
        called["args"] = args
        called["ctx"] = ctx
        return 0

    monkeypatch.setattr(cli, "cmd_simulate", fake_simulate)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "analysis",
            "simulate",
            "--params",
            "params-sim.yaml",
            "--repo-root",
            "/sim-repo",
            "--executable",
            "./gaussino",
        ],
    )

    exit_code = cli.main()

    assert exit_code == 0
    assert called["func"] == "simulate"
    assert called["params_path"] == Path("params-sim.yaml")
    assert called["repo_root"] == Path("/sim-repo")
    assert called["args"].cmd == "simulate"
    assert called["args"].executable == "./gaussino"


def test_cli_dispatches_to_report(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict = {}
    _common_patches(monkeypatch, called)

    def fake_report(args, ctx):  # type: ignore[explicit-any]
        called["func"] = "report"
        called["args"] = args
        called["ctx"] = ctx
        return 0

    monkeypatch.setattr(cli, "cmd_report", fake_report)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "analysis",
            "report",
            "--params",
            "params-report.yaml",
            "--repo-root",
            "/report-repo",
        ],
    )

    exit_code = cli.main()

    assert exit_code == 0
    assert called["func"] == "report"
    assert called["params_path"] == Path("params-report.yaml")
    assert called["repo_root"] == Path("/report-repo")
    assert called["args"].cmd == "report"
