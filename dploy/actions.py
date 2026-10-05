"""
This module contains the actions that are combined to perform dploy's sub
commands
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from dploy import utils

if TYPE_CHECKING:
    from pathlib import Path


class Actions:
    """
    A class that collects and executes action objects
    """

    def __init__(self, is_silent: bool, is_dry_run: bool) -> None:
        self.actions: list[AbstractBaseAction] = []
        self.is_silent = is_silent
        self.is_dry_run = is_dry_run

    def add(self, action: AbstractBaseAction) -> None:
        """
        Adds an action
        """
        self.actions.append(action)

    def execute(self) -> None:
        """
        Prints and executes actions
        """
        for action in self.actions:
            if not self.is_silent:
                print(action)
            if not self.is_dry_run:
                action.execute()

    def get_unlink_actions(self) -> list[UnLink]:
        """
        get the current Unlink() actions from the self.actions
        """
        return [a for a in self.actions if isinstance(a, UnLink)]

    def get_unlink_path_parents(self) -> list[Path]:
        """
        Get list of the parents for the current Unlink() actions from
        self.actions
        """
        unlink_actions = self.get_unlink_actions()
        # sort for deterministic output
        return sorted({a.path.parent for a in unlink_actions})

    def get_unlink_paths(self) -> list[Path]:
        """
        Get list of the paths for the current Unlink() actions from
        self.actions
        """
        unlink_actions = self.get_unlink_actions()
        return [a.path for a in unlink_actions]

    def get_duplicates(self) -> list[list[int]]:
        """
        return a tuple containing tuples with the following structure
        (link destination, [indices of duplicates])
        """
        tally = defaultdict(list)
        for index, action in enumerate(self.actions):
            if isinstance(action, SymbolicLink):
                tally[action.path].append(index)
        # sort for deterministic output
        return sorted([indices for _, indices in tally.items() if len(indices) > 1])


class AbstractBaseAction:
    """
    An abstract base class that define the interface for actions
    """

    def __init__(self) -> None:
        pass

    def execute(self) -> None:
        """
        function that executes the logic of each concrete action
        """


class SymbolicLink(AbstractBaseAction):
    """
    Action to create a symbolic link relative to the source of the link
    """

    def __init__(self, subcmd: str, source: Path, path: Path) -> None:
        super().__init__()
        self.source = source
        self.source_relative = utils.get_relative_path(source, path.parent)
        self.subcmd = subcmd
        self.path = path

    def execute(self) -> None:
        self.path.symlink_to(self.source_relative)

    def __repr__(self) -> str:
        return f"dploy {self.subcmd}: link {self.path} => {self.source_relative}"


class AlreadyLinked(AbstractBaseAction):
    """
    Action to used to print an already linked message
    """

    def __init__(self, subcmd: str, source: Path, path: Path) -> None:
        super().__init__()
        self.source = source
        self.source_relative = utils.get_relative_path(source, path.parent)
        self.path = path
        self.subcmd = subcmd

    def execute(self) -> None:
        pass

    def __repr__(self) -> str:
        return (
            f"dploy {self.subcmd}: already linked {self.path} => {self.source_relative}"
        )


class AlreadyUnlinked(AbstractBaseAction):
    """
    Action to used to print an already unlinked message
    """

    def __init__(self, subcmd: str, source: Path, path: Path) -> None:
        super().__init__()
        self.source = source
        self.source_relative = utils.get_relative_path(source, path.parent)
        self.path = path
        self.subcmd = subcmd

    def execute(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"dploy {self.subcmd}: already unlinked {self.path} => {self.source_relative}"


class DotfilesMismatch(AbstractBaseAction):
    """
    Action used to warn that a translated dotfile link exists but --dotfiles
    was not passed to unstow, so it was left untouched
    """

    def __init__(self, subcmd: str, package: Path, dotfile_destination: Path) -> None:
        super().__init__()
        self.package = package
        self.dotfile_destination = dotfile_destination
        self.subcmd = subcmd

    def execute(self) -> None:
        pass

    def __repr__(self) -> str:
        return (
            f"dploy {self.subcmd}: warning: '{self.dotfile_destination}' looks like it "
            f"was stowed with --dotfiles; pass --dotfiles to unstow it "
            f"({self.package.name})"
        )


class UnLink(AbstractBaseAction):
    """
    Action to unlink a symbolic link
    """

    def __init__(self, subcmd: str, path: Path) -> None:
        super().__init__()
        self.path = path
        self.subcmd = subcmd

    def execute(self) -> None:
        if not self.path.is_symlink():
            raise RuntimeError(
                f"dploy detected and aborted an attempt to unlink a non-symlink {self.path} this is a bug and should be reported"
            )
        self.path.unlink()

    def __repr__(self) -> str:
        return f"dploy {self.subcmd}: unlink {self.path} => {utils.readlink(self.path)}"


class MakeDirectory(AbstractBaseAction):
    """
    Action to create a directory
    """

    def __init__(self, subcmd: str, path: Path) -> None:
        super().__init__()
        self.path = path
        self.subcmd = subcmd

    def execute(self) -> None:
        self.path.mkdir()

    def __repr__(self) -> str:
        return f"dploy {self.subcmd}: make directory {self.path}"


class RemoveDirectory(AbstractBaseAction):
    """
    Action to remove a directory
    """

    def __init__(self, subcmd: str, path: Path) -> None:
        super().__init__()
        self.path = path
        self.subcmd = subcmd

    def execute(self) -> None:
        self.path.rmdir()

    def __repr__(self) -> str:
        return f"dploy {self.subcmd}: remove directory {self.path}"
