"""
Tests for stow utils file
"""

from __future__ import annotations

import os
import pathlib
import stat
from typing import TYPE_CHECKING

import pytest

from dploy import utils
from tests import utils as tests_utils

if TYPE_CHECKING:
    from collections.abc import Callable
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
    # the absolute form is normalized: no '..' segments survive, so the result
    # can be compared against other absolute paths. Normalization is lexical,
    # so it works even though this link's target does not exist.
    assert utils.readlink(dest_path, absolute_target=True) == pathlib.Path(
        os.path.normpath(os.path.join(dest, target))
    )


def test_readlink_with_relative_target(dest: Any, source_a: Any) -> None:
    # pylint: disable=unused-argument
    # disable lint errors for source_a since we don't use the variable but use
    # the fixture
    target = os.path.join("..", "source_a", "aaa")
    dest_path = os.path.join(dest, "bbb")
    os.symlink(target, dest_path)
    assert utils.readlink(dest_path) == pathlib.Path(target)
    assert utils.readlink(dest_path, absolute_target=True) == pathlib.Path(
        os.path.normpath(os.path.join(dest, target))
    )
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


def test_is_same_files_ignores_order(dest: Any) -> None:
    file_a = pathlib.Path(dest) / "aaa"
    file_b = pathlib.Path(dest) / "bbb"
    file_a.touch()
    file_b.touch()
    assert utils.is_same_files([file_a, file_b], [file_b, file_a])
    assert not utils.is_same_files([file_a], [file_a, file_b])


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
    pathlib.Path(locked, "file").touch()
    tests_utils.remove_execute_permission(locked)
    try:
        with pytest.raises(PermissionError):
            utils.exists_or_raise_permission_error(pathlib.Path(locked, "file"))
    finally:
        os.chmod(locked, 0o700)


# The tests below deny access with a real ACL entry, which is the case
# os.access cannot see on Windows (#28). Each one is paired with an assertion
# that the path is accessible before and after, so a helper that always
# answers False cannot pass.


@tests_utils.only_on_windows
@pytest.mark.parametrize(
    ("rights", "helper"),
    [
        ("RD", utils.is_directory_readable),
        ("WD", utils.is_directory_writable),
        ("X", utils.is_directory_executable),
    ],
)
def test_directory_helper_sees_acl_deny(
    tmp_path: pathlib.Path,
    rights: str,
    helper: Callable[[pathlib.Path], bool],
) -> None:
    directory = tmp_path / "directory"
    directory.mkdir()
    assert helper(directory)
    tests_utils.deny_acl(directory, rights)
    try:
        assert not helper(directory)
    finally:
        tests_utils.remove_acl_denies(directory)
    assert helper(directory)


@tests_utils.only_on_windows
@pytest.mark.parametrize(
    ("rights", "helper"),
    [
        ("RD", utils.is_file_readable),
        ("WD", utils.is_file_writable),
    ],
)
def test_file_helper_sees_acl_deny(
    tmp_path: pathlib.Path,
    rights: str,
    helper: Callable[[pathlib.Path], bool],
) -> None:
    a_file = tmp_path / "file"
    a_file.touch()
    assert helper(a_file)
    tests_utils.deny_acl(a_file, rights)
    try:
        assert not helper(a_file)
    finally:
        tests_utils.remove_acl_denies(a_file)
    assert helper(a_file)


@tests_utils.only_on_windows
def test_directory_helper_sees_inherited_acl_deny(tmp_path: pathlib.Path) -> None:
    # Inherited deny entries are what GetEffectiveRightsFromAcl rejects, and
    # inheritance is the default on a directory tree, so this is the common case.
    parent = tmp_path / "parent"
    parent.mkdir()
    tests_utils.deny_acl(parent, "RD", inherit=True)
    try:
        child = parent / "child"
        # the deny blocks listing parent, but creating child only needs write
        child.mkdir()
        assert not utils.is_directory_readable(child)
    finally:
        tests_utils.remove_acl_denies(parent)


@tests_utils.only_on_windows
def test_file_is_not_writable_with_read_only_attribute(
    tmp_path: pathlib.Path,
) -> None:
    # the read-only attribute is not part of the ACL, but os.access honours it
    # for files, so the ACL check must not lose that
    a_file = tmp_path / "file"
    a_file.touch()
    os.chmod(a_file, stat.S_IREAD)
    try:
        assert not utils.is_file_writable(a_file)
    finally:
        os.chmod(a_file, stat.S_IWRITE)
    assert utils.is_file_writable(a_file)


@tests_utils.only_on_windows
def test_missing_path_is_not_accessible(tmp_path: pathlib.Path) -> None:
    # os.access answers False for a path that does not exist, not an error
    assert not utils.is_directory_readable(tmp_path / "missing")
    assert not utils.is_file_writable(tmp_path / "missing")
