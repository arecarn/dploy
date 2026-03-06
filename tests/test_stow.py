"""
Tests for the stow stub command
"""

import os
import re

import pytest

import dploy
from dploy import error
from tests import utils

SUBCMD = "stow"


def test_stow_with_simple_senario(source_only_files, dest) -> None:
    dploy.stow([source_only_files], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_only_files", "aaa"
    )


def test_stow_with_basic_senario(source_a, dest) -> None:
    dploy.stow([source_a], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )


def test_stow_with_the_same_tree_twice(source_a, dest) -> None:
    dploy.stow([source_a], dest)
    dploy.stow([source_a], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )


def test_stow_with_existing_file_conflicts(source_a, source_c, dest) -> None:
    dploy.stow([source_a], dest)
    source_file = os.path.join(source_c, "aaa", "aaa")
    conflicting_file = os.path.join(dest, "aaa", "aaa")
    message = str(
        error.ConflictsWithExistingFile(
            subcmd=SUBCMD, source=source_file, dest=conflicting_file
        )
    )
    with pytest.raises(error.ConflictsWithExistingFile, match=re.escape(message)):
        dploy.stow([source_c], dest)


def test_stow_with_existing_broken_link(source_a, dest) -> None:
    conflicting_link = os.path.join(dest, "aaa")
    os.symlink("non_existant_source", conflicting_link)
    with pytest.raises(error.ConflictsWithExistingLink):
        dploy.stow([source_a], dest)


def test_stow_with_source_conflicts(source_a, source_c, dest) -> None:
    conflicting_source_files = [
        os.path.join(source_a, "aaa", "aaa"),
        os.path.join(source_c, "aaa", "aaa"),
    ]
    message = str(
        error.ConflictsWithAnotherSource(subcmd=SUBCMD, files=conflicting_source_files)
    )
    with pytest.raises(error.ConflictsWithAnotherSource, match=re.escape(message)):
        dploy.stow([source_a, source_c], dest)


def test_stow_with_non_existant_source(dest) -> None:
    non_existant_source = "source"
    message = str(error.NoSuchDirectory(subcmd=SUBCMD, file=non_existant_source))
    with pytest.raises(error.NoSuchDirectory, match=re.escape(message)):
        dploy.stow([non_existant_source], dest)


def test_stow_with_duplicate_source(source_a, dest) -> None:
    message = str(error.DuplicateSource(subcmd=SUBCMD, file=source_a))
    with pytest.raises(error.DuplicateSource, match=re.escape(message)):
        dploy.stow([source_a, source_a], dest)


def test_stow_with_non_existant_dest(source_a) -> None:
    non_existant_dest = "dest"
    message = str(
        error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=non_existant_dest)
    )
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=re.escape(message)):
        dploy.stow([source_a], "dest")


def test_stow_with_file_as_source(file_a, dest) -> None:
    message = str(error.NoSuchDirectory(subcmd=SUBCMD, file=file_a))
    with pytest.raises(error.NoSuchDirectory, match=re.escape(message)):
        dploy.stow([file_a], dest)


def test_stow_with_file_as_dest(source_a, file_a) -> None:
    message = str(error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=file_a))
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=re.escape(message)):
        dploy.stow([source_a], file_a)


def test_stow_with_file_as_dest_and_source(file_a, file_b) -> None:
    message = str(error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=file_b))
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=re.escape(message)):
        dploy.stow([file_a], file_b)


def test_stow_with_same_directory_used_as_source_and_dest(source_a) -> None:
    message = str(error.SourceIsSameAsDest(subcmd=SUBCMD, file=source_a))
    with pytest.raises(error.SourceIsSameAsDest, match=re.escape(message)):
        dploy.stow([source_a], source_a)


def test_stow_with_same_simple_directory_used_as_source_and_dest(source_only_files) -> None:
    message = str(error.SourceIsSameAsDest(subcmd=SUBCMD, file=source_only_files))
    with pytest.raises(error.SourceIsSameAsDest, match=re.escape(message)):
        dploy.stow([source_only_files], source_only_files)


def test_stow_with_read_only_dest(source_a, dest) -> None:
    utils.remove_write_permission(dest)
    message = str(error.InsufficientPermissionsToSubcmdTo(subcmd=SUBCMD, file=dest))
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdTo, match=re.escape(message)
    ):
        dploy.stow([source_a], dest)


def test_stow_with_write_only_source(source_a, source_c, dest) -> None:
    utils.remove_read_permission(source_a)
    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_a)
    )
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdFrom, match=re.escape(message)
    ):
        dploy.stow([source_a, source_c], dest)


def test_stow_with_source_with_no_executue_permissions(source_a, source_c, dest) -> None:
    utils.remove_execute_permission(source_a)
    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_a)
    )
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdFrom, match=re.escape(message)
    ):
        dploy.stow([source_a, source_c], dest)


def test_stow_with_source_dir_with_no_executue_permissions(source_a, source_c, dest) -> None:
    source_dir = os.path.join(source_a, "aaa")
    utils.remove_execute_permission(source_dir)
    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_dir)
    )
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdFrom, match=re.escape(message)
    ):
        dploy.stow([source_a, source_c], dest)


def test_stow_with_write_only_source_file(source_a, dest) -> None:
    source_file = os.path.join(source_a, "aaa")
    utils.remove_read_permission(source_file)
    dploy.stow([source_a], dest)


def verify_unfolded_source_a_and_source_b(dest) -> None:
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


def test_stow_unfolding_with_two_invocations(source_a, source_b, dest) -> None:
    dploy.stow([source_a], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )
    dploy.stow([source_b], dest)
    verify_unfolded_source_a_and_source_b(dest)


def test_stow_unfolding_with_mutliple_sources(source_a, source_b, dest) -> None:
    dploy.stow([source_a, source_b], dest)
    verify_unfolded_source_a_and_source_b(dest)


def test_stow_unfolding_with_first_sources_execute_permission_removed(
    source_a, source_b, dest
) -> None:
    dploy.stow([source_a], dest)
    utils.remove_execute_permission(source_a)
    dest_dir = os.path.join(dest, "aaa")
    message = str(error.PermissionDenied(subcmd=SUBCMD, file=dest_dir))
    with pytest.raises(error.PermissionDenied, match=re.escape(message)):
        dploy.stow([source_b], dest)


def test_stow_unfolding_with_write_only_source_file(source_a, source_b, dest) -> None:
    source_file = os.path.join(source_a, "aaa")
    utils.remove_read_permission(source_file)

    with pytest.raises(error.InsufficientPermissionsToSubcmdFrom):
        dploy.stow([source_a, source_b], dest)
