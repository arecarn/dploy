"""
The logic and workings behind the link sub-commands
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dploy import actions, error, main, utils

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence


class Link(main.AbstractBaseSubCommand):
    """
    Concrete class implementation of the link sub-command
    """

    def __init__(
        self,
        source: str | Path,
        dest: str | Path,
        is_silent: bool = True,
        is_dry_run: bool = False,
        ignore_patterns: list[str] | None = None,
    ) -> None:
        super().__init__("link", [source], dest, is_silent, is_dry_run, ignore_patterns)

    def _is_valid_input(self, sources: Sequence[Path], dest: Path) -> bool:
        """
        Check to see if the input is valid
        """
        return LinkInput(self.errors, self.subcmd).is_valid(sources, dest)

    def _collect_actions(self, source: Path, dest: Path) -> None:
        """
        Concrete method to collect required actions to perform a link
        sub-command
        """

        if dest.exists():
            if utils.is_same_file(dest, source):
                self.actions.add(actions.AlreadyLinked(self.subcmd, source, dest))
            else:
                self.errors.add(
                    error.ConflictsWithExistingFile(self.subcmd, source, dest)
                )
        elif dest.is_symlink():
            self.errors.add(error.ConflictsWithExistingLink(self.subcmd, source, dest))

        elif not dest.parent.exists():
            self.errors.add(error.NoSuchDirectoryToSubcmdInto(self.subcmd, dest.parent))

        else:
            self.actions.add(actions.SymbolicLink(self.subcmd, source, dest))


class LinkInput(main.Input):
    """
    Input validator for the link command
    """

    def _is_valid_dest(self, dest: Path) -> bool:
        if not dest.parent.exists():
            self.errors.add(error.NoSuchFileOrDirectory(self.subcmd, dest.parent))
            return False

        if not utils.is_file_writable(dest.parent) or not utils.is_directory_writable(
            dest.parent
        ):
            self.errors.add(error.InsufficientPermissionsToSubcmdTo(self.subcmd, dest))
            return False

        return True

    def _is_valid_source(self, source: Path) -> bool:
        if not source.exists():
            self.errors.add(error.NoSuchFileOrDirectory(self.subcmd, source))
            return False

        if not utils.is_file_readable(source) or not utils.is_directory_readable(
            source
        ):
            self.errors.add(error.InsufficientPermissions(self.subcmd, source))
            return False

        return True
