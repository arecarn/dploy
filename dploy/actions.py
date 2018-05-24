"""
This module contains the actions that are combined to perform dploy's sub
commands
"""

from collections import defaultdict
from collections import OrderedDict
from dploy import utils


class DefaultListOrderedDict(OrderedDict):
    def __missing__(self, k):
        self[k] = []
        return self[k]


class Actions():
    """
    A class that collects and executes action objects
    """

    def __init__(self, is_silent, is_dry_run):
        self.actions = []
        self.actions_map = DefaultListOrderedDict()
        self.is_silent = is_silent
        self.is_dry_run = is_dry_run

    def add(self, action):
        """
        Adds an action
        """
        self.actions.append(action)
        self.actions_map[action.dest].append(action)

    def execute(self):
        """
        Prints and executes actions
        """
        # print(self.actions_map)
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
        return sorted(set([a.target.parent for a in unlink_actions]))

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
        return sorted(
            [indices for _, indices in tally.items() if len(indices) > 1])


class AbstractBaseAction():
    # pylint: disable=too-few-public-methods
    """
    An abstract base class that define the interface for actions
    """

    def __init__(self):
        pass

    def execute(self):
        """
        function that executes the logic of each concrete action
        """
        pass


class SymbolicLink(AbstractBaseAction):
    # pylint: disable=too-few-public-methods
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
        return "dploy {subcmd}: link {dest} => {source}".format(
            subcmd=self.subcmd, dest=self.dest, source=self.source_relative)


class AlreadyLinked(AbstractBaseAction):
    # pylint: disable=too-few-public-methods
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
        return "dploy {subcmd}: already linked {dest} => {source}".format(
            subcmd=self.subcmd, source=self.source_relative, dest=self.dest)


class AlreadyUnlinked(AbstractBaseAction):
    # pylint: disable=too-few-public-methods
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
        return "dploy {subcmd}: already unlinked {dest} => {source}".format(
            subcmd=self.subcmd, source=self.source_relative, dest=self.dest)


class UnLink(AbstractBaseAction):
    # pylint: disable=too-few-public-methods
    """
    Action to unlink a symbolic link
    """

    def __init__(self, subcmd, target):
        super().__init__()
        self.target = target
        self.dest = target
        self.subcmd = subcmd

    def execute(self):
        if not self.target.is_symlink():
            # pylint: disable=line-too-long
            raise RuntimeError(
                'dploy detected and aborted an attempt to unlink a non-symlink {target} this is a bug and should be reported'.format(target=self.target)
            )
        self.target.unlink()

    def __repr__(self):
        return "dploy {subcmd}: unlink {target} => {source}".format(
            subcmd=self.subcmd, target=self.target, source=utils.readlink(self.target))


class MakeDirectory(AbstractBaseAction):
    # pylint: disable=too-few-public-methods
    """
    Action to create a directory
    """

    def __init__(self, subcmd, target):
        super().__init__()
        self.target = target
        self.dest = target
        self.subcmd = subcmd

    def execute(self):
        self.target.mkdir()

    def __repr__(self):
        return "dploy {subcmd}: make directory {target}".format(
            target=self.target, subcmd=self.subcmd)


class RemoveDirectory(AbstractBaseAction):
    # pylint: disable=too-few-public-methods
    """
    Action to remove a directory
    """

    def __init__(self, subcmd, target):
        super().__init__()
        self.target = target
        self.dest = target
        self.subcmd = subcmd

    def execute(self):
        self.target.rmdir()

    def __repr__(self):
        msg = "dploy {subcmd}: remove directory {target}"
        return msg.format(target=self.target, subcmd=self.subcmd)
