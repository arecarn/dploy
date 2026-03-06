"""
Module for the --ignore IGNORE_PATTERN flag and .dploystowignore file
"""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

from dploy import utils

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Sequence


class Ignore:
    """
    Handles ignoring of files via glob patterns either passed in directly in or
    in a specified ignore file.
    """

    def __init__(self, patterns: Sequence[str] | None, source: Path) -> None:
        input_patterns = [] if patterns is None else patterns
        self.ignored_files: list[Path] = []

        file = source.parent / pathlib.Path(".dploystowignore")

        self.patterns = [str(file.name)]  # ignore the ignore file
        self.patterns.extend(input_patterns)
        self._read_ignore_file_patterns(file)

    def _read_ignore_file_patterns(self, file: Path) -> None:
        """
        read ignore patterns from a specified file
        """
        try:
            with open(str(file), encoding="utf-8") as afile:
                file_patterns = afile.read().splitlines()
                self.patterns.extend(file_patterns)
        except FileNotFoundError:
            pass

    def should_ignore(self, source: Path) -> bool:
        """
        check if a source should be ignored, based on the ignore patterns in
        self.patterns

        This checks if the ignore patterns match either the file exactly or
        its parents
        """
        for pattern in self.patterns:
            try:
                files = sorted(source.parent.glob(pattern))
            except IndexError:  # the glob result was empty
                continue

            for file in files:
                if utils.is_same_file(file, source) or source in file.parents:
                    return True
        return False

    def ignore(self, file: Path) -> None:
        """
        add a file to be ignored
        """
        self.ignored_files.append(file)

    def get_ignored_files(self) -> list[Path]:
        """
        get a list of the files that have been ignored
        """
        return self.ignored_files
