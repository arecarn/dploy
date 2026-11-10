"""
Tests for the link sub command
"""

from __future__ import annotations

import os
import pathlib
import re
from typing import TYPE_CHECKING

import pytest

import dploy
from dploy import error
from tests import utils

if TYPE_CHECKING:
    from typing import Any

SUBCMD = "link"


def test_link_with_directory_as_source(source_a: Any, dest: Any) -> None:
    dploy.link(source_a, os.path.join(dest, "source_a_link"))
    assert os.path.islink(os.path.join(dest, "source_a_link"))


def test_link_with_file_as_source(file_a: Any, dest: Any) -> None:
    dploy.link(file_a, os.path.join(dest, "file_a"))
    assert os.path.islink(os.path.join(dest, "file_a"))


def test_link_with_non_existant_source(dest: Any) -> None:
    non_existant_source = "source_a"
    message = str(error.NoSuchFileOrDirectory(subcmd=SUBCMD, file=non_existant_source))
    with pytest.raises(error.NoSuchFileOrDirectory, match=re.escape(message)):
        dploy.link(non_existant_source, os.path.join(dest, "source_a_link"))


def test_link_with_non_existant_dest(source_a: Any) -> None:
    non_existant_dest = "dest"
    message = str(error.NoSuchFileOrDirectory(subcmd=SUBCMD, file=non_existant_dest))
    with pytest.raises(error.NoSuchFileOrDirectory, match=re.escape(message)):
        dploy.link(source_a, os.path.join(non_existant_dest, "source_a_link"))


def test_link_with_read_only_dest(file_a: Any, dest: Any) -> None:
    dest_file = os.path.join(dest, "file_a_link")
    utils.remove_write_permission(dest)
    message = str(
        error.InsufficientPermissionsToSubcmdTo(subcmd=SUBCMD, file=dest_file)
    )
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdTo, match=re.escape(message)
    ):
        dploy.link(file_a, dest_file)


def test_link_with_write_only_source(file_a: Any, dest: Any) -> None:
    dest_file = os.path.join(dest, "file_a_link")
    utils.remove_read_permission(file_a)
    message = str(error.InsufficientPermissions(subcmd=SUBCMD, file=file_a))
    with pytest.raises(error.InsufficientPermissions, match=re.escape(message)):
        dploy.link(file_a, dest_file)


def test_link_with_conflicting_broken_link_at_dest(file_a: Any, dest: Any) -> None:
    dest_file = os.path.join(dest, "file_a_link")
    os.symlink("non_existant_source", dest_file)
    message = str(
        error.ConflictsWithExistingLink(subcmd=SUBCMD, source=file_a, dest=dest_file)
    )
    with pytest.raises(error.ConflictsWithExistingLink, match=re.escape(message)):
        dploy.link(file_a, dest_file)


def _record_symlink_to(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, bool]]:
    """
    record the keyword arguments of every Path.symlink_to call

    target_is_directory is ignored on POSIX, so the call itself is the only
    thing a POSIX run can check. On Windows a directory link made without it
    is a broken file symlink.
    """
    calls: list[dict[str, bool]] = []
    real_symlink_to = pathlib.Path.symlink_to

    def recording_symlink_to(self: pathlib.Path, target: Any, **kwargs: bool) -> None:
        calls.append(kwargs)
        real_symlink_to(self, target, **kwargs)

    monkeypatch.setattr(pathlib.Path, "symlink_to", recording_symlink_to)
    return calls


def test_link_creates_directory_symlink_as_directory(
    source_a: Any, dest: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _record_symlink_to(monkeypatch)
    dploy.link(source_a, os.path.join(dest, "source_a_link"))
    assert calls == [{"target_is_directory": True}]


def test_link_creates_file_symlink_as_file(
    file_a: Any, dest: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _record_symlink_to(monkeypatch)
    dploy.link(file_a, os.path.join(dest, "file_a_link"))
    assert calls == [{"target_is_directory": False}]


def test_link_with_file_as_dest_parent(file_a: Any, tmpdir: Any) -> None:
    not_a_dir = tmpdir.join("not_a_dir")
    not_a_dir.write("I am a file, not a directory")
    dest_file = os.path.join(str(not_a_dir), "file_a_link")
    message = str(
        error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=str(not_a_dir))
    )
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=re.escape(message)):
        dploy.link(file_a, dest_file)
