"""
The logic and workings behind the stow and unstow sub-commands
"""

from collections import Counter
import pathlib
from dploy import actions
from dploy import utils
from dploy import error
from dploy import main
from dploy import ignore


# pylint: disable=too-few-public-methods
class AbstractBaseStow(main.AbstractBaseSubCommand):
    """
    Abstract Base class that contains the shared logic for all of the stow
    commands
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        subcmd,
        source,
        dest,
        is_silent,
        is_dry_run,
        ignore_patterns,
        dotfiles=False,
    ):
        self.is_unfolding = False
        super().__init__(
            subcmd, source, dest, is_silent, is_dry_run, ignore_patterns, dotfiles
        )

    def _is_valid_input(self, sources, dest):
        """
        Check to see if the input is valid
        """
        return StowInput(self.errors, self.subcmd).is_valid(sources, dest)

    def get_directory_contents(self, directory):
        """
        Get the contents of a directory while handling errors that may occur
        """
        contents = []

        try:
            contents = utils.get_directory_contents(directory)
        except PermissionError:
            self.errors.add(error.PermissionDenied(self.subcmd, directory))
        except FileNotFoundError:
            self.errors.add(error.NoSuchFileOrDirectory(self.subcmd, directory))
        except NotADirectoryError:
            self.errors.add(error.NoSuchDirectory(self.subcmd, directory))

        return contents

    def _are_same_file(self, source, dest):
        """
        Abstract method that handles the case when the source and dest are the
        same file when collecting actions
        """
        pass

    def _are_directories(self, source, dest):
        """
        Abstract method that handles the case when the source and dest are directories
        same file when collecting actions
        """
        pass

    def _are_other(self, source, dest):
        """
        Abstract method that handles all other cases what to do if no particular
        condition is true cases are found
        """
        pass

    def _collect_actions_existing_dest(self, source, dest):
        """
        _collect_actions() helper to collect required actions to perform a stow
        command when the destination already exists
        """
        if utils.is_same_file(dest, source):
            if dest.is_symlink() or self.is_unfolding:
                self._are_same_file(source, dest)
            else:
                self.errors.add(error.SourceIsSameAsDest(self.subcmd, dest.parent))

        elif dest.is_dir() and source.is_dir:
            self._are_directories(source, dest)
        else:
            self.errors.add(error.ConflictsWithExistingFile(self.subcmd, source, dest))

    def _collect_actions(self, source, dest):
        """
        Concrete method to collect required actions to perform a stow
        sub-command
        """

        if self.ignore.should_ignore(source):
            self.ignore.ignore(source)
            return

        if not StowInput(self.errors, self.subcmd).is_valid_collection_input(
            source, dest
        ):
            return

        sources = self.get_directory_contents(source)

        for subsources in sources:
            if self.ignore.should_ignore(subsources):
                self.ignore.ignore(subsources)
                continue

            dest_name = subsources.name
            if self.dotfiles and dest_name.startswith("dot-"):
                dest_name = dest_name.replace("dot-", ".", 1)
            dest_path = dest / pathlib.Path(dest_name)

            does_dest_path_exist = False
            try:
                does_dest_path_exist = dest_path.exists()
            except PermissionError:
                self.errors.add(error.PermissionDenied(self.subcmd, dest_path))
                return

            if does_dest_path_exist:
                self._collect_actions_existing_dest(subsources, dest_path)
            elif dest_path.is_symlink():
                self.errors.add(
                    error.ConflictsWithExistingLink(self.subcmd, subsources, dest_path)
                )
            elif not dest_path.parent.exists() and not self.is_unfolding:
                self.errors.add(error.NoSuchDirectory(self.subcmd, dest_path.parent))
            else:
                self._are_other(subsources, dest_path)


# pylint: disable=too-few-public-methods
class Stow(AbstractBaseStow):
    """
    Concrete class implementation of the stow sub-command
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        source,
        dest,
        is_silent=True,
        is_dry_run=False,
        ignore_patterns=None,
        dotfiles=False,
    ):
        super().__init__(
            "stow", source, dest, is_silent, is_dry_run, ignore_patterns, dotfiles
        )

    def _unfold(self, source, dest):
        """
        Method unfold a destination directory
        """
        self.is_unfolding = True
        self.actions.add(actions.UnLink(self.subcmd, dest))
        self.actions.add(actions.MakeDirectory(self.subcmd, dest))
        self._collect_actions(source, dest)
        self.is_unfolding = False

    def _handle_duplicate_actions(self):
        """
        check for symbolic link actions that would cause conflicting symbolic
        links to the same destination. Also check for actions that conflict but
        are candidates for unfolding instead.
        """
        has_conflicts = False
        dupes = self.actions.get_duplicates()

        if len(dupes) == 0:
            return

        for indices in dupes:
            first_action = self.actions.actions[indices[0]]
            remaining_actions = [self.actions.actions[i] for i in indices[1:]]

            if first_action.source.is_dir():
                self._unfold(first_action.source, first_action.dest)

                for action in remaining_actions:
                    self.is_unfolding = True
                    self._collect_actions(action.source, action.dest)
                    self.is_unfolding = False
            else:
                duplicate_action_sources = [
                    str(self.actions.actions[i].source) for i in indices
                ]
                self.errors.add(
                    error.ConflictsWithAnotherSource(
                        self.subcmd, duplicate_action_sources
                    )
                )
                has_conflicts = True

        if has_conflicts:
            return

        # remove duplicates
        for indices in dupes:
            for index in reversed(indices[1:]):
                del self.actions.actions[index]

        self._handle_duplicate_actions()

    def _check_for_other_actions(self):
        self._handle_duplicate_actions()

    def _are_same_file(self, source, dest):
        """
        what to do if source and dest are the same files
        """
        if self.is_unfolding:
            self.actions.add(actions.SymbolicLink(self.subcmd, source, dest))
        else:
            self.actions.add(actions.AlreadyLinked(self.subcmd, source, dest))

    def _are_directories(self, source, dest):
        if dest.is_symlink():
            self._unfold(dest.resolve(), dest)
        self._collect_actions(source, dest)

    def _are_other(self, source, dest):
        self.actions.add(actions.SymbolicLink(self.subcmd, source, dest))


