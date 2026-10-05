"""
Tests for the stow sub command
"""

from __future__ import annotations

import os
import re
import sys
from typing import TYPE_CHECKING

import pytest

import dploy
from dploy import error
from tests import utils

if TYPE_CHECKING:
    from typing import Any

SUBCMD = "unstow"


def test_unstow_with_basic_senario(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest)
    dploy.unstow([source_a], dest)
    assert not os.path.exists(os.path.join(dest, "aaa"))


def test_unstow_dwith_basic_senario_doesnt_delete_dest_directory(
    source_a: Any, dest: Any
) -> None:
    dploy.stow([source_a], dest)
    dploy.unstow([source_a], dest)
    assert os.path.exists(dest)


def test_unstow_with_a_broken_link_dest(source_a: Any, dest: Any) -> None:
    conflicting_link = os.path.join(dest, "aaa")
    source_file = os.path.join(source_a, "aaa")
    os.symlink("non_existant_source", os.path.join(dest, "aaa"))

    message = str(
        error.ConflictsWithExistingLink(
            subcmd=SUBCMD, source=source_file, dest=conflicting_link
        )
    )

    with pytest.raises(error.ConflictsWithExistingLink, match=re.escape(message)):
        dploy.unstow([source_a], dest)


def test_unstow_with_broken_link_in_dest(source_a: Any, dest: Any) -> None:
    os.mkdir(os.path.join(dest, "aaa"))
    dploy.stow([source_a], dest)
    os.symlink(
        os.path.join(source_a, "non_existant_source"),
        os.path.join(dest, "aaa", "non_existant_source"),
    )
    dploy.unstow([source_a], dest)


def test_unstow_with_non_existant_source(dest: Any) -> None:
    source = "source"
    message = str(error.NoSuchDirectory(subcmd=SUBCMD, file=source))
    with pytest.raises(error.NoSuchDirectory, match=re.escape(message)):
        dploy.unstow([source], dest)


def test_unstow_with_duplicate_source(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest)
    message = str(error.DuplicateSource(subcmd=SUBCMD, file=source_a))
    with pytest.raises(error.DuplicateSource, match=re.escape(message)):
        dploy.unstow([source_a, source_a], dest)


def test_unstow_with_non_existant_dest(source_a: Any) -> None:
    dest = "dest"
    message = str(error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=dest))
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=re.escape(message)):
        dploy.unstow([source_a], dest)


def test_unstow_with_file_as_source(file_a: Any, dest: Any) -> None:
    message = str(error.NoSuchDirectory(subcmd=SUBCMD, file=file_a))
    with pytest.raises(error.NoSuchDirectory, match=re.escape(message)):
        dploy.unstow([file_a], dest)


def test_unstow_with_file_as_dest(source_a: Any, file_a: Any) -> None:
    message = str(error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=file_a))
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=re.escape(message)):
        dploy.unstow([source_a], file_a)


def test_unstow_with_file_as_source_and_dest(file_a: Any, file_b: Any) -> None:
    message = str(error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=file_b))
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=re.escape(message)):
        dploy.unstow([file_a], file_b)


@utils.skip_on_windows_permissions
def test_unstow_with_read_only_dest(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest)
    utils.remove_write_permission(dest)
    message = str(error.InsufficientPermissionsToSubcmdTo(subcmd=SUBCMD, file=dest))
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdTo, match=re.escape(message)
    ):
        dploy.unstow([source_a], dest)


@utils.skip_on_windows_permissions
def test_unstow_with_read_only_dest_file(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest)
    utils.remove_write_permission(os.path.join(dest, "aaa"))
    dploy.unstow([source_a], dest)


@utils.skip_on_windows_permissions
def test_unstow_with_write_only_source(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest)
    utils.remove_read_permission(source_a)
    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_a)
    )
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdFrom, match=re.escape(message)
    ):
        dploy.unstow([source_a], dest)

    utils.add_read_permission(source_a)


