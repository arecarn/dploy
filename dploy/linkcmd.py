"""
The logic and workings behind the link sub-commands
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dploy import actions, error, main, utils

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


class Link(main.AbstractBaseSubCommand):
    """
    Concrete class implementation of the link sub-command
    """

    def __init__(
        self,
        source: str | Path,
        destination: str | Path,
        is_silent: bool = True,
        is_dry_run: bool = False,
        ignore_patterns: list[str] | None = None,
    ) -> None:
        super().__init__(
            "link", [source], destination, is_silent, is_dry_run, ignore_patterns
        )

    def _is_valid_input(self, packages: Sequence[Path], destination: Path) -> bool:
        """
        Check to see if the input is valid. Parameter named `packages` only to
        match the `AbstractBaseSubCommand` signature it overrides (enforced by
        `ty`'s override check) -- link's argument is a single file or
        directory, not a package.
        """
        return LinkInput(self.errors, self.subcmd).is_valid(packages, destination)

    def _collect_actions(self, package: Path, destination: Path) -> None:
        """
        Concrete method to collect required actions to perform a link
        sub-command. Parameter named `package` only to match the
        `AbstractBaseSubCommand` signature it overrides (enforced by `ty`'s
        override check) -- link's argument is a single file or directory, not
        a package.
        """

        if destination.exists():
            if utils.is_same_file(destination, package):
                self.actions.add(
                    actions.AlreadyLinked(self.subcmd, package, destination)
                )
            else:
                self.errors.add(
                    error.ConflictsWithExistingFile(self.subcmd, package, destination)
                )
        elif destination.is_symlink():
            self.errors.add(
                error.ConflictsWithExistingLink(self.subcmd, package, destination)
            )

        elif not destination.parent.exists():
            self.errors.add(
                error.NoSuchDirectoryToSubcmdInto(self.subcmd, destination.parent)
            )

        else:
            self.actions.add(actions.SymbolicLink(self.subcmd, package, destination))


class LinkInput(main.Input):
    """
    Input validator for the link command
    """

    def _is_valid_destination(self, destination: Path) -> bool:
        if not destination.parent.exists():
            self.errors.add(
                error.NoSuchFileOrDirectory(self.subcmd, destination.parent)
            )
            return False

        if not utils.is_file_writable(
            destination.parent
        ) or not utils.is_directory_writable(destination.parent):
            self.errors.add(
                error.InsufficientPermissionsToSubcmdTo(self.subcmd, destination)
            )
            return False

        return True

    def _is_valid_package(self, package: Path) -> bool:
        """
        Overrides Input._is_valid_package. Parameter named `package` only to
        match the signature it overrides (enforced by `ty`'s override check)
        -- the link command's argument is a single file or directory, not a
        package (CONTEXT.md).
        """
        if not package.exists():
            self.errors.add(error.NoSuchFileOrDirectory(self.subcmd, package))
            return False

        if not utils.is_file_readable(package) or not utils.is_directory_readable(
            package
        ):
            self.errors.add(error.InsufficientPermissions(self.subcmd, package))
            return False

        return True
