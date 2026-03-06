"""
This module contains the actions that are combined to perform dploy's sub
commands
"""

from collections import defaultdict
from dploy import utils


class Actions:
    """
    A class that collects and executes action objects
    """

    def __init__(self, is_silent, is_dry_run):
        self.actions = []
        self.is_silent = is_silent
        self.is_dry_run = is_dry_run

    def add(self, action):
        """
        Adds an action
        """
        self.actions.append(action)

    def execute(self):
        """
        Prints and executes actions
        """
        for action in self.actions:
            if not self.is_silent:
                print(action)
            if not self.is_dry_run:
                action.execute()

    def get_unlink_actions(self):
        """
        get the current Unlink() actions from the self.actions
        """
        return [a for a in self.actions if isinstance(a, UnLink)]

    def get_unlink_target_parents(self):
        """
        Get list of the parents for the current Unlink() actions from
        self.actions
        """
        unlink_actions = self.get_unlink_actions()
        # sort for deterministic output
        return sorted({a.target.parent for a in unlink_actions})

    def get_unlink_targets(self):
        """
        Get list of the targets for the current Unlink() actions from
        self.actions
        """
        unlink_actions = self.get_unlink_actions()
        return [a.target for a in unlink_actions]

    def get_duplicates(self):
        """
        return a tuple containing tuples with the following structure
        (link destination, [indices of duplicates])
        """
        tally = defaultdict(list)
        for index, action in enumerate(self.actions):
            if isinstance(action, SymbolicLink):
                tally[action.dest].append(index)
        # sort for deterministic output
        return sorted([indices for _, indices in tally.items() if len(indices) > 1])


class AbstractBaseAction:
    """
    An abstract base class that define the interface for actions
    """

    def __init__(self):
        pass

    def execute(self):
        """
        function that executes the logic of each concrete action
        """


class SymbolicLink(AbstractBaseAction):
    """
    Action to create a symbolic link relative to the source of the link
    """

    def __init__(self, subcmd, source, dest):
        super().__init__()
        self.source = source
        self.source_relative = utils.get_relative_path(source, dest.parent)
        self.subcmd = subcmd
        self.dest = dest

    def execute(self):
        self.dest.symlink_to(self.source_relative)

    def __repr__(self):
        return f"dploy {self.subcmd}: link {self.dest} => {self.source_relative}"


class AlreadyLinked(AbstractBaseAction):
    """
    Action to used to print an already linked message
    """

    def __init__(self, subcmd, source, dest):
        super().__init__()
        self.source = source
        self.source_relative = utils.get_relative_path(source, dest.parent)
        self.dest = dest
        self.subcmd = subcmd

    def execute(self):
        pass

    def __repr__(self):
        return f"dploy {self.subcmd}: already linked {self.dest} => {self.source_relative}"


class AlreadyUnlinked(AbstractBaseAction):
    """
    Action to used to print an already unlinked message
    """

    def __init__(self, subcmd, source, dest):
        super().__init__()
        self.source = source
        self.source_relative = utils.get_relative_path(source, dest.parent)
        self.dest = dest
        self.subcmd = subcmd

    def execute(self):
        pass

    def __repr__(self):
        return f"dploy {self.subcmd}: already unlinked {self.dest} => {self.source_relative}"


class UnLink(AbstractBaseAction):
    """
    Action to unlink a symbolic link
    """

    def __init__(self, subcmd, target):
        super().__init__()
        self.target = target
        self.subcmd = subcmd

    def execute(self):
        if not self.target.is_symlink():
            raise RuntimeError(
                f"dploy detected and aborted an attempt to unlink a non-symlink {self.target} this is a bug and should be reported"
            )
        self.target.unlink()

    def __repr__(self):
        return f"dploy {self.subcmd}: unlink {self.target} => {utils.readlink(self.target)}"


class MakeDirectory(AbstractBaseAction):
    """
    Action to create a directory
    """

    def __init__(self, subcmd, target):
        super().__init__()
        self.target = target
        self.subcmd = subcmd

    def execute(self):
        self.target.mkdir()

    def __repr__(self):
        return f"dploy {self.subcmd}: make directory {self.target}"


class RemoveDirectory(AbstractBaseAction):
    """
    Action to remove a directory
    """

    def __init__(self, subcmd, target):
        super().__init__()
        self.target = target
        self.subcmd = subcmd

    def execute(self):
        self.target.rmdir()

    def __repr__(self):
        return f"dploy {self.subcmd}: remove directory {self.target}"
