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
from dploy import error
from tests import utils

if TYPE_CHECKING:
    from typing import Any

SUBCMD = "clean"


def test_clean_with_simple_senario(source_only_files: Any, dest: Any) -> None:
    broken = os.path.join("..", "source_only_files", "bbb")
    dest_path = os.path.join(dest, "bbb")
    os.symlink(broken, dest_path)
    assert os.readlink(dest_path) == broken
    dploy.clean([source_only_files], dest)
    assert not os.path.islink(dest_path)


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


def test_clean_with_a_nested_package(tmpdir: Any) -> None:
    """
    a package that is not a direct child of the working directory is still
    matched: the whole package path is used, not its basename
    """
    packages = tmpdir.mkdir("packages")
    package = packages.mkdir("pkg")
    dest = tmpdir.mkdir("dest")
    broken = os.path.join("..", "packages", "pkg", "bbb")
    dest_path = os.path.join(str(dest), "bbb")
    os.symlink(broken, dest_path)
    dploy.clean([str(package)], str(dest))
    assert not os.path.islink(dest_path)


def test_clean_from_an_unrelated_working_directory(
    tmpdir: Any, monkeypatch: Any
) -> None:
    """
    clean does not depend on where dploy was invoked from
    """
    package = tmpdir.mkdir("source_a")
    dest = tmpdir.mkdir("dest")
    elsewhere = tmpdir.mkdir("elsewhere")
    broken = os.path.join("..", "source_a", "bbb")
    dest_path = os.path.join(str(dest), "bbb")
    os.symlink(broken, dest_path)
    monkeypatch.chdir(str(elsewhere))
    dploy.clean([str(package)], str(dest))
    assert not os.path.islink(dest_path)


def test_clean_is_a_no_op_on_a_dry_run(source_only_files: Any, dest: Any) -> None:
    """
    --dry-run reports what it would remove without removing it
    """
    broken = os.path.join("..", "source_only_files", "bbb")
    dest_path = os.path.join(dest, "bbb")
    os.symlink(broken, dest_path)
    dploy.clean([source_only_files], dest, is_dry_run=True)
    assert os.path.islink(dest_path)


@pytest.mark.skipif(os.name == "nt", reason="os.chmod has limited effect on Windows")
def test_clean_reports_an_unreadable_subdirectory(
    source_only_files: Any, dest: Any
) -> None:
    """
    an unreadable directory in the destination is reported as a dploy error
    rather than raising a bare PermissionError
    """
    broken = os.path.join("..", "source_only_files", "bbb")
    os.symlink(broken, os.path.join(dest, "bbb"))
    unreadable = os.path.join(dest, "unreadable")
    os.mkdir(unreadable)
    utils.remove_read_permission(unreadable)
    try:
        with pytest.raises(error.DployError):
            dploy.clean([source_only_files], dest)
    finally:
        utils.add_read_permission(unreadable)
