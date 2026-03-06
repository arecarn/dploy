"""
Contains the fixtures used by the dploy tests
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests import utils

if TYPE_CHECKING:
    from typing import Any, Iterator


@pytest.fixture()
def source_a(tmpdir: Any) -> Iterator[str]:
    """
    a source directory to stow and unstow
    """
    name = str(tmpdir.join("source_a"))
    tree = [
        {
            name: [
                {
                    "aaa": [
                        "aaa",
                        "bbb",
                        {
                            "ccc": [
                                "aaa",
                                "bbb",
                            ],
                        },
                    ],
                },
            ],
        },
    ]
    utils.create_tree(tree)
    yield name
    utils.restore_tree_permissions(tmpdir)


@pytest.fixture()
def source_b(tmpdir: Any) -> Iterator[str]:
    """
    a source directory to stow and unstow
    """
    name = str(tmpdir.join("source_b"))
    tree = [
        {
            name: [
                {
                    "aaa": [
                        "ddd",
                        "eee",
                        {
                            "fff": [
                                "aaa",
                                "bbb",
                            ],
                        },
                    ],
                },
            ],
        },
    ]
    utils.create_tree(tree)
    yield name
    utils.restore_tree_permissions(tmpdir)


@pytest.fixture()
def source_d(tmpdir: Any) -> Iterator[str]:
    """
    a source directory to stow and unstow
    """
    name = str(tmpdir.join("source_d"))
    tree = [
        {
            name: [
                {
                    "aaa": [
                        "ggg",
                        "hhh",
                        {
                            "iii": [
                                "aaa",
                                "bbb",
                            ],
                        },
                    ],
                },
            ],
        },
    ]
    utils.create_tree(tree)
    yield name
    utils.restore_tree_permissions(tmpdir)


@pytest.fixture()
def source_c(tmpdir: Any) -> Iterator[str]:
    """
    a source directory to stow and unstow identical to source_a
    """
    name = str(tmpdir.join("source_c"))
    tree = [
        {
            name: [
                {
                    "aaa": [
                        "aaa",
                        "bbb",
                        {
                            "ccc": [
                                "aaa",
                                "bbb",
                            ],
                        },
                    ],
                },
            ],
        },
    ]
    utils.create_tree(tree)
    yield name
    utils.restore_tree_permissions(tmpdir)


@pytest.fixture()
def source_only_files(tmpdir: Any) -> Iterator[str]:
    """
    a source directory to stow and unstow that only contains files
    """
    name = str(tmpdir.join("source_only_files"))
    tree = [
        {
            name: [
                "aaa",
            ]
        }
    ]
    utils.create_tree(tree)
    yield name
    utils.restore_tree_permissions(tmpdir)


@pytest.fixture()
def dest(tmpdir: Any) -> Iterator[str]:
    """
    a destination directory to stow into or unstow from
    """
    name = str(tmpdir.join("dest"))
    utils.create_directory(name)
    yield name
    utils.restore_tree_permissions(tmpdir)


@pytest.fixture()
def file_a(tmpdir: Any) -> str:
    """
    creates a file
    """
    name = str(tmpdir.join("file_a"))
    utils.create_file(name)
    return name


@pytest.fixture()
def file_b(tmpdir: Any) -> str:
    """
    creates a file
    """
    name = str(tmpdir.join("file_b"))
    utils.create_file(name)
    return name


@pytest.fixture()
def file_dploystowignore(tmpdir: Any) -> str:
    """
    creates an empty ignore file file
    """
    name = str(tmpdir.join(".dploystowignore"))
    utils.create_file(name)
    return name
