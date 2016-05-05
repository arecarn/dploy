"""
Tests for the link sub command
"""
# pylint: disable=missing-docstring
# disable lint errors for function names longer that 30 characters
# pylint: disable=invalid-name

import os
import pytest
import dploy
import util


def test_link_directory(source_a, dest):
    dploy.link(source_a, os.path.join(dest, 'source_a_link'))
    assert os.path.islink(os.path.join(dest, 'source_a_link'))


def test_link_file(file_a, dest):
    dploy.link(file_a, os.path.join(dest, 'source_a_link'))
    assert os.path.islink(os.path.join(dest, 'source_a_link'))


def test_link_with_non_existant_source(dest):
    with pytest.raises(SystemExit):
        dploy.link('source_a', os.path.join(dest, 'source_a_link'))


def test_link_with_non_existant_dest(source_a):
    with pytest.raises(SystemExit):
        dploy.link(source_a, os.path.join('dest', 'source_a_link'))


def test_link_with_read_only_dest(file_a, dest):
    util.read_only(dest)
    with pytest.raises(SystemExit):
        dploy.link(file_a, os.path.join(dest, 'file_a_link'))


def test_link_with_write_only_source(file_a, dest):
    util.write_only(file_a)
    with pytest.raises(SystemExit):
        dploy.link(file_a, os.path.join(dest, 'file_a_link'))


def test_link_with_conflicting_broken_lint_at_dest(file_a, dest):
    os.symlink('non_existant_source', os.path.join(dest, 'file_a_link'))
    with pytest.raises(SystemExit):
        dploy.link(file_a, os.path.join(dest, 'file_a_link'))
