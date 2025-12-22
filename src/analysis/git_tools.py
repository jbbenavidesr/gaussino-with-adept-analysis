from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitStatus:
    commit: str | None
    is_git_repo: bool
    is_dirty: bool | None
    status_porcelain: str | None


def _run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def is_git_repo(path: Path) -> bool:
    p = _run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
    return p.returncode == 0 and p.stdout.strip() == "true"


def get_commit(path: Path) -> str | None:
    p = _run_git(["rev-parse", "HEAD"], cwd=path)
    if p.returncode != 0:
        return None
    return p.stdout.strip()


def get_status_porcelain(path: Path) -> str | None:
    p = _run_git(["status", "--porcelain"], cwd=path)
    if p.returncode != 0:
        return None
    return p.stdout


def get_diff(path: Path, *, staged: bool) -> str | None:
    args = ["diff"]
    if staged:
        args.append("--staged")
    p = _run_git(args, cwd=path)
    if p.returncode != 0:
        return None
    return p.stdout


def describe_repo(path: Path) -> GitStatus:
    if not is_git_repo(path):
        return GitStatus(commit=None, is_git_repo=False, is_dirty=None, status_porcelain=None)

    commit = get_commit(path)
    porcelain = get_status_porcelain(path)
    is_dirty = None if porcelain is None else (porcelain.strip() != "")
    return GitStatus(commit=commit, is_git_repo=True, is_dirty=is_dirty, status_porcelain=porcelain)
