from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from analysis.git_tools import describe_repo, get_diff


@dataclass(frozen=True)
class ManifestOptions:
    repo_root: Path
    stack_root: Path
    output_dir: Path
    write_patches: bool = True


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _stack_repos(stack_root: Path) -> list[Path]:
    if not stack_root.exists():
        return []
    # Shallow scan (one level) keeps this fast and predictable.
    return [p for p in sorted(stack_root.iterdir()) if p.is_dir()]


def write_run_manifest(*, options: ManifestOptions) -> dict[str, Any]:
    repo_status = describe_repo(options.repo_root)

    manifest: dict[str, Any] = {
        "repo": {
            "path": str(options.repo_root),
            "is_git_repo": repo_status.is_git_repo,
            "commit": repo_status.commit,
            "is_dirty": repo_status.is_dirty,
            "status_porcelain": repo_status.status_porcelain,
        },
        "stack": {
            "path": str(options.stack_root),
            "exists": options.stack_root.exists(),
            "repos": [],
        },
    }

    patches_dir = options.output_dir / "patches"

    # Record diffs for the main repo if requested
    if options.write_patches and repo_status.is_git_repo:
        unstaged = get_diff(options.repo_root, staged=False) or ""
        staged = get_diff(options.repo_root, staged=True) or ""
        if unstaged.strip():
            _write_text(patches_dir / "repo" / "unstaged.patch", unstaged)
        if staged.strip():
            _write_text(patches_dir / "repo" / "staged.patch", staged)

    # Record stack repos
    for child in _stack_repos(options.stack_root):
        st = describe_repo(child)
        entry: dict[str, Any] = {
            "name": child.name,
            "path": str(child),
            "is_git_repo": st.is_git_repo,
            "commit": st.commit,
            "is_dirty": st.is_dirty,
            "status_porcelain": st.status_porcelain,
        }

        if options.write_patches and st.is_git_repo:
            unstaged = get_diff(child, staged=False) or ""
            staged = get_diff(child, staged=True) or ""
            if unstaged.strip():
                _write_text(patches_dir / "stack" / child.name / "unstaged.patch", unstaged)
            if staged.strip():
                _write_text(patches_dir / "stack" / child.name / "staged.patch", staged)

        manifest["stack"]["repos"].append(entry)

    options.output_dir.mkdir(parents=True, exist_ok=True)
    (options.output_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest
