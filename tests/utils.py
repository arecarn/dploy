"""
Contains utilities used during testing
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Any

    from typing_extensions import Self


only_on_windows = pytest.mark.skipif(
    os.name != "nt",
    reason="needs Windows ACLs, which os.chmod cannot set or os.access read",
)


# S-1-1-0 is Everyone. Denying it covers the current user's token without
# needing the account name, which varies between local, domain and CI users.
_EVERYONE = "*S-1-1-0"


def deny_acl(path: str | os.PathLike, rights: str, *, inherit: bool = False) -> None:
    """
    deny Everyone the given icacls rights (e.g. RD, WD, X) on a path

    With inherit, the deny applies only to what is created under a directory,
    not to the directory itself. Removing an inheritable entry makes Windows
    list the directory to update its children, so denying the directory too
    would make remove_acl_denies fail with access denied.
    Undo with remove_acl_denies.
    """
    rights = f"(OI)(CI)(IO){rights}" if inherit else f"({rights})"
    subprocess.run(
        ["icacls", os.fspath(path), "/deny", f"{_EVERYONE}:{rights}"],
        check=True,
        capture_output=True,
    )


# Paths that deny_acl denied through the helpers below. A directory denied read
# cannot be listed, which stops os.walk and shutil.rmtree, so teardown clears
# these first (clear_acl_denies).
_denied_paths: set[str] = set()


def _deny(path: str | os.PathLike, rights: str) -> None:
    deny_acl(path, rights)
    _denied_paths.add(os.path.abspath(path))


def _allow(path: str | os.PathLike) -> None:
    remove_acl_denies(path)
    _denied_paths.discard(os.path.abspath(path))


def clear_acl_denies(top: str | os.PathLike) -> None:
    """
    remove the ACL denies set through this module on a path and everything below
    """
    top = os.path.abspath(top)
    for denied in sorted(_denied_paths):
        if denied == top or denied.startswith(top + os.sep):
            _allow(denied)


def remove_acl_denies(path: str | os.PathLike) -> None:
    """
    remove every deny entry for Everyone that deny_acl put on a path
    """
    subprocess.run(
        ["icacls", os.fspath(path), "/remove:d", _EVERYONE],
        check=True,
        capture_output=True,
    )


skip_on_windows_trailing_dot = pytest.mark.skipif(
    os.name == "nt",
    reason="Windows strips a trailing dot from file names, so 'dot-.' cannot exist",
)


def remove_tree(tree: str | os.PathLike) -> None:
    """
    reset the permission of a file and directory tree and remove it
    """
    clear_acl_denies(tree)
    os.chmod(tree, 0o777)
    shutil.rmtree(tree)


def remove_file(file_name: str | os.PathLike) -> None:
    """
    reset the permission of a file and remove it
    """
    clear_acl_denies(file_name)
    os.chmod(file_name, 0o777)
    os.remove(file_name)


def create_file(file_name: str | os.PathLike) -> None:
    """
    create an file
    """
    with open(file_name, "w", encoding="utf-8"):
        pass


def create_directory(directory_name: str | os.PathLike) -> None:
    """
    create an directory
    """
    os.makedirs(directory_name)


class ChangeDirectory:
    """
    Context manager for changing the current working directory
    """

    def __init__(self, new_path: str | os.PathLike) -> None:
        self.new_path = os.path.expanduser(str(new_path))
        self.saved_path = os.getcwd()

    def __enter__(self) -> Self:
        os.chdir(self.new_path)
        return self

    def __exit__(
        self,
        etype: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        os.chdir(self.saved_path)


def create_tree(tree: Any) -> None:
    """
    create an file and directory tree
    """
    for branch in tree:
        if isinstance(branch, str):
            create_file(branch)

        elif isinstance(branch, dict):
            for directory, file_objs in branch.items():
                create_directory(directory)

                with ChangeDirectory(directory):
                    create_tree(file_objs)


def remove_read_permission(path: str | os.PathLike) -> None:
    """
    change users permissions to a path to write only
    """
    if os.name == "nt":
        _deny(path, "RD")
        return
    mode = os.stat(path)[stat.ST_MODE]
    os.chmod(path, mode & ~stat.S_IRUSR & ~stat.S_IRGRP & ~stat.S_IROTH)


def add_read_permission(path: str | os.PathLike) -> None:
    """
    change users permissions to a path to write only
    """
    if os.name == "nt":
        _allow(path)
        return
    mode = os.stat(path)[stat.ST_MODE]
    os.chmod(path, mode | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def remove_write_permission(path: str | os.PathLike) -> None:
    """
    change users permissions to a path to read only
    """
    if os.name == "nt":
        _deny(path, "WD")
        return
    mode = os.stat(path)[stat.ST_MODE]
    os.chmod(path, mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)


def remove_execute_permission(path: str | os.PathLike) -> None:
    """
    change users permissions to a path to read only
    """
    if os.name == "nt":
        _deny(path, "X")
        return
    mode = os.stat(path)[stat.ST_MODE]
    os.chmod(path, mode & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH)


def restore_tree_permissions(top_directory: os.PathLike | str) -> None:
    """Reset users's permissions on a directory tree."""
    clear_acl_denies(top_directory)
    if not os.path.isdir(top_directory):
        raise NotADirectoryError(f"Invalid directory: {top_directory}")

    add_user_permissions(top_directory)
    for current_dir, dirs, files in os.walk(top_directory):
        for file_name in dirs + files:
            add_user_permissions(os.path.join(current_dir, file_name))


def add_user_permissions(path: os.PathLike | str) -> None:
    """Restore owner's file/dir permissions."""
    if not os.path.exists(path) and not os.path.islink(path):
        raise FileNotFoundError(f"Invalid file or directory: {path}")

    wanted = stat.S_IREAD | stat.S_IWRITE
    if os.path.isdir(path):
        wanted |= stat.S_IEXEC

    mode = stat.S_IMODE(os.lstat(path).st_mode)
    if mode & wanted != wanted and not os.path.islink(path):
        os.chmod(path, mode | wanted)
