"""
Tests for the stow sub command
"""

from __future__ import annotations

import os
import re
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


@utils.skip_on_windows_permissions
def test_unstow_folding_with_multiple_sources_with_execute_permission_unset(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    dploy.stow([source_a, source_b], dest)
    first_package_link = os.path.join(dest, "aaa", "aaa")
    link_target = os.readlink(first_package_link)
    utils.remove_execute_permission(source_b)
    dest_dir = os.path.join(dest, "aaa", "ddd")
    message = str(error.PermissionDenied(subcmd=SUBCMD, file=dest_dir))
    with pytest.raises(error.PermissionDenied, match=re.escape(message)):
        dploy.unstow([source_a], dest)
    assert os.readlink(first_package_link) == link_target


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


@pytest.mark.parametrize("unstow_dotfiles", [True, False])
@pytest.mark.parametrize("stow_dotfiles", [True, False])
def test_unstow_removes_links_whichever_way_they_were_stowed(
    source_with_dotfiles: Any,
    dest_with_dotfiles: Any,
    stow_dotfiles: bool,
    unstow_dotfiles: bool,
) -> None:
    """
    unstow finds links by what they point at, so the flag it is given does not
    have to match the one the stow was given
    """
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=stow_dotfiles)

    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, dotfiles=unstow_dotfiles)

    assert os.listdir(dest_with_dotfiles) == []


@pytest.mark.parametrize("unstow_dotfiles", [True, False])
def test_unstow_removes_links_stowed_with_and_without_dotfiles(
    source_with_dotfiles: Any, dest_with_dotfiles: Any, unstow_dotfiles: bool
) -> None:
    dploy.stow([source_with_dotfiles], dest_with_dotfiles)
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)
    assert os.path.islink(os.path.join(dest_with_dotfiles, "dot-bbb"))
    assert os.path.islink(os.path.join(dest_with_dotfiles, ".bbb"))

    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, dotfiles=unstow_dotfiles)

    assert os.listdir(dest_with_dotfiles) == []


@pytest.mark.parametrize(
    ("child", "linked_name"), [("file", "file"), ("dot-nested", ".nested")]
)
def test_unstow_without_dotfiles_removes_links_in_unfolded_directory(
    source_with_dotfiles: Any, dest_with_dotfiles: Any, child: str, linked_name: str
) -> None:
    _, dotfile_dir = make_dot_directory(source_with_dotfiles, dest_with_dotfiles, child)
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)
    link = os.path.join(dotfile_dir, linked_name)
    assert os.path.islink(link)

    dploy.unstow([source_with_dotfiles], dest_with_dotfiles)

    assert not os.path.lexists(link)


@pytest.mark.parametrize("user_file_exists", [True, False])
def test_unstow_without_dotfiles_only_touches_links_in_unfolded_directory(
    source_with_dotfiles: Any,
    dest_with_dotfiles: Any,
    capsys: Any,
    user_file_exists: bool,
) -> None:
    """
    inside a directory found under the other name, only links into the package
    are acted on: a user file where the package has an entry is not a conflict,
    and a package entry with nothing there is not reported as already unlinked
    """
    source_dir, dotfile_dir = make_dot_directory(
        source_with_dotfiles, dest_with_dotfiles, "file"
    )
    utils.create_file(os.path.join(source_dir, "other"))
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)
    other = os.path.join(dotfile_dir, "other")
    os.unlink(other)
    if user_file_exists:
        utils.create_file(other)
    capsys.readouterr()

    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, is_silent=False)

    assert not os.path.lexists(os.path.join(dotfile_dir, "file"))
    assert os.path.isfile(other) == user_file_exists
    assert "already unlinked" not in capsys.readouterr().out


