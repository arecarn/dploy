"""
The logic and workings behind the stow and unstow sub-commands
"""

from __future__ import annotations

import pathlib
from collections import Counter
from typing import TYPE_CHECKING

from dploy import actions, error, ignore, main, utils

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


class AbstractBaseStow(main.AbstractBaseSubCommand):
    """
    Abstract Base class that contains the shared logic for all of the stow
    commands
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
        self.is_unfolding = False
        super().__init__(
            subcmd, packages, destination, is_silent, is_dry_run, ignore_patterns
        )

    def _is_valid_input(self, packages: Sequence[Path], destination: Path) -> bool:
        """
        Check to see if the input is valid
        """
        return StowInput(self.errors, self.subcmd).is_valid(packages, destination)

    def get_directory_contents(self, directory: Path) -> list[Path]:
        """
        Get the contents of a directory while handling errors that may occur
        """
        contents: list[Path] = []

        try:
            contents = utils.get_directory_contents(directory)
        except PermissionError:
            self.errors.add(error.PermissionDenied(self.subcmd, directory))
        except FileNotFoundError:
            self.errors.add(error.NoSuchFileOrDirectory(self.subcmd, directory))
        except NotADirectoryError:
            self.errors.add(error.NoSuchDirectory(self.subcmd, directory))

        return contents

    def _are_same_file(self, package: Path, destination: Path) -> None:
        """
        Abstract method that handles the case when the package and destination
        are the same file when collecting actions
        """

    def _are_directories(self, package: Path, destination: Path) -> None:
        """
        Abstract method that handles the case when the package and destination
        are directories when collecting actions
        """

    def _are_other(self, package: Path, destination: Path) -> None:
        """
        Abstract method that handles all other cases what to do if no particular
        condition is true cases are found
        """

    def _collect_actions_existing_dest(self, package: Path, destination: Path) -> None:
        """
        _collect_actions() helper to collect required actions to perform a stow
        command when the destination already exists
        """
        if utils.is_same_file(destination, package):
            if destination.is_symlink() or self.is_unfolding:
                self._are_same_file(package, destination)
            else:
                self.errors.add(
                    error.SourceIsSameAsDest(self.subcmd, destination.parent)
                )

        elif destination.is_dir() and package.is_dir():
            self._are_directories(package, destination)
        else:
            self.errors.add(
                error.ConflictsWithExistingFile(self.subcmd, package, destination)
            )

    def _collect_actions(self, package: Path, destination: Path) -> None:
        """
        Concrete method to collect required actions to perform a stow
        sub-command
        """

        if self.ignore.should_ignore(package):
            self.ignore.ignore(package)
            return

        if not StowInput(self.errors, self.subcmd).is_valid_collection_input(
            package, destination
        ):
            return

        package_contents = self.get_directory_contents(package)

        for entry in package_contents:
            if self.ignore.should_ignore(entry):
                self.ignore.ignore(entry)
                continue

            destination_path = destination / pathlib.Path(entry.name)

            does_destination_path_exist = False
            try:
                does_destination_path_exist = destination_path.exists()
            except PermissionError:
                self.errors.add(error.PermissionDenied(self.subcmd, destination_path))
                return

            if does_destination_path_exist:
                self._collect_actions_existing_dest(entry, destination_path)
            elif destination_path.is_symlink():
                self.errors.add(
                    error.ConflictsWithExistingLink(
                        self.subcmd, entry, destination_path
                    )
                )
            elif not destination_path.parent.exists() and not self.is_unfolding:
                self.errors.add(
                    error.NoSuchDirectory(self.subcmd, destination_path.parent)
                )
            else:
                self._are_other(entry, destination_path)


class Stow(AbstractBaseStow):
    """
    Concrete class implementation of the stow sub-command
    """

    def __init__(
        self,
        packages: Sequence[str | Path],
        destination: str | Path,
        is_silent: bool = True,
        is_dry_run: bool = False,
        ignore_patterns: list[str] | None = None,
    ) -> None:
        super().__init__(
            "stow", packages, destination, is_silent, is_dry_run, ignore_patterns
        )

    def _unfold(self, package: Path, destination: Path) -> None:
        """
        Method unfold a destination directory
        """
        self.is_unfolding = True
        self.actions.add(actions.UnLink(self.subcmd, destination))
        self.actions.add(actions.MakeDirectory(self.subcmd, destination))
        self._collect_actions(package, destination)
        self.is_unfolding = False

    def _handle_duplicate_actions(self) -> None:
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

            if isinstance(first_action, actions.SymbolicLink):
                if first_action.source.is_dir():
                    self._unfold(first_action.source, first_action.path)

                    for action in remaining_actions:
                        if isinstance(action, actions.SymbolicLink):
                            self.is_unfolding = True
                            self._collect_actions(action.source, action.path)
                            self.is_unfolding = False
                else:
                    duplicate_action_sources = []
                    for i in indices:
                        action = self.actions.actions[i]
                        if isinstance(action, actions.SymbolicLink):
                            duplicate_action_sources.append(str(action.source))

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

    def _check_for_other_actions(self) -> None:
        self._handle_duplicate_actions()

    def _are_same_file(self, package: Path, destination: Path) -> None:
        """
        what to do if package and destination are the same files
        """
        if self.is_unfolding:
            self.actions.add(actions.SymbolicLink(self.subcmd, package, destination))
        else:
            self.actions.add(actions.AlreadyLinked(self.subcmd, package, destination))

    def _are_directories(self, package: Path, destination: Path) -> None:
        if self._needs_unfolding(destination):
            self._unfold(destination.resolve(), destination)
        self._collect_actions(package, destination)

    def _needs_unfolding(self, destination: Path) -> bool:
        """
        Check whether any path component between self.destination_input and
        destination is itself a symlink, meaning destination is only reached
        by traversing into another package's folded subtree (not just
        whether destination itself is a symlink). A shared directory two or
        more levels deep is missed by a leaf-only symlink check, because
        only the top of the folded subtree is a literal symlink on disk.
        """
        current = self.destination_input
        for part in destination.relative_to(self.destination_input).parts:
            current = current / part
            if current.is_symlink():
                return True
        return False

    def _are_other(self, package: Path, destination: Path) -> None:
        self.actions.add(actions.SymbolicLink(self.subcmd, package, destination))


class UnStow(AbstractBaseStow):
    """
    Concrete class implementation of the unstow sub-command
    """

    def __init__(
        self,
        packages: Sequence[str | Path],
        destination: str | Path,
        is_silent: bool = True,
        is_dry_run: bool = False,
        ignore_patterns: list[str] | None = None,
    ) -> None:
        super().__init__(
            "unstow", packages, destination, is_silent, is_dry_run, ignore_patterns
        )

    def _are_same_file(self, package: Path, destination: Path) -> None:
        """
        what to do if package and destination are the same files
        """
        self.actions.add(actions.UnLink(self.subcmd, destination))

    def _are_directories(self, package: Path, destination: Path) -> None:
        self._collect_actions(package, destination)

    def _are_other(self, package: Path, destination: Path) -> None:
        self.actions.add(actions.AlreadyUnlinked(self.subcmd, package, destination))

    def _check_for_other_actions(self) -> None:
        self._collect_folding_actions()

    def _collect_folding_actions(self) -> None:
        """
        find candidates for folding i.e. when a directory contains symlinks to
        files that all share the same parent directory
        """
        for parent in self.actions.get_unlink_path_parents():
            items = utils.get_directory_contents(parent)
            other_links_parents: list[Path] = []
            other_links: list[Path] = []
            package_parent: Path | None = None
            is_normal_files_detected = False

            for item in items:
                if item not in self.actions.get_unlink_paths():
                    does_item_exist = False
                    try:
                        does_item_exist = item.exists()
                    except PermissionError:
                        self.errors.add(error.PermissionDenied(self.subcmd, item))
                        return

                    if does_item_exist and item.is_symlink():
                        resolved_parent = item.resolve().parent
                        package_parent = resolved_parent
                        other_links_parents.append(resolved_parent)
                        other_links.append(item)
                    else:
                        is_normal_files_detected = True
                        break

            if not is_normal_files_detected:
                other_links_parent_count = len(Counter(other_links_parents))

                if other_links_parent_count == 1:
                    assert package_parent is not None
                    if utils.is_same_files(
                        utils.get_directory_contents(package_parent), other_links
                    ):
                        self._fold(package_parent, parent)

                elif other_links_parent_count == 0 and not utils.is_same_file(
                    parent, self.destination_input
                ):
                    self.actions.add(actions.RemoveDirectory(self.subcmd, parent))

    def _fold(self, package: Path, destination: Path) -> None:
        """
        add the required actions for folding
        """
        self._collect_actions(package, destination)
        self.actions.add(actions.RemoveDirectory(self.subcmd, destination))
        self.actions.add(actions.SymbolicLink(self.subcmd, package, destination))


class StowInput(main.Input):
    """
    Input validator for the stow command
    """

    def _is_valid_destination(self, destination: Path) -> bool:
        """
        Check if the destination argument is valid
        """
        result = True

        if not destination.is_dir():
            self.errors.add(error.NoSuchDirectoryToSubcmdInto(self.subcmd, destination))
            result = False
        else:
            if not utils.is_directory_writable(destination):
                self.errors.add(
                    error.InsufficientPermissionsToSubcmdTo(self.subcmd, destination)
                )
                result = False

            if not utils.is_directory_readable(destination):
                self.errors.add(
                    error.InsufficientPermissionsToSubcmdTo(self.subcmd, destination)
                )
                result = False

            if not utils.is_directory_executable(destination):
                self.errors.add(
                    error.InsufficientPermissionsToSubcmdTo(self.subcmd, destination)
                )
                result = False

        return result

    def _is_valid_package(self, package: Path) -> bool:
        """
        Check if the package argument is valid
        """
        result = True

        if not package.is_dir():
            self.errors.add(error.NoSuchDirectory(self.subcmd, package))
            result = False
        else:
            if not utils.is_directory_readable(package):
                self.errors.add(
                    error.InsufficientPermissionsToSubcmdFrom(self.subcmd, package)
                )
                result = False

            if not utils.is_directory_executable(package):
                self.errors.add(
                    error.InsufficientPermissionsToSubcmdFrom(self.subcmd, package)
                )
                result = False

        return result

    def is_valid_collection_input(self, package: Path, destination: Path) -> bool:
        """
        Helper to validate the package and destination parameters passed to
        _collect_actions()
        """
        result = True
        if not self._is_valid_package(package):
            result = False

        if destination.exists() and not self._is_valid_destination(destination):
            result = False
        return result


class Clean(main.AbstractBaseSubCommand):
    """
    Abstract Base class that contains the shared logic for all of the stow
    commands
    """

    def __init__(
        self,
        packages: Sequence[str | Path],
        destination: str | Path,
        is_silent: bool,
        is_dry_run: bool,
        ignore_patterns: list[str] | None,
    ) -> None:
        self.packages = [pathlib.Path(p) for p in packages]
        self.destination = pathlib.Path(destination)
        self.ignore_patterns = ignore_patterns
        super().__init__(
            "clean", packages, destination, is_silent, is_dry_run, ignore_patterns
        )

    def _is_valid_input(self, packages: Sequence[Path], destination: Path) -> bool:
        """
        Check to see if the input is valid
        """
        return StowInput(self.errors, self.subcmd).is_valid(packages, destination)

    def get_directory_contents(self, directory: Path) -> list[Path]:
        """
        Get the contents of a directory while handling errors that may occur
        """
        contents: list[Path] = []

        try:
            contents = utils.get_directory_contents(directory)
        except PermissionError:
            self.errors.add(error.PermissionDenied(self.subcmd, directory))
        except FileNotFoundError:
            self.errors.add(error.NoSuchFileOrDirectory(self.subcmd, directory))
        except NotADirectoryError:
            self.errors.add(error.NoSuchDirectory(self.subcmd, directory))

        return contents

    def _collect_clean_actions(
        self, packages: Sequence[Path], package_names: set[str], destination: Path
    ) -> None:
        subdestinations = utils.get_directory_contents(destination)
        for subdestination in subdestinations:
            if subdestination.is_symlink():
                link_target = utils.readlink(subdestination, absolute_target=True)
                if not link_target.exists() and not package_names.isdisjoint(
                    set(str(p) for p in link_target.parents)
                ):
                    self.actions.add(actions.UnLink(self.subcmd, subdestination))
            elif subdestination.is_dir():
                self._collect_clean_actions(packages, package_names, subdestination)

    def _check_for_other_actions(self) -> None:
        """
        Concrete method to collect required actions to perform a stow
        sub-command
        """
        valid_files: list[Path] = []
        for a_file in self.packages:
            self.ignore = ignore.Ignore(self.ignore_patterns, a_file)
            if self.ignore.should_ignore(a_file):
                self.ignore.ignore(a_file)
                continue

            valid_files.append(a_file)

            if not StowInput(self.errors, self.subcmd).is_valid_collection_input(
                a_file, self.destination
            ):
                return

        # NOTE: an option to make clean more aggressive is to change f.name to
        # f.parent this could a be a good --option
        files_names = [str(utils.get_absolute_path(f.name)) for f in valid_files]
        package_names_set = set(files_names)
        self._collect_clean_actions(valid_files, package_names_set, self.destination)
