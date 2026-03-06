"""
Tests for the stow stub command
"""

# pylint: disable=missing-docstring
# disable lint errors for function names longer that 30 characters
# pylint: disable=invalid-name

import os
import pytest
import dploy
from dploy import error
from tests import utils

SUBCMD = "stow"


def test_stow_with_simple_senario(source_only_files, dest):
    dploy.stow([source_only_files], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_only_files", "aaa"
    )


def test_stow_with_basic_senario(source_a, dest):
    dploy.stow([source_a], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )


def test_stow_with_the_same_tree_twice(source_a, dest):
    dploy.stow([source_a], dest)
    dploy.stow([source_a], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )


def test_stow_with_existing_file_conflicts(source_a, source_c, dest):
    dploy.stow([source_a], dest)
    source_file = os.path.join(source_c, "aaa", "aaa")
    conflicting_file = os.path.join(dest, "aaa", "aaa")
    message = str(
        error.ConflictsWithExistingFile(
            subcmd=SUBCMD, source=source_file, dest=conflicting_file
        )
    )
    with pytest.raises(error.ConflictsWithExistingFile, match=message):
        dploy.stow([source_c], dest)


def test_stow_with_existing_broken_link(source_a, dest):
    conflicting_link = os.path.join(dest, "aaa")
    os.symlink("non_existant_source", conflicting_link)
    source_file = os.path.join(source_a, "aaa")
    message = str(
        error.ConflictsWithExistingLink(
            subcmd=SUBCMD, source=source_file, dest=conflicting_link
        )
    )
    with pytest.raises(error.ConflictsWithExistingLink):
        dploy.stow([source_a], dest)


def test_stow_with_source_conflicts(source_a, source_c, dest):
    conflicting_source_files = [
        os.path.join(source_a, "aaa", "aaa"),
        os.path.join(source_c, "aaa", "aaa"),
    ]
    message = str(
        error.ConflictsWithAnotherSource(subcmd=SUBCMD, files=conflicting_source_files)
    )
    with pytest.raises(error.ConflictsWithAnotherSource, match=message):
        dploy.stow([source_a, source_c], dest)


def test_stow_with_non_existant_source(dest):
    non_existant_source = "source"
    message = str(error.NoSuchDirectory(subcmd=SUBCMD, file=non_existant_source))
    with pytest.raises(error.NoSuchDirectory, match=message):
        dploy.stow([non_existant_source], dest)


def test_stow_with_duplicate_source(source_a, dest):
    message = str(error.DuplicateSource(subcmd=SUBCMD, file=source_a))
    with pytest.raises(error.DuplicateSource, match=message):
        dploy.stow([source_a, source_a], dest)


def test_stow_with_non_existant_dest(source_a):
    non_existant_dest = "dest"
    message = str(
        error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=non_existant_dest)
    )
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=message):
        dploy.stow([source_a], "dest")


def test_stow_with_file_as_source(file_a, dest):
    message = str(error.NoSuchDirectory(subcmd=SUBCMD, file=file_a))
    with pytest.raises(error.NoSuchDirectory, match=message):
        dploy.stow([file_a], dest)


def test_stow_with_file_as_dest(source_a, file_a):
    message = str(error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=file_a))
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=message):
        dploy.stow([source_a], file_a)


def test_stow_with_file_as_dest_and_source(file_a, file_b):
    message = str(error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=file_b))
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=message):
        dploy.stow([file_a], file_b)


def test_stow_with_same_directory_used_as_source_and_dest(source_a):
    message = str(error.SourceIsSameAsDest(subcmd=SUBCMD, file=source_a))
    with pytest.raises(error.SourceIsSameAsDest, match=message):
        dploy.stow([source_a], source_a)


def test_stow_with_same_simple_directory_used_as_source_and_dest(source_only_files):
    message = str(error.SourceIsSameAsDest(subcmd=SUBCMD, file=source_only_files))
    with pytest.raises(error.SourceIsSameAsDest, match=message):
        dploy.stow([source_only_files], source_only_files)


def test_stow_with_read_only_dest(source_a, dest):
    utils.remove_write_permission(dest)
    message = str(error.InsufficientPermissionsToSubcmdTo(subcmd=SUBCMD, file=dest))
    with pytest.raises(error.InsufficientPermissionsToSubcmdTo, match=message):
        dploy.stow([source_a], dest)


def test_stow_with_write_only_source(source_a, source_c, dest):
    utils.remove_read_permission(source_a)
    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_a)
    )
    with pytest.raises(error.InsufficientPermissionsToSubcmdFrom, match=message):
        dploy.stow([source_a, source_c], dest)


def test_stow_with_source_with_no_executue_permissions(source_a, source_c, dest):
    utils.remove_execute_permission(source_a)
    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_a)
    )
    with pytest.raises(error.InsufficientPermissionsToSubcmdFrom, match=message):
        dploy.stow([source_a, source_c], dest)