def test_unstow_with_links_in_directories_under_both_names(
    source_with_dotfiles: Any, dest_with_dotfiles: Any, capsys: Any
) -> None:
    """
    'dot-ccc' and '.ccc' are both real directories, each holding some of the
    package's links. Every link is removed, and an entry linked under one name
    is not also reported as already unlinked under the other
    """
    source_dir, dotfile_dir = make_dot_directory(
        source_with_dotfiles, dest_with_dotfiles, "x"
    )
    utils.create_file(os.path.join(source_dir, "y"))
    literal_dir = os.path.join(dest_with_dotfiles, "dot-ccc")
    utils.create_directory(literal_dir)
    os.symlink(
        os.path.relpath(os.path.join(source_dir, "x"), dotfile_dir),
        os.path.join(dotfile_dir, "x"),
    )
    os.symlink(
        os.path.relpath(os.path.join(source_dir, "y"), literal_dir),
        os.path.join(literal_dir, "y"),
    )
    capsys.readouterr()

    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, is_silent=False)

    out = capsys.readouterr().out
    assert not os.path.lexists(os.path.join(dotfile_dir, "x"))
    assert not os.path.lexists(os.path.join(literal_dir, "y"))
    reported = [line for line in out.splitlines() if "dot-ccc" in line]
    assert reported and not any("already unlinked" in line for line in reported)


def test_unstow_with_dotfiles_removes_literal_links_in_unfolded_directory(
    source_with_dotfiles: Any, dest_with_dotfiles: Any
) -> None:
    utils.create_directory(os.path.join(dest_with_dotfiles, "aaa"))
    dploy.stow([source_with_dotfiles], dest_with_dotfiles)
    assert os.path.islink(os.path.join(dest_with_dotfiles, "aaa", "dot-ccc"))

    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    assert os.listdir(dest_with_dotfiles) == []


def test_unstow_without_dotfiles_leaves_unrelated_dotfile_alone(
    source_with_dotfiles: Any, dest_with_dotfiles: Any, capsys: Any
) -> None:
    """
    a real file at the translated name is not dploy's, so it is not a conflict
    when the flag is off and the entry was never stowed
    """
    unrelated = os.path.join(dest_with_dotfiles, ".bbb")
    utils.create_file(unrelated)

    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, is_silent=False)

    assert os.path.isfile(unrelated)
    assert "already unlinked" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("dotfiles", "other_name"), [(False, ".bbb"), (True, "dot-bbb")]
)
def test_unstow_leaves_unrelated_link_at_the_other_name_alone(
    source_with_dotfiles: Any,
    dest_with_dotfiles: Any,
    tmp_path: Any,
    dotfiles: bool,
    other_name: str,
) -> None:
    link = os.path.join(dest_with_dotfiles, other_name)
    os.symlink(str(tmp_path), link)

    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, dotfiles=dotfiles)

    assert os.path.islink(link)
    assert os.path.samefile(link, str(tmp_path))


def test_unstow_without_dotfiles_leaves_unrelated_directory_alone(
    source_with_dotfiles: Any, dest_with_dotfiles: Any
) -> None:
    _, dotfile_dir = make_dot_directory(
        source_with_dotfiles, dest_with_dotfiles, "file"
    )
    unrelated = os.path.join(dotfile_dir, "file")
    utils.create_file(unrelated)

    dploy.unstow([source_with_dotfiles], dest_with_dotfiles)

    assert os.path.isfile(unrelated)


def test_unstow_with_dotfiles_conflicts_with_unrelated_dotfile(
    source_with_dotfiles: Any, dest_with_dotfiles: Any
) -> None:
    utils.create_file(os.path.join(dest_with_dotfiles, ".bbb"))

    with pytest.raises(error.ConflictsWithExistingFile):
        dploy.unstow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)


def test_unstow_with_dot_in_exist_fold_with_dotfiles(
    source_with_dotfiles: Any, dest_with_dotfiles: Any
) -> None:
    utils.create_directory(os.path.join(dest_with_dotfiles, "aaa"))

    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)
    dploy.unstow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    # the emptied directory is removed along with the links inside it
    assert not os.path.exists(os.path.join(dest_with_dotfiles, "aaa"))
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


@pytest.mark.parametrize("unstow_dotfiles", [True, False])
def test_unstow_with_dotfiles_folds_remaining_package(
    source_with_dotfiles: Any,
    source_b: Any,
    dest_with_dotfiles: Any,
    unstow_dotfiles: bool,
) -> None:
    """
    the remaining links are named .aaa, .ccc and bbb in the destination but
    bbb, dot-aaa and dot-ccc in the package, so they sort differently on each
    side; folding must not depend on that order. They all point into
    source_with_dotfiles/aaa, so they are replaced by one link to it, and the
    unstow does not need to be given the flag the stow was
    """
    dploy.stow([source_b, source_with_dotfiles], dest_with_dotfiles, dotfiles=True)
    dploy.unstow([source_b], dest_with_dotfiles, dotfiles=unstow_dotfiles)

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
