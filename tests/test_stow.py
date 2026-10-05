"""
Tests for the stow stub command
"""

from __future__ import annotations

import os
import re
import sys
from typing import TYPE_CHECKING

import pytest

import dploy
from dploy import error, stowcmd
from tests import utils

if TYPE_CHECKING:
    from typing import Any

SUBCMD = "stow"


def test_stow_with_simple_senario(source_only_files: Any, dest: Any) -> None:
    dploy.stow([source_only_files], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_only_files", "aaa"
    )


def test_stow_with_basic_senario(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )


def test_stow_with_the_same_tree_twice(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest)
    dploy.stow([source_a], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )


def test_stow_with_existing_file_conflicts(
    source_a: Any, source_c: Any, dest: Any
) -> None:
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


def test_stow_with_existing_broken_link(source_a: Any, dest: Any) -> None:
    conflicting_link = os.path.join(dest, "aaa")
    os.symlink("non_existant_source", conflicting_link)
    with pytest.raises(error.ConflictsWithExistingLink):
        dploy.stow([source_a], dest)


def create_partial_conflicts_for_source_a(dest: Any) -> tuple[str, str]:
    """
    Create an unmanaged file and a broken link in dest where source_a's
    aaa/bbb and aaa/ccc would be linked, leaving aaa/aaa free of conflicts.
    """
    utils.create_directory(os.path.join(dest, "aaa"))
    conflicting_file = os.path.join(dest, "aaa", "bbb")
    utils.create_file(conflicting_file)
    conflicting_link = os.path.join(dest, "aaa", "ccc")
    os.symlink("non_existant_source", conflicting_link)
    return conflicting_file, conflicting_link


def test_stow_with_partial_conflicts_links_nothing(source_a: Any, dest: Any) -> None:
    create_partial_conflicts_for_source_a(dest)
    with pytest.raises(error.ConflictsWithExistingFile):
        dploy.stow([source_a], dest)
    assert not os.path.islink(os.path.join(dest, "aaa", "aaa"))


def test_stow_with_skip_conflicts_links_non_conflicting_files(
    source_a: Any, dest: Any, capsys: Any
) -> None:
    conflicting_file, conflicting_link = create_partial_conflicts_for_source_a(dest)

    dploy.stow([source_a], dest, is_silent=False, skip_conflicts=True)

    assert os.readlink(os.path.join(dest, "aaa", "aaa")) == os.path.join(
        "..", "..", "source_a", "aaa", "aaa"
    )
    assert not os.path.islink(conflicting_file)
    assert os.readlink(conflicting_link) == "non_existant_source"

    _, err = capsys.readouterr()
    file_conflict = error.ConflictsWithExistingFile(
        subcmd=SUBCMD,
        source=os.path.join(source_a, "aaa", "bbb"),
        dest=conflicting_file,
    )
    link_conflict = error.ConflictsWithExistingLink(
        subcmd=SUBCMD,
        source=os.path.join(source_a, "aaa", "ccc"),
        dest=conflicting_link,
    )
    assert f"{file_conflict}\n" in err
    assert f"{link_conflict}\n" in err


def test_stow_with_skip_conflicts_keeps_source_conflicts_fatal(
    source_a: Any, source_c: Any, dest: Any
) -> None:
    with pytest.raises(error.ConflictsWithAnotherSource):
        dploy.stow([source_a, source_c], dest, skip_conflicts=True)


def test_stow_with_source_conflicts(source_a: Any, source_c: Any, dest: Any) -> None:
    conflicting_source_files = [
        os.path.join(source_a, "aaa", "aaa"),
        os.path.join(source_c, "aaa", "aaa"),
    ]
    message = str(
        error.ConflictsWithAnotherSource(subcmd=SUBCMD, files=conflicting_source_files)
    )
    with pytest.raises(error.ConflictsWithAnotherSource, match=re.escape(message)):
        dploy.stow([source_a, source_c], dest)


def test_stow_with_non_existant_source(dest: Any) -> None:
    non_existant_source = "source"
    message = str(error.NoSuchDirectory(subcmd=SUBCMD, file=non_existant_source))
    with pytest.raises(error.NoSuchDirectory, match=re.escape(message)):
        dploy.stow([non_existant_source], dest)


def test_stow_with_duplicate_source(source_a: Any, dest: Any) -> None:
    message = str(error.DuplicateSource(subcmd=SUBCMD, file=source_a))
    with pytest.raises(error.DuplicateSource, match=re.escape(message)):
        dploy.stow([source_a, source_a], dest)


def test_stow_with_non_existant_dest(source_a: Any) -> None:
    non_existant_dest = "dest"
    message = str(
        error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=non_existant_dest)
    )
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=re.escape(message)):
        dploy.stow([source_a], "dest")


