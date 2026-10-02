"""
Tests for the ignore feature
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import dploy
from dploy.ignore import Ignore

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

SUBCMD = "stow"


def test_recursive_ignore_keeps_parent_and_nonmatching_files(tmp_path: Path) -> None:
    package = tmp_path / "package"
    config = package / ".config"
    config.mkdir(parents=True)
    (config / "cache.swp").touch()
    (config / "settings.conf").touch()
    ignored = Ignore(["**/*.swp"], package)

    assert not ignored.should_ignore(config)
    assert ignored.should_ignore(config / "cache.swp")
    assert not ignored.should_ignore(config / "settings.conf")


def test_stow_recursive_ignore_links_nonmatching_siblings(tmp_path: Path) -> None:
    package = tmp_path / "package"
    config = package / ".config"
    config.mkdir(parents=True)
    (config / "cache.swp").touch()
    (config / "settings.conf").touch()
    destination = tmp_path / "destination"
    destination.mkdir()

    dploy.stow([str(package)], str(destination), ignore_patterns=["**/*.swp"])

    assert (destination / ".config" / "settings.conf").is_file()
    assert not (destination / ".config" / "cache.swp").exists()


def test_ignore_by_ignoring_everthing(source_a: Any, source_c: Any, dest: Any) -> None:
    dploy.stow([source_a, source_c], dest, ignore_patterns=["*"])
    assert not os.path.exists(os.path.join(dest, "aaa"))


def test_recursive_ignore_shared_nested_destination(tmp_path: Path) -> None:
    packages = [tmp_path / "first", tmp_path / "second"]
    for index, package in enumerate(packages):
        nested = package / ".config" / "editor"
        nested.mkdir(parents=True)
        (nested / "cache.swp").touch()
        (nested / f"settings{index}.conf").touch()
    destination = tmp_path / "destination"
    destination.mkdir()

    dploy.stow(packages, destination, ignore_patterns=["**/*.swp"], is_dry_run=True)
    assert not (destination / ".config").exists()
    dploy.stow(packages, destination, ignore_patterns=["**/*.swp"])
    for index in range(2):
        assert (destination / ".config" / "editor" / f"settings{index}.conf").is_file()
    assert not (destination / ".config" / "editor" / "cache.swp").exists()

    dploy.unstow(packages, destination, ignore_patterns=["**/*.swp"])
    for index in range(2):
        assert not (
            destination / ".config" / "editor" / f"settings{index}.conf"
        ).exists()


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


def test_ignore_file_with_blank_line_does_not_crash(
    source_a: Any, dest: Any, file_dploystowignore: Any
) -> None:
    with open(file_dploystowignore, "w", encoding="utf-8") as file:
        file.write("\n")
    dploy.stow([source_a], dest)
    assert os.path.exists(os.path.join(dest, "aaa"))


def test_ignore_file_with_blank_lines_still_honors_real_patterns(
    source_a: Any, source_c: Any, dest: Any, file_dploystowignore: Any
) -> None:
    with open(file_dploystowignore, "w", encoding="utf-8") as file:
        file.write("\n*/aaa\n\n")
    dploy.stow([source_a, source_c], dest)
    assert not os.path.exists(os.path.join(dest, "aaa"))


def test_ignore_pattern_empty_string_does_not_crash(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest, ignore_patterns=[""])
    assert os.path.exists(os.path.join(dest, "aaa"))


def test_ignore_file_with_blank_line_does_not_crash_unstow(
    source_a: Any, dest: Any, file_dploystowignore: Any
) -> None:
    dploy.stow([source_a], dest)
    with open(file_dploystowignore, "w", encoding="utf-8") as file:
        file.write("\n")
    dploy.unstow([source_a], dest)
    assert not os.path.exists(os.path.join(dest, "aaa"))
