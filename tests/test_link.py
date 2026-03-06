"""
Tests for the link sub command
"""

import os
import pytest
import dploy
from dploy import error
from tests import utils

SUBCMD = "link"


def test_link_with_directory_as_source(source_a, dest):
    dploy.link(source_a, os.path.join(dest, "source_a_link"))
    assert os.path.islink(os.path.join(dest, "source_a_link"))


def test_link_with_file_as_source(file_a, dest):
    dploy.link(file_a, os.path.join(dest, "file_a"))
    assert os.path.islink(os.path.join(dest, "file_a"))


def test_link_with_non_existant_source(dest):
    non_existant_source = "source_a"
    message = str(error.NoSuchFileOrDirectory(subcmd=SUBCMD, file=non_existant_source))
    with pytest.raises(error.NoSuchFileOrDirectory, match=message):
        dploy.link(non_existant_source, os.path.join(dest, "source_a_link"))


def test_link_with_non_existant_dest(source_a):
    non_existant_dest = "dest"
    message = str(error.NoSuchFileOrDirectory(subcmd=SUBCMD, file=non_existant_dest))
    with pytest.raises(error.NoSuchFileOrDirectory, match=message):
        dploy.link(source_a, os.path.join(non_existant_dest, "source_a_link"))


def test_link_with_read_only_dest(file_a, dest):
    dest_file = os.path.join(dest, "file_a_link")
    utils.remove_write_permission(dest)
    message = str(
        error.InsufficientPermissionsToSubcmdTo(subcmd=SUBCMD, file=dest_file)
    )
    with pytest.raises(error.InsufficientPermissionsToSubcmdTo, match=message):
        dploy.link(file_a, dest_file)


def test_link_with_write_only_source(file_a, dest):
    dest_file = os.path.join(dest, "file_a_link")
    utils.remove_read_permission(file_a)
    message = str(error.InsufficientPermissions(subcmd=SUBCMD, file=file_a))
    with pytest.raises(error.InsufficientPermissions, match=message):
        dploy.link(file_a, dest_file)


def test_link_with_conflicting_broken_link_at_dest(file_a, dest):
    dest_file = os.path.join(dest, "file_a_link")
    os.symlink("non_existant_source", dest_file)
    message = str(
        error.ConflictsWithExistingLink(subcmd=SUBCMD, source=file_a, dest=dest_file)
    )
    with pytest.raises(error.ConflictsWithExistingLink, match=message):
        dploy.link(file_a, dest_file)