@utils.skip_on_windows_permissions
def test_unstow_with_dest_with_no_executue_permissions(
    source_a: Any, dest: Any
) -> None:
    dploy.stow([source_a], dest)
    utils.remove_execute_permission(dest)
    message = str(error.InsufficientPermissionsToSubcmdTo(subcmd=SUBCMD, file=dest))
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdTo, match=re.escape(message)
    ):
        dploy.unstow([source_a], dest)


@utils.skip_on_windows_permissions
def test_unstow_with_dest_dir_with_no_executue_permissions(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    dest_dir = os.path.join(dest, "aaa")
    dploy.stow([source_a, source_b], dest)
    utils.remove_execute_permission(os.path.join(dest, "aaa"))
    message = str(error.InsufficientPermissionsToSubcmdTo(subcmd=SUBCMD, file=dest_dir))
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdTo, match=re.escape(message)
    ):
        dploy.unstow([source_a, source_b], dest)


def test_unstow_with_write_only_source_file(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest)
    utils.remove_read_permission(os.path.join(source_a, "aaa", "aaa"))
    dploy.unstow([source_a], dest)


def test_unstow_with_write_only_dest_file(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest)
    utils.remove_read_permission(os.path.join(dest, "aaa"))
    dploy.unstow([source_a], dest)


def test_unstow_with_same_directory_used_as_source_and_dest(source_a: Any) -> None:
    message = str(error.SourceIsSameAsDest(subcmd=SUBCMD, file=source_a))
    with pytest.raises(error.SourceIsSameAsDest, match=re.escape(message)):
        dploy.unstow([source_a], source_a)


def test_unstow_with_same_simple_directory_used_as_source_and_dest(
    source_only_files: Any,
) -> None:
    message = str(error.SourceIsSameAsDest(subcmd=SUBCMD, file=source_only_files))
    with pytest.raises(error.SourceIsSameAsDest, match=re.escape(message)):
        dploy.unstow([source_only_files], source_only_files)


def test_unstow_folding_basic(source_a: Any, source_b: Any, dest: Any) -> None:
    dploy.stow([source_a, source_b], dest)
    dploy.unstow([source_b], dest)
    assert os.path.islink(os.path.join(dest, "aaa"))


def test_unstow_folding_with_multiple_sources(
    source_a: Any, source_b: Any, source_d: Any, dest: Any
) -> None:
    dploy.stow([source_a, source_b, source_d], dest)
    dploy.unstow([source_b, source_d], dest)
    assert os.path.islink(os.path.join(dest, "aaa"))


def test_unstow_folding_with_stray_symlink_in_unfolded_dest_dir(
    source_a: Any, source_b: Any, source_d: Any, dest: Any
) -> None:
    """
    Given a dest directory with stowed packages that share a unfolded directory,
    that also contains a stray link along with the links created by stowing.

    When the stowed packages are unstowed

    Then the folded directory remains with the single stray symlink
    """
    stray_path = os.path.join(dest, "aaa", "ggg")
    dploy.stow([source_a, source_b], dest)
    dploy.link(os.path.join(source_d, "aaa", "ggg"), stray_path)
    dploy.unstow([source_a, source_b], dest)
    assert os.path.islink(stray_path)


def test_unstow_folding_with_multiple_stowed_sources(
    source_a: Any, source_b: Any, source_d: Any, dest: Any
) -> None:
    dploy.stow([source_a, source_b, source_d], dest)
    dploy.unstow([source_b], dest)
    assert not os.path.islink(os.path.join(dest, "aaa"))


