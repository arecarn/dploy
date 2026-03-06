"""
dploy script is an attempt at creating a clone of GNU stow that will work on
Windows as well as *nix
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dploy import linkcmd, stowcmd

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence


def stow(
    sources: Sequence[str | Path],
    dest: str | Path,
    is_silent: bool = True,
    is_dry_run: bool = False,
    ignore_patterns: list[str] | None = None,
) -> None:
    """
    sub command stow
    """
    stowcmd.Stow(sources, dest, is_silent, is_dry_run, ignore_patterns)


def unstow(
    sources: Sequence[str | Path],
    dest: str | Path,
    is_silent: bool = True,
    is_dry_run: bool = False,
    ignore_patterns: list[str] | None = None,
) -> None:
    """
    sub command unstow
    """
    stowcmd.UnStow(sources, dest, is_silent, is_dry_run, ignore_patterns)


def clean(
    sources: Sequence[str | Path],
    dest: str | Path,
    is_silent: bool = True,
    is_dry_run: bool = False,
    ignore_patterns: list[str] | None = None,
) -> None:
    """
    sub command clean
    """
    stowcmd.Clean(sources, dest, is_silent, is_dry_run, ignore_patterns)


def link(
    source: str | Path,
    dest: str | Path,
    is_silent: bool = True,
    is_dry_run: bool = False,
    ignore_patterns: list[str] | None = None,
) -> None:
    """
    sub command link
    """
    linkcmd.Link(source, dest, is_silent, is_dry_run, ignore_patterns)
