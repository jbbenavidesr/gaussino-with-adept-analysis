from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from analysis.git_tools import get_commit
from analysis.manifest import ManifestOptions, write_run_manifest
from analysis.params import LoadedParams, load_params
from analysis.run_id import compute_run_ids
from analysis.paths import RunPaths
from analysis.extract import extract_run
from analysis.report import generate_performance_report
from analysis.simulate import SimulateConfig, run_simulations


def _setup_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


logger = logging.getLogger(__name__)


def _repo_root_default() -> Path:
    # Assumption: invoked from repo root (e.g. via DVC stage command).
    return Path.cwd()


def _stack_root(repo_root: Path) -> Path:
    return repo_root / "stack"


def _first(v):
    if isinstance(v, list) and v:
        return v[0]
    return None


def _default_summary_from_cfg(cfg: dict) -> str:
    p = cfg.get("parameters", {}) if isinstance(cfg.get("parameters", {}), dict) else {}
    threads = _first(p.get("NUMBER_OF_THREADS"))
    ppe = _first(p.get("PARTICLES_PER_EVENT"))
    nev = _first(p.get("NUMBER_OF_EVENTS"))

    summary_parts: list[str] = []
    if threads is not None:
        summary_parts.append(f"t{threads}")
    if ppe is not None:
        summary_parts.append(f"ppe{ppe}")
    if nev is not None:
        summary_parts.append(f"e{nev}")

    return "-".join(summary_parts) if summary_parts else "params"


@dataclass(frozen=True)
class CliContext:
    params: LoadedParams
    repo_root: Path
    commit: str


def _build_context(*, params_path: Path, repo_root: Path) -> CliContext:
    params = load_params(params_path)
    commit = get_commit(repo_root)
    if commit is None:
        raise RuntimeError(f"Not a git repo: {repo_root}")
    return CliContext(params=params, repo_root=repo_root, commit=commit)


def cmd_run_id(args: argparse.Namespace, ctx: CliContext) -> int:
    for bench in ctx.params.benchmarks_selected:
        cfg = ctx.params.get_benchmark(bench)
        ids = compute_run_ids(benchmark=bench, repo_sha=ctx.commit, params_for_hash=cfg)
        summary = _default_summary_from_cfg(cfg)
        logger.info(
            "benchmark=%s run_id=%s run_slug=%s",
            bench,
            ids.run_id,
            ids.run_slug(summary=summary),
        )

    return 0


def cmd_manifest(args: argparse.Namespace, ctx: CliContext) -> int:
    for bench in ctx.params.benchmarks_selected:
        cfg = ctx.params.get_benchmark(bench)
        ids = compute_run_ids(benchmark=bench, repo_sha=ctx.commit, params_for_hash=cfg)
        out_dir = Path(args.out_root) / bench / ids.run_id

        options = ManifestOptions(
            repo_root=ctx.repo_root,
            stack_root=_stack_root(ctx.repo_root),
            output_dir=out_dir,
            write_patches=not args.no_patches,
        )
        write_run_manifest(options=options)
        logger.info("wrote run manifest: %s", out_dir / "run-manifest.json")

    return 0


def cmd_extract(args: argparse.Namespace, ctx: CliContext) -> int:
    for bench in ctx.params.benchmarks_selected:
        cfg = ctx.params.get_benchmark(bench)
        ids = compute_run_ids(benchmark=bench, repo_sha=ctx.commit, params_for_hash=cfg)
        paths = RunPaths(benchmark=bench, run_id=ids.run_id, repo_root=ctx.repo_root)

        # Performance always
        extract_run(
            benchmark=bench,
            run_dir=paths.run_dir,
            out_dir=paths.derived_dir,
            extract_type="performance",
        )

        # Physics if requested
        if not args.no_physics:
            try:
                extract_run(
                    benchmark=bench,
                    run_dir=paths.run_dir,
                    out_dir=paths.derived_dir,
                    extract_type="physics",
                )
            except Exception:
                logger.exception("Physics extraction failed for benchmark=%s", bench)

    return 0