def test_unstow_folding_with_multiple_sources_all_unstowed(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    dploy.stow([source_a, source_b], dest, is_silent=False)
    dploy.unstow([source_a, source_b], dest, is_silent=False)
    assert not os.path.exists(os.path.join(dest, "aaa"))


def test_unstow_folding_with_existing_file_in_dest(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    os.mkdir(os.path.join(dest, "aaa"))
    a_file = os.path.join(dest, "aaa", "a_file")
    utils.create_file(a_file)
    dploy.stow([source_a, source_b], dest)
    dploy.unstow([source_a], dest)
    assert os.path.exists(a_file)


@pytest.mark.xfail(
    sys.version_info >= (3, 14),
    reason=(
        "#31: Path.exists() no longer raises PermissionError on 3.14, so the "
        "permission failure is misreported as a conflict"
    ),
    strict=True,
)
@utils.skip_on_windows_permissions
def test_unstow_folding_with_multiple_sources_with_execute_permission_unset(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    dploy.stow([source_a, source_b], dest)
    utils.remove_execute_permission(source_b)
    dest_dir = os.path.join(dest, "aaa", "ddd")
    message = str(error.PermissionDenied(subcmd=SUBCMD, file=dest_dir))
    with pytest.raises(error.PermissionDenied, match=re.escape(message)):
        dploy.unstow([source_a], dest)


def test_unstow_with_dotfiles(
    source_with_dotfiles: Any, dest_with_dotfiles: Any
) -> None:
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)
    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    assert not os.path.exists(os.path.join(dest_with_dotfiles, "aaa"))
    assert not os.path.exists(os.path.join(dest_with_dotfiles, ".bbb"))


def mismatch_warning(path: str) -> str:
    return f"warning: '{path}' looks like it was stowed with --dotfiles"


def unstow_without_dotfiles(source: str, dest: str, capsys: Any) -> str:
    """
    unstow without --dotfiles and return only what that run printed, dropping
    anything printed earlier by a stow in the same test
    """
    capsys.readouterr()
    dploy.unstow([source], dest, is_silent=False)
    return str(capsys.readouterr().out)


def make_dot_directory(source: str, dest: str, child: str) -> tuple[str, str]:
    """
    create 'dot-ccc' in the source holding one file, and an existing '.ccc'
    directory in the dest, so stowing with --dotfiles has to unfold it; returns
    (source directory, dest directory)
    """
    source_dir = os.path.join(source, "dot-ccc")
    utils.create_directory(source_dir)
    utils.create_file(os.path.join(source_dir, child))
    dotfile_dir = os.path.join(dest, ".ccc")
    utils.create_directory(dotfile_dir)
    return source_dir, dotfile_dir


def test_unstow_without_dotfiles_warns_about_dotfile_links(
    source_with_dotfiles: Any, dest_with_dotfiles: Any, capsys: Any
) -> None:
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    out = unstow_without_dotfiles(source_with_dotfiles, dest_with_dotfiles, capsys)

    dotfile_link = os.path.join(dest_with_dotfiles, ".bbb")
    assert os.path.islink(dotfile_link)
    assert mismatch_warning(dotfile_link) in out
    assert not os.path.exists(os.path.join(dest_with_dotfiles, "aaa"))


def test_unstow_without_dotfiles_does_not_warn_without_dotfile_links(
    source_with_dotfiles: Any, dest_with_dotfiles: Any, capsys: Any
) -> None:
    out = unstow_without_dotfiles(source_with_dotfiles, dest_with_dotfiles, capsys)

    assert "warning" not in out


def test_unstow_without_dotfiles_does_not_warn_about_unrelated_links(
    source_with_dotfiles: Any, dest_with_dotfiles: Any, tmp_path: Any, capsys: Any
) -> None:
    os.symlink(str(tmp_path), os.path.join(dest_with_dotfiles, ".bbb"))

    out = unstow_without_dotfiles(source_with_dotfiles, dest_with_dotfiles, capsys)

    assert "warning" not in out


def test_unstow_without_dotfiles_warns_about_unfolded_dotfile_directory(
    source_with_dotfiles: Any, dest_with_dotfiles: Any, capsys: Any
) -> None:
    _, dotfile_dir = make_dot_directory(
        source_with_dotfiles, dest_with_dotfiles, "file"
    )
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    out = unstow_without_dotfiles(source_with_dotfiles, dest_with_dotfiles, capsys)

    assert os.path.islink(os.path.join(dotfile_dir, "file"))
    assert mismatch_warning(dotfile_dir) in out


def test_unstow_without_dotfiles_warns_about_nested_dotfile_link(
    source_with_dotfiles: Any, dest_with_dotfiles: Any, capsys: Any
) -> None:
    _, dotfile_dir = make_dot_directory(
        source_with_dotfiles, dest_with_dotfiles, "dot-nested"
    )
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    out = unstow_without_dotfiles(source_with_dotfiles, dest_with_dotfiles, capsys)

    assert os.path.islink(os.path.join(dotfile_dir, ".nested"))
    assert mismatch_warning(dotfile_dir) in out


def test_unstow_without_dotfiles_does_not_warn_about_unrelated_directory(
    source_with_dotfiles: Any, dest_with_dotfiles: Any, capsys: Any
) -> None:
    _, dotfile_dir = make_dot_directory(
        source_with_dotfiles, dest_with_dotfiles, "file"
    )
    utils.create_file(os.path.join(dotfile_dir, "file"))

    out = unstow_without_dotfiles(source_with_dotfiles, dest_with_dotfiles, capsys)

    assert "warning" not in out


def test_unstow_with_dot_in_exist_fold_with_dotfiles(
    source_with_dotfiles: Any, dest_with_dotfiles: Any
) -> None:
    utils.create_directory(os.path.join(dest_with_dotfiles, "aaa"))

    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)
    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    assert not os.path.islink(os.path.join(dest_with_dotfiles, "aaa"))
    # see https://github.com/arecarn/dploy/issues/15
    # assert len(os.listdir(os.path.join(dest_with_dotfiles, 'aaa'))) == 0
    assert not os.path.exists(os.path.join(dest_with_dotfiles, ".bbb"))


def test_unstow_with_dot_in_exist_fold_exist_other_with_dotfiles(
    source_with_dotfiles: Any, dest_with_dotfiles: Any
) -> None:
    utils.create_directory(os.path.join(dest_with_dotfiles, "aaa"))
    utils.create_file(os.path.join(dest_with_dotfiles, "aaa", ".keep"))
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)
    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    assert os.path.exists(os.path.join(dest_with_dotfiles, "aaa"))
    assert not os.path.islink(os.path.join(dest_with_dotfiles, "aaa"))

    assert len(os.listdir(os.path.join(dest_with_dotfiles, "aaa"))) == 1
    assert os.path.exists(os.path.join(dest_with_dotfiles, "aaa", ".keep"))
    assert not os.path.exists(os.path.join(dest_with_dotfiles, "aaa", ".aaa"))
    assert not os.path.exists(os.path.join(dest_with_dotfiles, "aaa", ".ccc"))