# pylint: disable=too-few-public-methods
class UnStow(AbstractBaseStow):
    """
    Concrete class implementation of the unstow sub-command
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        source,
        dest,
        is_silent=True,
        is_dry_run=False,
        ignore_patterns=None,
        dotfiles=False,
    ):
        super().__init__(
            "unstow", source, dest, is_silent, is_dry_run, ignore_patterns, dotfiles
        )

    def _are_same_file(self, source, dest):
        """
        what to do if source and dest are the same files
        """
        self.actions.add(actions.UnLink(self.subcmd, dest))

    def _are_directories(self, source, dest):
        self._collect_actions(source, dest)

    def _are_other(self, source, dest):
        self.actions.add(actions.AlreadyUnlinked(self.subcmd, source, dest))

    def _check_for_other_actions(self):
        self._collect_folding_actions()

    def _collect_folding_actions(self):
        """
        find candidates for folding i.e. when a directory contains symlinks to
        files that all share the same parent directory
        """
        for parent in self.actions.get_unlink_target_parents():
            items = utils.get_directory_contents(parent)
            other_links_parents = []
            other_links = []
            source_parent = None
            is_normal_files_detected = False

            for item in items:
                if item not in self.actions.get_unlink_targets():
                    does_item_exist = False
                    try:
                        does_item_exist = item.exists()
                    except PermissionError:
                        self.errors.add(error.PermissionDenied(self.subcmd, item))
                        return

                    if does_item_exist and item.is_symlink():
                        source_parent = item.resolve().parent
                        other_links_parents.append(item.resolve().parent)
                        other_links.append(item)
                    else:
                        is_normal_files_detected = True
                        break

            if not is_normal_files_detected:
                other_links_parent_count = len(Counter(other_links_parents))

                if other_links_parent_count == 1:
                    assert source_parent is not None
                    if utils.is_same_files(
                        utils.get_directory_contents(source_parent), other_links
                    ):
                        self._fold(source_parent, parent)

                elif other_links_parent_count == 0 and not utils.is_same_file(
                    parent, self.dest_input
                ):
                    self.actions.add(actions.RemoveDirectory(self.subcmd, parent))

    def _fold(self, source, dest):
        """
        add the required actions for folding
        """
        self._collect_actions(source, dest)
        self.actions.add(actions.RemoveDirectory(self.subcmd, dest))
        self.actions.add(actions.SymbolicLink(self.subcmd, source, dest))


class StowInput(main.Input):
    """
    Input validator for the link command
    """

    def _is_valid_dest(self, dest):
        """
        Check if the test argument is valid
        """
        result = True

        if not dest.is_dir():
            self.errors.add(error.NoSuchDirectoryToSubcmdInto(self.subcmd, dest))
            result = False
        else:
            if not utils.is_directory_writable(dest):
                self.errors.add(
                    error.InsufficientPermissionsToSubcmdTo(self.subcmd, dest)
                )
                result = False

            if not utils.is_directory_readable(dest):
                self.errors.add(
                    error.InsufficientPermissionsToSubcmdTo(self.subcmd, dest)
                )
                result = False

            if not utils.is_directory_executable(dest):
                self.errors.add(
                    error.InsufficientPermissionsToSubcmdTo(self.subcmd, dest)
                )
                result = False

        return result

    def _is_valid_source(self, source):
        """
        Check if the source argument is valid
        """
        result = True

        if not source.is_dir():
            self.errors.add(error.NoSuchDirectory(self.subcmd, source))
            result = False
        else:
            if not utils.is_directory_readable(source):
                self.errors.add(
                    error.InsufficientPermissionsToSubcmdFrom(self.subcmd, source)
                )
                result = False

            if not utils.is_directory_executable(source):
                self.errors.add(
                    error.InsufficientPermissionsToSubcmdFrom(self.subcmd, source)
                )
                result = False

        return result

    def is_valid_collection_input(self, source, dest):
        """
        Helper to validate the source and dest parameters passed to
        _collect_actions()
        """
        result = True
        if not self._is_valid_source(source):
            result = False

        if dest.exists():
            if not self._is_valid_dest(dest):
                result = False
        return result


# pylint: disable=too-few-public-methods
class Clean(main.AbstractBaseSubCommand):
    """
    Abstract Base class that contains the shared logic for all of the stow
    commands
    """

    # pylint: disable=too-many-arguments
    def __init__(self, source, dest, is_silent, is_dry_run, ignore_patterns):
        self.source = [pathlib.Path(s) for s in source]
        self.dest = pathlib.Path(dest)
        self.ignore_patterns = ignore_patterns
        super().__init__(
            "clean",
            source,
            dest,
            is_silent,
            is_dry_run,
            ignore_patterns,
            dotfiles=False,
        )

    def _is_valid_input(self, sources, dest):
        """
        Check to see if the input is valid
        """
        return StowInput(self.errors, self.subcmd).is_valid(sources, dest)

    def get_directory_contents(self, directory):
        """
        Get the contents of a directory while handling errors that may occur
        """
        contents = []

        try:
            contents = utils.get_directory_contents(directory)
        except PermissionError:
            self.errors.add(error.PermissionDenied(self.subcmd, directory))
        except FileNotFoundError:
            self.errors.add(error.NoSuchFileOrDirectory(self.subcmd, directory))
        except NotADirectoryError:
            self.errors.add(error.NoSuchDirectory(self.subcmd, directory))

        return contents

    def _collect_clean_actions(self, source, source_names, dest):
        subdests = utils.get_directory_contents(dest)
        for subdest in subdests:
            if subdest.is_symlink():
                link_target = utils.readlink(subdest, absolute_target=True)
                if not link_target.exists() and not source_names.isdisjoint(
                    set(link_target.parents)
                ):
                    self.actions.add(actions.UnLink(self.subcmd, subdest))
            elif subdest.is_dir():
                self._collect_clean_actions(source, source_names, subdest)

    def _check_for_other_actions(self):
        """
        Concrete method to collect required actions to perform a stow
        sub-command
        """
        valid_files = []
        for a_file in self.source:
            self.ignore = ignore.Ignore(self.ignore_patterns, a_file)
            if self.ignore.should_ignore(a_file):
                self.ignore.ignore(a_file)
                continue
            else:
                valid_files.append(a_file)

            if not StowInput(self.errors, self.subcmd).is_valid_collection_input(
                a_file, self.dest
            ):
                return

        # NOTE: an option to make clean more aggressive is to change f.name to
        # f.parent this could a be a good --option
        files_names = [utils.get_absolute_path(f.name) for f in valid_files]
        files_names_set = set(files_names)
        self._collect_clean_actions(valid_files, files_names_set, self.dest)