def test_stow_with_source_dir_with_no_executue_permissions(source_a, source_c, dest):
    source_dir = os.path.join(source_a, "aaa")
    utils.remove_execute_permission(source_dir)
    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_dir)
    )
    with pytest.raises(error.InsufficientPermissionsToSubcmdFrom, match=message):
        dploy.stow([source_a, source_c], dest)


def test_stow_with_write_only_source_file(source_a, dest):
    source_file = os.path.join(source_a, "aaa")
    utils.remove_read_permission(source_file)
    dploy.stow([source_a], dest)


def verify_unfolded_source_a_and_source_b(dest):
    common_dest_dir = os.path.join(dest, "aaa")
    common_source_a_dir = os.path.join("..", "..", "source_a", "aaa")
    common_source_b_dir = os.path.join("..", "..", "source_b", "aaa")
    file_maps = (
        {
            "dest": os.path.join(common_dest_dir, "aaa"),
            "source": os.path.join(common_source_a_dir, "aaa"),
        },
        {
            "dest": os.path.join(common_dest_dir, "bbb"),
            "source": os.path.join(common_source_a_dir, "bbb"),
        },
        {
            "dest": os.path.join(common_dest_dir, "ccc"),
            "source": os.path.join(common_source_a_dir, "ccc"),
        },
        {
            "dest": os.path.join(common_dest_dir, "ddd"),
            "source": os.path.join(common_source_b_dir, "ddd"),
        },
        {
            "dest": os.path.join(common_dest_dir, "eee"),
            "source": os.path.join(common_source_b_dir, "eee"),
        },
        {
            "dest": os.path.join(common_dest_dir, "fff"),
            "source": os.path.join(common_source_b_dir, "fff"),
        },
    )

    assert os.path.isdir(os.path.join(common_dest_dir))

    for file_map in file_maps:
        assert os.readlink(file_map["dest"]) == file_map["source"]


def test_stow_unfolding_with_two_invocations(source_a, source_b, dest):
    dploy.stow([source_a], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )
    dploy.stow([source_b], dest)
    verify_unfolded_source_a_and_source_b(dest)


def test_stow_unfolding_with_mutliple_sources(source_a, source_b, dest):
    dploy.stow([source_a, source_b], dest)
    verify_unfolded_source_a_and_source_b(dest)


def test_stow_unfolding_with_first_sources_execute_permission_removed(
    source_a, source_b, dest
):
    dploy.stow([source_a], dest)
    utils.remove_execute_permission(source_a)
    dest_dir = os.path.join(dest, "aaa")
    message = str(error.PermissionDenied(subcmd=SUBCMD, file=dest_dir))
    with pytest.raises(error.PermissionDenied, match=message):
        dploy.stow([source_b], dest)


def test_stow_unfolding_with_write_only_source_file(source_a, source_b, dest):
    source_file = os.path.join(source_a, "aaa")
    utils.remove_read_permission(source_file)

    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_file)
    )
    with pytest.raises(error.InsufficientPermissionsToSubcmdFrom):
        dploy.stow([source_a, source_b], dest)


def test_stow_with_dotfiles(source_with_dotfiles, dest_with_dotfiles):
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    assert os.readlink(os.path.join(dest_with_dotfiles, ".bbb")) == os.path.join(
        "..", "source_with_dotfiles", "dot-bbb"
    )
    assert os.path.islink(os.path.join(dest_with_dotfiles, "aaa"))
    assert os.readlink(os.path.join(dest_with_dotfiles, "aaa")) == os.path.join(
        "..", "source_with_dotfiles", "aaa"
    )
    assert not os.path.islink(os.path.join(dest_with_dotfiles, "aaa", "dot-aaa"))


def test_stow_with_dot_in_exist_fold_with_dotfiles(
    source_with_dotfiles, dest_with_dotfiles
):
    utils.create_directory(os.path.join(dest_with_dotfiles, "aaa"))
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    assert not os.path.islink(os.path.join(dest_with_dotfiles, "aaa"))
    assert os.readlink(os.path.join(dest_with_dotfiles, "aaa", ".aaa")) == os.path.join(
        "..", "..", "source_with_dotfiles", "aaa", "dot-aaa"
    )


def test_stow_with_dot_in_exist_fold_exist_other_with_dotfiles(
    source_with_dotfiles, dest_with_dotfiles
):
    utils.create_directory(os.path.join(dest_with_dotfiles, "aaa"))
    utils.create_file(os.path.join(dest_with_dotfiles, "aaa", ".keep"))
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    assert os.readlink(os.path.join(dest_with_dotfiles, "aaa", ".aaa")) == os.path.join(
        "..", "..", "source_with_dotfiles", "aaa", "dot-aaa"
    )

    assert os.readlink(os.path.join(dest_with_dotfiles, "aaa", ".ccc")) == os.path.join(
        "..", "..", "source_with_dotfiles", "aaa", "dot-ccc"
    )

    assert not os.path.islink(
        os.path.join(dest_with_dotfiles, "aaa", ".ccc", "dot-aaa")
    )
    assert not os.path.islink(os.path.join(dest_with_dotfiles, "aaa", ".ccc", "bbb"))
