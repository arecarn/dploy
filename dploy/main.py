"""
The logic and workings behind the stow and unstow sub-commands
"""

from __future__ import annotations

import pathlib
from collections import defaultdict
from typing import TYPE_CHECKING

from dploy import actions, error, ignore

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


class Input:
    """
    Input validator abstract base class
    """

    def __init__(self, errors: error.Errors, subcmd: str) -> None:
        self.errors = errors
        self.subcmd = subcmd

    def is_valid(self, packages: Sequence[Path], destination: Path) -> bool:
        """
        Checks if the passed in packages and destination are valid
        """
        is_input_valid = True
        if not self._is_there_duplicate_packages(
            packages
        ) and self._is_valid_destination(destination):
            for package in packages:
                if not self._is_valid_package(package):
                    is_input_valid = False
        else:
            is_input_valid = False

        return is_input_valid

    def _is_there_duplicate_packages(self, packages: Sequence[Path]) -> bool:
        """
        Checks packages to see if there are any duplicates
        """

        is_there_duplicates = False

        tally: dict[Path, int] = defaultdict(int)
        for package in packages:
            tally[package] += 1

        for package, count in tally.items():
            if count > 1:
                is_there_duplicates = True
                self.errors.add(error.DuplicateSource(self.subcmd, package))

        return is_there_duplicates

    def _is_valid_destination(self, destination: Path) -> bool:  # pylint: disable=unused-argument
        """
        Abstract method to check if the destination input to a sub-command is valid
        """
        return True

    def _is_valid_package(self, package: Path) -> bool:  # pylint: disable=unused-argument
        """
        Abstract method to check if the package input to a sub-command is valid
        """
        return True


class AbstractBaseSubCommand:
    """
    An abstract class to unify shared functionality in stow commands
    """

    def __init__(
        self,
        subcmd: str,
        packages: Sequence[str | Path],
        destination: str | Path,
        is_silent: bool,
        is_dry_run: bool,
        ignore_patterns: list[str] | None,
    ) -> None:
        self.subcmd = subcmd

        self.actions = actions.Actions(is_silent, is_dry_run)
        self.errors = error.Errors(is_silent)

        self.is_silent = is_silent
        self.is_dry_run = is_dry_run

        self.destination_input = pathlib.Path(destination)
        package_inputs = [pathlib.Path(package) for package in packages]

        if self._is_valid_input(package_inputs, self.destination_input):
            for package in package_inputs:
                self.ignore = ignore.Ignore(ignore_patterns, package)

                if self.ignore.should_ignore(package):
                    self.ignore.ignore(package)
                    continue

                self._collect_actions(package, self.destination_input)

        self._check_for_other_actions()
        self._execute_actions()

    def _check_for_other_actions(self) -> None:
        """
        Abstract method for examine the existing action to see if more actions
        need to be added or if some actions need to be removed.
        """

    def _is_valid_input(  # pylint: disable=unused-argument
        self, packages: Sequence[Path], destination: Path
    ) -> bool:
        """
        Abstract method to check if the input to a sub-command is valid
        """
        return True

    def _collect_actions(self, package: Path, destination: Path) -> None:
        """
        Abstract method that collects the actions required to complete a
        sub-command.
        """

    def _execute_actions(self) -> None:
        """
        Either executes collected actions by a sub command or raises collected
        exceptions.
        """
        self.errors.handle()
        self.actions.execute()
