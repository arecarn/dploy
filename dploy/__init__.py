"""
dploy script is an attempt at creating a clone of GNU stow that will work on
Windows as well as *nix
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dploy import linkcmd, stowcmd

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


def stow(
    packages: Sequence[str | Path],
    destination: str | Path,
    is_silent: bool = True,
    is_dry_run: bool = False,
    ignore_patterns: list[str] | None = None,
    skip_conflicts: bool = False,
) -> None:
    """
    sub command stow
    """
    stowcmd.Stow(
        packages, destination, is_silent, is_dry_run, ignore_patterns, skip_conflicts
    )


def unstow(
    packages: Sequence[str | Path],
    destination: str | Path,
    is_silent: bool = True,
    is_dry_run: bool = False,
    ignore_patterns: list[str] | None = None,
) -> None:
    """
    sub command unstow
    """
    stowcmd.UnStow(packages, destination, is_silent, is_dry_run, ignore_patterns)


def clean(
    packages: Sequence[str | Path],
    destination: str | Path,
    is_silent: bool = True,
    is_dry_run: bool = False,
    ignore_patterns: list[str] | None = None,
) -> None:
    """
    sub command clean
    """
    stowcmd.Clean(packages, destination, is_silent, is_dry_run, ignore_patterns)


def link(
    source: str | Path,
    destination: str | Path,
    is_silent: bool = True,
    is_dry_run: bool = False,
    ignore_patterns: list[str] | None = None,
) -> None:
    """
    sub command link
    """
    linkcmd.Link(source, destination, is_silent, is_dry_run, ignore_patterns)