def test_stow_with_file_as_source(file_a: Any, dest: Any) -> None:
    message = str(error.NoSuchDirectory(subcmd=SUBCMD, file=file_a))
    with pytest.raises(error.NoSuchDirectory, match=re.escape(message)):
        dploy.stow([file_a], dest)


def test_stow_with_file_as_dest(source_a: Any, file_a: Any) -> None:
    message = str(error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=file_a))
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=re.escape(message)):
        dploy.stow([source_a], file_a)


def test_stow_with_file_as_dest_and_source(file_a: Any, file_b: Any) -> None:
    message = str(error.NoSuchDirectoryToSubcmdInto(subcmd=SUBCMD, file=file_b))
    with pytest.raises(error.NoSuchDirectoryToSubcmdInto, match=re.escape(message)):
        dploy.stow([file_a], file_b)


def test_stow_with_same_directory_used_as_source_and_dest(source_a: Any) -> None:
    message = str(error.SourceIsSameAsDest(subcmd=SUBCMD, file=source_a))
    with pytest.raises(error.SourceIsSameAsDest, match=re.escape(message)):
        dploy.stow([source_a], source_a)


def test_stow_with_same_simple_directory_used_as_source_and_dest(
    source_only_files: Any,
) -> None:
    message = str(error.SourceIsSameAsDest(subcmd=SUBCMD, file=source_only_files))
    with pytest.raises(error.SourceIsSameAsDest, match=re.escape(message)):
        dploy.stow([source_only_files], source_only_files)


@utils.skip_on_windows_permissions
def test_stow_with_read_only_dest(source_a: Any, dest: Any) -> None:
    utils.remove_write_permission(dest)
    message = str(error.InsufficientPermissionsToSubcmdTo(subcmd=SUBCMD, file=dest))
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdTo, match=re.escape(message)
    ):
        dploy.stow([source_a], dest)


@utils.skip_on_windows_permissions
def test_stow_with_write_only_source(source_a: Any, source_c: Any, dest: Any) -> None:
    utils.remove_read_permission(source_a)
    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_a)
    )
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdFrom, match=re.escape(message)
    ):
        dploy.stow([source_a, source_c], dest)


@utils.skip_on_windows_permissions
def test_stow_with_source_with_no_executue_permissions(
    source_a: Any, source_c: Any, dest: Any
) -> None:
    utils.remove_execute_permission(source_a)
    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_a)
    )
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdFrom, match=re.escape(message)
    ):
        dploy.stow([source_a, source_c], dest)


@utils.skip_on_windows_permissions
def test_stow_with_source_dir_with_no_executue_permissions(
    source_a: Any, source_c: Any, dest: Any
) -> None:
    source_dir = os.path.join(source_a, "aaa")
    utils.remove_execute_permission(source_dir)
    message = str(
        error.InsufficientPermissionsToSubcmdFrom(subcmd=SUBCMD, file=source_dir)
    )
    with pytest.raises(
        error.InsufficientPermissionsToSubcmdFrom, match=re.escape(message)
    ):
        dploy.stow([source_a, source_c], dest)


def test_stow_with_write_only_source_file(source_a: Any, dest: Any) -> None:
    source_file = os.path.join(source_a, "aaa")
    utils.remove_read_permission(source_file)
    dploy.stow([source_a], dest)


def verify_unfolded_source_a_and_source_b(dest: Any) -> None:
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


def test_stow_unfolding_with_two_invocations(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    dploy.stow([source_a], dest)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )
    dploy.stow([source_b], dest)
    verify_unfolded_source_a_and_source_b(dest)


