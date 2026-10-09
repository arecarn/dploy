"""
A module that contains utility function mainly used for operations in the
missing from the pathlib module.
"""

from __future__ import annotations

import os
import pathlib
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


def get_directory_contents(directory: Path) -> list[Path]:
    """
    return a sorted list of the contents of a directory
    """
    contents: list[Path] = []

    for child in directory.iterdir():
        contents.append(child)

    return sorted(contents)


def exists_or_raise_permission_error(path: Path) -> bool:
    """
    test if a path exists, following symlinks

    Unlike Path.exists(), this raises PermissionError on every Python version.
    Path.exists() stopped doing so in Python 3.14. Any other OSError (such as a
    missing path or a symlink loop) means the path does not exist.
    """
    try:
        path.stat()
    except PermissionError:
        raise
    except OSError:
        return False
    return True


def rmtree(tree: Path) -> None:
    """
    a wrapper around shutil.rmtree to recursively delete a directory specified
    by a pathlib.Path object
    """
    shutil.rmtree(str(tree))


def is_same_file(file1: Path, file2: Path) -> bool:
    """
    test if two pathlib.Path() objects are the same file

    TODO: consider using pathlib.Path.samefile() instead
    NOTE: this can raise exception FileNotFoundError
    """
    return file1.resolve() == file2.resolve()


def is_same_files(files1: Sequence[Path], files2: Sequence[Path]) -> bool:
    """
    test if two collection of files are equivalent, regardless of order
    """
    files1_resolved = sorted(f.resolve() for f in files1)
    files2_resolved = sorted(f.resolve() for f in files2)
    return files1_resolved == files2_resolved


def get_absolute_path(file: str | Path) -> Path:
    """
    get the absolute path of a pathlib.Path() object
    """
    absolute_path = os.path.abspath(os.path.expanduser(str(file)))
    return pathlib.Path(absolute_path)


def get_relative_path(path: Path, start_at: Path) -> Path:
    """
    get the relative path of a pathlib.Path() object

    TODO: consider using Path.relative_to() with walk_up=True (3.12+)
    """
    try:
        relative_path = os.path.relpath(str(path), str(start_at))
    except ValueError:  # when a relative path does not exist
        return get_absolute_path(path)

    return pathlib.Path(relative_path)


def is_file_readable(a_file: Path) -> bool:
    """
    check if a pathlib.Path() file is readable
    """
    return os.access(str(a_file), os.R_OK)


def is_file_writable(a_file: Path) -> bool:
    """
    check if a pathlib.Path() file is writable
    """
    return os.access(str(a_file), os.W_OK)


def is_directory_readable(directory: Path) -> bool:
    """
    check if a pathlib.Path() directory is readable
    """
    return os.access(str(directory), os.R_OK)


def is_directory_writable(directory: Path) -> bool:
    """
    check if a pathlib.Path() directory is writable
    """
    return os.access(str(directory), os.W_OK)


def is_directory_executable(directory: Path) -> bool:
    """
    check if a pathlib.Path() directory is executable
    """
    return os.access(str(directory), os.X_OK)


def readlink(path: Path, absolute_target: bool = False) -> Path:
    """
    get the target of a symbolic link passed as a pathlib.Path object and
    provide the option to return an absolute path even if the link target is
    relative.

    Note: we can't use pathlib.Path.resolve because it doesn't work for broken
    links (it resolves the target, which may not exist)

    """
    link_target = os.readlink(str(path))
    path_dir = os.path.dirname(str(path))
    if absolute_target:
        if not os.path.isabs(link_target):
            link_target = os.path.join(path_dir, link_target)
        return pathlib.Path(link_target)
    return pathlib.Path(link_target)
