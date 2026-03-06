"""
Contains the fixtures used by the dploy tests
"""

import pytest
from tests import utils


@pytest.fixture()
def source_a(tmpdir):
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
def source_b(tmpdir):
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
def source_d(tmpdir):
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
def source_c(tmpdir):
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
def source_only_files(tmpdir):
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
def dest(tmpdir):
    """
    a destination directory to stow into or unstow from
    """
    name = str(tmpdir.join("dest"))
    utils.create_directory(name)
    yield name
    utils.restore_tree_permissions(tmpdir)


@pytest.fixture()
def file_a(tmpdir):
    """
    creates a file
    """
    name = str(tmpdir.join("file_a"))
    utils.create_file(name)
    return name


@pytest.fixture()
def file_b(tmpdir):
    """
    creates a file
    """
    name = str(tmpdir.join("file_b"))
    utils.create_file(name)
    return name


@pytest.fixture()
def file_dploystowignore(tmpdir):
    """
    creates an empty ignore file file
    """
    name = str(tmpdir.join(".dploystowignore"))
    utils.create_file(name)
    return name


@pytest.fixture(scope="function")
def source_with_dotfiles(tmpdir):
    """
    a source directory to stow and unstow that contains files and folders named with prefix 'dot-'
    """
    name = str(tmpdir.join("source_with_dotfiles"))
    tree = [
        {
            name: [
                {
                    "aaa": [
                        "dot-aaa",
                        "bbb",
                        {
                            "dot-ccc": [
                                "dot-aaa",
                                "bbb",
                            ],
                        },
                    ],
                },
                "dot-bbb",
            ],
        },
    ]
    utils.create_tree(tree)
    yield name
    utils.remove_tree(name)


@pytest.fixture(scope="function")
def dest_with_dotfiles(tmpdir):
    """
    a destination directory to stow into or unstow from with dotfiles
    """
    name = str(tmpdir.join("dest_with_dotfiles"))
    utils.create_directory(name)
    yield name
    utils.remove_tree(name)
