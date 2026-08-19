"""
The command line interface
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from dploy import linkcmd, stowcmd, version
from dploy.error import DployError

if TYPE_CHECKING:
    from collections.abc import Sequence


def add_ignore_argument(parser: argparse.ArgumentParser) -> None:
    """
    adds the ignore argument to a subcmd parser
    """
    parser.add_argument(
        "--ignore",
        dest="ignore_patterns",
        action="append",
        default=None,
        help="glob pattern used to ignore directories",
    )


def add_dotfiles_argument(parser: argparse.ArgumentParser) -> None:
    """
    add the --dotfiles argument to a sub-command parser
    """
    parser.add_argument(
        "--dotfiles",
        dest="dotfiles",
        action="store_true",
        help=(
            "stow a source named 'dot-something' as a destination named "
            "'.something'. Must be passed to unstow as well"
        ),
    )


def create_parser() -> argparse.ArgumentParser:
    """
    create the CLI argument parser
    """
    parser = argparse.ArgumentParser(prog="dploy")

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version.__version__}",
    )
    parser.add_argument(
        "--silent", dest="is_silent", action="store_true", help="suppress all output"
    )
    parser.add_argument(
        "--dry-run",
        dest="is_dry_run",
        action="store_true",
        help="show what would be done without doing it",
    )

    sub_parsers = parser.add_subparsers(dest="subcmd")

    stow_parser = sub_parsers.add_parser("stow")
    stow_parser.add_argument("source", nargs="+", help="source directory to stow")
    stow_parser.add_argument("dest", help="destination path to stow into")
    add_dotfiles_argument(stow_parser)
    add_ignore_argument(stow_parser)

    unstow_parser = sub_parsers.add_parser("unstow")
    unstow_parser.add_argument(
        "source", nargs="+", help="source directory to unstow from"
    )
    unstow_parser.add_argument("dest", help="destination path to unstow")
    add_dotfiles_argument(unstow_parser)
    add_ignore_argument(unstow_parser)

    clean_parser = sub_parsers.add_parser("clean")
    clean_parser.add_argument(
        "source", nargs="+", help="source directory to clean from"
    )
    clean_parser.add_argument("dest", help="destination path to clean")
    add_ignore_argument(clean_parser)

    link_parser = sub_parsers.add_parser("link")
    link_parser.add_argument("source", help="source file or directory to link")
    link_parser.add_argument("dest", help="destination path to link")
    add_ignore_argument(link_parser)
    return parser


def run(arguments: Sequence[str] | None = None) -> None:
    """
    interpret the parser arguments and execute the corresponding commands
    """

    # --dotfiles is a stow-family concept, so those sub-commands are dispatched
    # separately rather than giving clean and link a parameter they ignore
    stow_subcmd_map: dict[str, type[stowcmd.Stow | stowcmd.UnStow]] = {
        "stow": stowcmd.Stow,
        "unstow": stowcmd.UnStow,
    }
    other_subcmd_map: dict[str, type[stowcmd.Clean | linkcmd.Link]] = {
        "clean": stowcmd.Clean,
        "link": linkcmd.Link,
    }

    try:
        parser = create_parser()

        if arguments is None:
            args = parser.parse_args()
        else:
            args = parser.parse_args(arguments)

        if args.subcmd not in stow_subcmd_map and args.subcmd not in other_subcmd_map:
            parser.print_help()
            sys.exit(0)

        try:
            if args.subcmd in stow_subcmd_map:
                stow_subcmd_map[args.subcmd](
                    args.source,
                    args.dest,
                    is_silent=args.is_silent,
                    is_dry_run=args.is_dry_run,
                    ignore_patterns=args.ignore_patterns,
                    dotfiles=args.dotfiles,
                )
            else:
                other_subcmd_map[args.subcmd](
                    args.source,
                    args.dest,
                    is_silent=args.is_silent,
                    is_dry_run=args.is_dry_run,
                    ignore_patterns=args.ignore_patterns,
                )
        except DployError:
            sys.exit(1)

    except KeyboardInterrupt as error:
        print(error, file=sys.stderr)
        sys.exit(130)
