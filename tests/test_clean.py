"""
Tests for the clean sub command

NOTE: assertions about a link's removal use os.path.islink() rather than
os.path.exists(). os.path.exists() follows the link and reports False for a
link whose target is missing, which is what a dangling link is by definition.
It is therefore already False before clean runs, and cannot detect a no-op.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

import dploy

if TYPE_CHECKING:
    from typing import Any

SUBCMD = "clean"

# see https://github.com/arecarn/dploy/issues/25
CLEAN_IS_A_NO_OP = pytest.mark.xfail(
    reason="clean removes nothing: package matching uses the basename resolved "
    "against the working directory, and the absolute link target is not "
    "normalized. See issue #25.",
    strict=True,
)


@CLEAN_IS_A_NO_OP
def test_clean_with_simple_senario(source_only_files: Any, dest: Any) -> None:
    broken = os.path.join("..", "source_only_files", "bbb")
    dest_path = os.path.join(dest, "bbb")
    os.symlink(broken, dest_path)
    assert os.readlink(dest_path) == broken
    dploy.clean([source_only_files], dest)
    assert not os.path.islink(dest_path)


@CLEAN_IS_A_NO_OP
def test_clean_after_stow_removing_invalid_link_from_source(
    source_a: Any, dest: Any
) -> None:
    dploy.stow([source_a], dest)
    broken = os.path.join("..", "source_a", "bbb")
    dest_path = os.path.join(dest, "bbb")
    os.symlink(broken, dest_path)
    assert os.readlink(dest_path) == broken
    dploy.clean([source_a], dest)
    assert not os.path.islink(dest_path)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )


def test_clean_after_stow_not_removing_invalid_link_from_other_source(
    source_a: Any, dest: Any
) -> None:
    dploy.stow([source_a], dest)
    broken = os.path.join("..", "source_b", "bbb")
    dest_path = os.path.join(dest, "bbb")
    os.symlink(broken, dest_path)
    assert os.readlink(dest_path) == broken
    dploy.clean([source_a], dest)
    # the link must still be there, and must still point where it did: a
    # preservation test passes trivially if clean is a no-op, so assert on
    # both the link's existence and its target
    assert os.path.islink(dest_path)
    assert os.readlink(dest_path) == broken
