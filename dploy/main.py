"""
The logic and workings behind the stow and unstow sub-commands
"""

from __future__ import annotations

import pathlib
from collections import defaultdict
from typing import TYPE_CHECKING

from dploy import actions, error, ignore

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence


class Input:
    """
    Input validator abstract base class
    """

    def __init__(self, errors: error.Errors, subcmd: str) -> None:
        self.errors = errors
        self.subcmd = subcmd

    def is_valid(self, sources: Sequence[Path], dest: Path) -> bool:
        """
        Checks if the passes in source and dest are valid
        """
        is_input_valid = True
        if not self._is_there_duplicate_sources(sources) and self._is_valid_dest(dest):
            for source in sources:
                if not self._is_valid_source(source):
                    is_input_valid = False
        else:
            is_input_valid = False

        return is_input_valid

    def _is_there_duplicate_sources(self, sources: Sequence[Path]) -> bool:
        """
        Checks sources to see if there are any duplicates
        """

        is_there_duplicates = False

        tally: dict[Path, int] = defaultdict(int)
        for source in sources:
            tally[source] += 1

        for source, count in tally.items():
            if count > 1:
                is_there_duplicates = True
                self.errors.add(error.DuplicateSource(self.subcmd, source))

        return is_there_duplicates

    def _is_valid_dest(self, dest: Path) -> bool:
        """
        Abstract method to check if the dest input to a sub-command is valid
        """
        return True

    def _is_valid_source(self, source: Path) -> bool:
        """
        Abstract method to check if the source input to a sub-command is valid
        """
        return True


class AbstractBaseSubCommand:
    """
    An abstract class to unify shared functionality in stow commands
    """

    def __init__(
        self,
        subcmd: str,
        sources: Sequence[str | Path],
        dest: str | Path,
        is_silent: bool,
        is_dry_run: bool,
        ignore_patterns: list[str] | None,
    ) -> None:
        self.subcmd = subcmd

        self.actions = actions.Actions(is_silent, is_dry_run)
        self.errors = error.Errors(is_silent)

        self.is_silent = is_silent
        self.is_dry_run = is_dry_run

        self.dest_input = pathlib.Path(dest)
        source_inputs = [pathlib.Path(source) for source in sources]

        if self._is_valid_input(source_inputs, self.dest_input):
            for source in source_inputs:
                self.ignore = ignore.Ignore(ignore_patterns, source)

                if self.ignore.should_ignore(source):
                    self.ignore.ignore(source)
                    continue

                self._collect_actions(source, self.dest_input)

        self._check_for_other_actions()
        self._execute_actions()

    def _check_for_other_actions(self) -> None:
        """
        Abstract method for examine the existing action to see if more actions
        need to be added or if some actions need to be removed.
        """

    def _is_valid_input(self, sources: Sequence[Path], dest: Path) -> bool:
        """
        Abstract method to check if the input to a sub-command is valid
        """
        return True

    def _collect_actions(self, source: Path, dest: Path) -> None:
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