def test_unstow_with_dotfiles_folds_remaining_package(
    source_with_dotfiles: Any, source_b: Any, dest_with_dotfiles: Any
) -> None:
    """
    the remaining links are named .aaa, .ccc and bbb in the destination but
    bbb, dot-aaa and dot-ccc in the package, so they sort differently on each
    side; folding must not depend on that order
    """
    dploy.stow([source_b, source_with_dotfiles], dest_with_dotfiles, dotfiles=True)
    dploy.unstow([source_b], dest_with_dotfiles, dotfiles=True)

    dest_dir = os.path.join(dest_with_dotfiles, "aaa")
    assert os.path.islink(dest_dir)
    assert os.readlink(dest_dir) == os.path.join("..", "source_with_dotfiles", "aaa")


def test_unstow_with_no_folding(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest, is_folding=False)
    dploy.unstow([source_a], dest, is_folding=False)
    assert os.listdir(dest) == []


def test_unstow_with_no_folding_does_not_fold_remaining_links(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    dploy.stow([source_a, source_b], dest)
    dploy.unstow([source_b], dest, is_folding=False)
    dest_dir = os.path.join(dest, "aaa")
    assert os.path.isdir(dest_dir) and not os.path.islink(dest_dir)
    assert sorted(os.listdir(dest_dir)) == ["aaa", "bbb", "ccc"]
