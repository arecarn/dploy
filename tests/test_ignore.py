"""
Tests for the ignore feature
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import dploy

if TYPE_CHECKING:
    from typing import Any

SUBCMD = "stow"


def test_ignore_by_ignoring_everthing(source_a: Any, source_c: Any, dest: Any) -> None:
    dploy.stow([source_a, source_c], dest, ignore_patterns=["*"])
    assert not os.path.exists(os.path.join(dest, "aaa"))


def test_ignore_by_ignoring_only_subdirectory(
    source_a: Any, source_c: Any, dest: Any
) -> None:
    dploy.stow([source_a, source_c], dest, ignore_patterns=["aaa"])
    assert not os.path.exists(os.path.join(dest, "aaa"))


def test_ignore_by_ignoring_everthing_(source_a: Any, source_c: Any, dest: Any) -> None:
    dploy.stow([source_a, source_c], dest, ignore_patterns=["source_*/aaa"])
    assert not os.path.exists(os.path.join(dest, "aaa"))


def test_ignore_by_ignoring_everthing__(
    source_a: Any, source_c: Any, dest: Any
) -> None:
    dploy.stow([source_a, source_c], dest, ignore_patterns=["*/aaa"])
    assert not os.path.exists(os.path.join(dest, "aaa"))


def test_ignore_file_by_ignoring_everthing__(
    source_a: Any, source_c: Any, file_dploystowignore: Any, dest: Any
) -> None:
    ignore_patterns = ["*/aaa"]
    with open(file_dploystowignore, "w", encoding="utf-8") as file:
        file.write("\n".join(ignore_patterns))
    dploy.stow([source_a, source_c], dest)
    assert not os.path.exists(os.path.join(dest, "aaa"))
