"""
Tests for stow utils file
"""

from __future__ import annotations

import os
import pathlib
from typing import TYPE_CHECKING

import pytest

from dploy import utils
from tests import utils as tests_utils

if TYPE_CHECKING:
    from typing import Any


@pytest.mark.skipif(
    os.name == "nt",
    reason=(
        "#27: a drive-relative target like /source/bbb comes back from "
        "os.readlink with the current drive prepended on Windows"
    ),
)
def test_readlink_with_broken_absolute_target(dest: Any) -> None:
    target = os.path.join("/", "source_only_files", "bbb")
    dest_path = os.path.join(dest, "bbb")
    os.symlink(target, dest_path)
    assert utils.readlink(dest_path) == pathlib.Path(target)
    assert utils.readlink(dest_path, absolute_target=True) == pathlib.Path(target)


def test_readlink_with_broken_relative_target(dest: Any) -> None:
    target = os.path.join("..", "source_only_files", "bbb")
    dest_path = os.path.join(dest, "bbb")
    os.symlink(target, dest_path)
    assert utils.readlink(dest_path) == pathlib.Path(target)
    assert utils.readlink(dest_path, absolute_target=True) == pathlib.Path(
        dest
    ) / pathlib.Path(target)


def test_readlink_with_relative_target(dest: Any, source_a: Any) -> None:
    # pylint: disable=unused-argument
    # disable lint errors for source_a since we don't use the variable but use
    # the fixture
    target = os.path.join("..", "source_a", "aaa")
    dest_path = os.path.join(dest, "bbb")
    os.symlink(target, dest_path)
    assert utils.readlink(dest_path) == pathlib.Path(target)
    assert utils.readlink(dest_path, absolute_target=True) == pathlib.Path(
        dest
    ) / pathlib.Path(target)
    assert utils.readlink(dest_path, absolute_target=True).exists()


@pytest.mark.skipif(
    os.name == "nt",
    reason="#27: os.readlink returns a \\\\?\\ extended-length path on Windows",
)
def test_readlink_with_absolute_target(dest: Any, source_a: Any) -> None:
    target = os.path.join(source_a, "aaa")
    dest_path = os.path.join(dest, "bbb")
    os.symlink(target, dest_path)
    assert utils.readlink(dest_path) == pathlib.Path(target)
    assert utils.readlink(dest_path, absolute_target=True) == pathlib.Path(target)
    assert utils.readlink(dest_path, absolute_target=True).exists()
    assert utils.readlink(dest_path).exists()


def test_exists_or_raise_permission_error_with_existing_path(dest: Any) -> None:
    assert utils.exists_or_raise_permission_error(pathlib.Path(dest))


def test_exists_or_raise_permission_error_with_missing_path(dest: Any) -> None:
    assert not utils.exists_or_raise_permission_error(pathlib.Path(dest, "missing"))


def test_exists_or_raise_permission_error_with_dangling_link(dest: Any) -> None:
    link = os.path.join(dest, "dangling")
    os.symlink("missing", link)
    assert not utils.exists_or_raise_permission_error(pathlib.Path(link))


def test_exists_or_raise_permission_error_with_symlink_loop(dest: Any) -> None:
    link = os.path.join(dest, "loop")
    os.symlink("loop", link)
    assert not utils.exists_or_raise_permission_error(pathlib.Path(link))


@tests_utils.skip_on_windows_permissions
def test_exists_or_raise_permission_error_without_permission(dest: Any) -> None:
    locked = os.path.join(dest, "locked")
    os.mkdir(locked)
    open(os.path.join(locked, "file"), "w").close()
    tests_utils.remove_execute_permission(locked)
    try:
        with pytest.raises(PermissionError):
            utils.exists_or_raise_permission_error(pathlib.Path(locked, "file"))
    finally:
        os.chmod(locked, 0o700)