def cmd_simulate(args: argparse.Namespace, ctx: CliContext) -> int:
    executable: Path | None = None

    # 1) Explicit flag wins
    if args.executable:
        candidate_path = Path(args.executable)
        executable = (
            candidate_path
            if candidate_path.is_absolute()
            else (ctx.repo_root / candidate_path)
        )

    # 2) Environment variable
    if executable is None:
        env_value = os.environ.get("GAUSSINO_EXECUTABLE")
        if env_value:
            executable = Path(env_value)

    # 3) Global config
    if executable is None:
        cfg_value = ctx.params.gaussino_executable
        if cfg_value:
            cfg_path = Path(cfg_value)
            executable = cfg_path if cfg_path.is_absolute() else (ctx.repo_root / cfg_path)

    if executable is None:
        raise RuntimeError(
            "Missing Gaussino executable. Provide --executable, set GAUSSINO_EXECUTABLE, "
            "or set gaussino_executable in params.yaml."
        )

    if not executable.exists():
        raise RuntimeError(
            f"Gaussino executable not found at: {executable}. "
            "(check --executable, GAUSSINO_EXECUTABLE, or params.yaml gaussino_executable)"
        )

    for bench in ctx.params.benchmarks_selected:
        cfg = ctx.params.get_benchmark(bench)
        ids = compute_run_ids(benchmark=bench, repo_sha=ctx.commit, params_for_hash=cfg)
        paths = RunPaths(benchmark=bench, run_id=ids.run_id, repo_root=ctx.repo_root)

        options_files = [ctx.repo_root / p for p in cfg.get("options_files", [])]
        simulation_files = [ctx.repo_root / p for p in cfg.get("simulation_files", [])]
        parameters = cfg.get("parameters", {})
        if not isinstance(parameters, dict):
            raise TypeError(f"params.yaml: benchmarks.{bench}.parameters must be a mapping")

        sim_cfg = SimulateConfig(
            benchmark=bench,
            executable=executable,
            options_files=options_files,
            simulation_files=simulation_files,
            run_dir=paths.run_dir,
            parameters=parameters,
        )

        run_simulations(cfg=sim_cfg)

    return 0


def cmd_report(args: argparse.Namespace, ctx: CliContext) -> int:
    for bench in ctx.params.benchmarks_selected:
        cfg = ctx.params.get_benchmark(bench)
        ids = compute_run_ids(benchmark=bench, repo_sha=ctx.commit, params_for_hash=cfg)
        paths = RunPaths(benchmark=bench, run_id=ids.run_id, repo_root=ctx.repo_root)

        perf_csv = paths.derived_dir / "performance-results.csv"
        if not perf_csv.exists():
            raise FileNotFoundError(f"Missing performance-results.csv: {perf_csv}")

        generate_performance_report(performance_csv=perf_csv, out_dir=paths.reports_dir)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="analysis")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_runid = sub.add_parser(
        "run-id", help="Compute deterministic run_id/run_slug for selected benchmarks"
    )
    p_runid.add_argument("--params", default="params.yaml")
    p_runid.add_argument("--repo-root", default=str(_repo_root_default()))
    p_runid.set_defaults(func=cmd_run_id)

    p_manifest = sub.add_parser(
        "manifest", help="Write run-manifest.json for selected benchmarks"
    )
    p_manifest.add_argument("--params", default="params.yaml")
    p_manifest.add_argument("--repo-root", default=str(_repo_root_default()))
    p_manifest.add_argument("--out-root", default="runs")
    p_manifest.add_argument("--no-patches", action="store_true")
    p_manifest.set_defaults(func=cmd_manifest)

    p_extract = sub.add_parser("extract", help="Extract CSVs from a completed run")
    p_extract.add_argument("--params", default="params.yaml")
    p_extract.add_argument("--repo-root", default=str(_repo_root_default()))
    p_extract.add_argument("--no-physics", action="store_true")
    p_extract.set_defaults(func=cmd_extract)

    p_sim = sub.add_parser("simulate", help="Run simulations for selected benchmarks")
    p_sim.add_argument("--params", default="params.yaml")
    p_sim.add_argument("--repo-root", default=str(_repo_root_default()))
    p_sim.add_argument("--executable", default="")
    p_sim.set_defaults(func=cmd_simulate)

    p_report = sub.add_parser("report", help="Generate plots + metrics from extracted CSVs")
    p_report.add_argument("--params", default="params.yaml")
    p_report.add_argument("--repo-root", default=str(_repo_root_default()))
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    _setup_logging(args.verbose)

    ctx = _build_context(params_path=Path(getattr(args, "params", "params.yaml")), repo_root=Path(getattr(args, "repo_root", _repo_root_default())))
    return int(args.func(args, ctx))


if __name__ == "__main__":
    raise SystemExit(main())
