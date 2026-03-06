"""
Tests for the CLI interface
"""

# pylint: disable=missing-docstring
# disable lint errors for function names longer that 30 characters
# pylint: disable=invalid-name

import os
import re
import pytest
import dploy.cli


def test_cli_with_stow_with_simple_senario(source_only_files, dest, capsys):
    args = ["stow", source_only_files, dest]
    dploy.cli.run(args)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_only_files", "aaa"
    )
    out, _ = capsys.readouterr()
    d = os.path.join(dest, "aaa")
    s = os.path.relpath(os.path.join(source_only_files, "aaa"), dest)
    assert out == "dploy stow: link {dest} => {source}\n".format(source=s, dest=d)


def test_cli_unstow_with_basic_senario(source_a, dest, capsys):
    args_stow = ["stow", source_a, dest]
    dploy.cli.run(args_stow)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_a", "aaa"
    )

    args_unstow = ["unstow", source_a, dest]
    dploy.cli.run(args_unstow)
    assert not os.path.exists(os.path.join(dest, "aaa"))

    out, _ = capsys.readouterr()
    src_dir = os.path.relpath(os.path.join(source_a, "aaa"), dest)
    dest_dir = os.path.join(dest, "aaa")
    expected_output = (
        "dploy stow: link {dest_dir} => {src_dir}\n"
        "dploy unstow: unlink {dest_dir} => {src_dir}\n".format(
            src_dir=src_dir, dest_dir=dest_dir
        )
    )
    assert out == (expected_output)


def test_cli_with_link_directory(source_a, dest, capsys):
    args = ["link", source_a, os.path.join(dest, "source_a_link")]
    dploy.cli.run(args)
    assert os.path.islink(os.path.join(dest, "source_a_link"))
    output, _ = capsys.readouterr()
    expected_output_unformatted = "dploy link: link {dest} => {source}\n"
    expected_output = expected_output_unformatted.format(
        source=os.path.relpath(source_a, dest), dest=os.path.join(dest, "source_a_link")
    )
    assert output == expected_output


def test_cli_with_dry_run_option_with_stow_with_simple_senario(
    source_only_files, dest, capsys
):
    args = ["--dry-run", "stow", source_only_files, dest]
    dploy.cli.run(args)
    assert not os.path.exists(os.path.join(dest, "aaa"))
    out, _ = capsys.readouterr()
    d = os.path.join(dest, "aaa")
    s = os.path.relpath(os.path.join(source_only_files, "aaa"), dest)
    assert out == "dploy stow: link {dest} => {source}\n".format(source=s, dest=d)


def test_cli_with_silent_option_with_stow_with_simple_senario(
    source_only_files, dest, capsys
):
    args = ["--silent", "stow", source_only_files, dest]
    dploy.cli.run(args)
    assert os.readlink(os.path.join(dest, "aaa")) == os.path.join(
        "..", "source_only_files", "aaa"
    )
    out, _ = capsys.readouterr()
    assert out == ""


def test_cli_with_version_option(capsys):
    args = ["--version"]
    with pytest.raises(SystemExit):
        dploy.cli.run(args)
        out, _ = capsys.readouterr()
        assert re.match(r"dploy \d+.\d+\.\d+(-\w+)?\n", out) is not None


def test_cli_stow_with_dotfiles_option(
    source_with_dotfiles, dest_with_dotfiles, capsys
):
    args = ["stow", "--dotfiles", source_with_dotfiles, dest_with_dotfiles]
    dploy.cli.run(args)
    assert os.readlink(os.path.join(dest_with_dotfiles, "aaa")) == os.path.join(
        "..", "source_with_dotfiles", "aaa"
    )
    assert os.readlink(os.path.join(dest_with_dotfiles, ".bbb")) == os.path.join(
        "..", "source_with_dotfiles", "dot-bbb"
    )

    out, _ = capsys.readouterr()
    d = os.path.join(dest_with_dotfiles, "aaa")
    s = os.path.relpath(os.path.join(source_with_dotfiles, "aaa"), dest_with_dotfiles)
    d2 = os.path.join(dest_with_dotfiles, ".bbb")
    s2 = os.path.relpath(
        os.path.join(source_with_dotfiles, "dot-bbb"), dest_with_dotfiles
    )
    assert (
        out
        == "dploy stow: link {dest} => {source}\ndploy stow: link {dest2} => {source2}\n".format(
            source=s, dest=d, source2=s2, dest2=d2
        )
    )


def test_cli_unstow_with_dotfiles_option(
    source_with_dotfiles, dest_with_dotfiles, capsys
):
    args = ["stow", "--dotfiles", source_with_dotfiles, dest_with_dotfiles]
    dploy.cli.run(args)
    args_unstow = ["unstow", "--dotfiles", source_with_dotfiles, dest_with_dotfiles]
    dploy.cli.run(args_unstow)
    assert not os.path.exists(os.path.join(dest_with_dotfiles, "aaa"))
    assert not os.path.exists(os.path.join(dest_with_dotfiles, ".bbb"))

    out, _ = capsys.readouterr()
    d = os.path.join(dest_with_dotfiles, "aaa")
    s = os.path.relpath(os.path.join(source_with_dotfiles, "aaa"), dest_with_dotfiles)
    d2 = os.path.join(dest_with_dotfiles, ".bbb")
    s2 = os.path.relpath(
        os.path.join(source_with_dotfiles, "dot-bbb"), dest_with_dotfiles
    )
    expected_output = (
        "dploy stow: link {dest} => {source}\n"
        "dploy stow: link {dest2} => {source2}\n"
        "dploy unstow: unlink {dest} => {source}\n"
        "dploy unstow: unlink {dest2} => {source2}\n".format(
            source=s, dest=d, source2=s2, dest2=d2
        )
    )
    assert out == (expected_output)