def test_stow_unfolding_with_mutliple_sources(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    dploy.stow([source_a, source_b], dest)
    verify_unfolded_source_a_and_source_b(dest)


def test_stow_unfolding_with_shared_directory_two_levels_deep(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """
    source_a and source_b live under unrelated roots (not siblings under
    one shared parent) and share a directory two levels deep ("x/y") that
    diverges only at the leaf file. Stowing source_a alone folds "x" into
    a single link; stowing source_b must unfold all the way down to "y",
    not just to "x", so source_b's file lands in dest instead of inside
    source_a's own tree. Unstowing both afterward must also leave dest
    clean, without conflicting with an existing link.
    """
    source_a = tmp_path_factory.mktemp("root_a") / "pkg"
    source_b = tmp_path_factory.mktemp("root_b") / "pkg"
    dest = tmp_path_factory.mktemp("dest")
    (source_a / "x" / "y").mkdir(parents=True)
    (source_a / "x" / "y" / "one").touch()
    (source_b / "x" / "y").mkdir(parents=True)
    (source_b / "x" / "y" / "two").touch()

    dploy.stow([str(source_a)], str(dest))
    dploy.stow([str(source_b)], str(dest))

    assert (dest / "x" / "y" / "one").resolve() == source_a / "x" / "y" / "one"
    assert (dest / "x" / "y" / "two").resolve() == source_b / "x" / "y" / "two"
    assert [p.name for p in (source_a / "x" / "y").iterdir()] == ["one"]

    dploy.unstow([str(source_b)], str(dest))
    dploy.unstow([str(source_a)], str(dest))

    assert not os.path.exists(dest / "x")


@pytest.mark.xfail(
    sys.version_info >= (3, 14),
    reason=(
        "#31: Path.exists() no longer raises PermissionError on 3.14, so the "
        "permission failure is misreported as a conflict"
    ),
    strict=True,
)
@utils.skip_on_windows_permissions
def test_stow_unfolding_with_first_sources_execute_permission_removed(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    dploy.stow([source_a], dest)
    utils.remove_execute_permission(source_a)
    dest_dir = os.path.join(dest, "aaa")
    message = str(error.PermissionDenied(subcmd=SUBCMD, file=dest_dir))
    with pytest.raises(error.PermissionDenied, match=re.escape(message)):
        dploy.stow([source_b], dest)


@utils.skip_on_windows_permissions
def test_stow_unfolding_with_write_only_source_file(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    source_file = os.path.join(source_a, "aaa")
    utils.remove_read_permission(source_file)

    with pytest.raises(error.InsufficientPermissionsToSubcmdFrom):
        dploy.stow([source_a, source_b], dest)


def test_stow_with_dotfiles(source_with_dotfiles: Any, dest_with_dotfiles: Any) -> None:
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
    source_with_dotfiles: Any, dest_with_dotfiles: Any
) -> None:
    utils.create_directory(os.path.join(dest_with_dotfiles, "aaa"))
    dploy.stow([source_with_dotfiles], dest_with_dotfiles, dotfiles=True)

    assert not os.path.islink(os.path.join(dest_with_dotfiles, "aaa"))
    assert os.readlink(os.path.join(dest_with_dotfiles, "aaa", ".aaa")) == os.path.join(
        "..", "..", "source_with_dotfiles", "aaa", "dot-aaa"
    )


def test_stow_with_dot_in_exist_fold_exist_other_with_dotfiles(
    source_with_dotfiles: Any, dest_with_dotfiles: Any
) -> None:
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


@pytest.mark.parametrize(
    ("source_name", "expected"),
    [
        ("dot-bashrc", ".bashrc"),
        ("dot-config", ".config"),
        ("dot-..", "..."),
        ("bashrc", "bashrc"),
        (".bashrc", ".bashrc"),
        ("adot-bashrc", "adot-bashrc"),
        # would translate to the destination itself
        ("dot-", "dot-"),
        # would translate to the destination's parent
        ("dot-.", "dot-."),
    ],
)
def test_translate_dotfile_name(source_name: str, expected: str) -> None:
    assert stowcmd.translate_dotfile_name(source_name) == expected


@utils.skip_on_windows_trailing_dot
def test_stow_with_dotfiles_does_not_escape_dest(tmpdir: Any) -> None:
    """
    a source directory named 'dot-.' would translate to '..', which would
    place the link outside the destination. it is left untranslated instead.
    """
    source = tmpdir.mkdir("source")
    package = source.mkdir("dot-.")
    utils.create_file(os.path.join(str(package), "payload"))
    dest = tmpdir.mkdir("dest")

    dploy.stow([str(source)], str(dest), dotfiles=True)

    assert sorted(os.listdir(str(tmpdir))) == ["dest", "source"]
    assert os.readlink(os.path.join(str(dest), "dot-.")) == os.path.join(
        "..", "source", "dot-."
    )


def test_stow_with_no_folding(source_a: Any, dest: Any) -> None:
    dploy.stow([source_a], dest, is_folding=False)
    dest_dir = os.path.join(dest, "aaa")
    source_dir = os.path.join("..", "..", "source_a", "aaa")
    assert os.path.isdir(dest_dir) and not os.path.islink(dest_dir)
    assert os.readlink(os.path.join(dest_dir, "aaa")) == os.path.join(source_dir, "aaa")
    assert os.readlink(os.path.join(dest_dir, "bbb")) == os.path.join(source_dir, "bbb")
    nested_dest_dir = os.path.join(dest_dir, "ccc")
    assert os.path.isdir(nested_dest_dir) and not os.path.islink(nested_dest_dir)
    assert os.readlink(os.path.join(nested_dest_dir, "aaa")) == os.path.join(
        "..", source_dir, "ccc", "aaa"
    )


def test_stow_with_no_folding_with_multiple_sources(
    source_a: Any, source_b: Any, dest: Any
) -> None:
    dploy.stow([source_a, source_b], dest, is_folding=False)
    for name in ("aaa", "bbb", "ddd", "eee"):
        assert os.path.islink(os.path.join(dest, "aaa", name))
    for name in ("ccc", "fff"):
        nested_dest_dir = os.path.join(dest, "aaa", name)
        assert os.path.isdir(nested_dest_dir) and not os.path.islink(nested_dest_dir)
