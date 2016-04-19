import sys
import pathlib
import dploy.command
import dploy.util
from collections import defaultdict

class AbstractBaseStow():
    """
    An abstract class to unify shared functionality in stow commands
    """

    def __init__(self, sources, dest):
        self.commands = []
        self.abort = False

        for source in sources:
            source_input = pathlib.Path(source)
            dest_input = pathlib.Path(dest)
            source_absolute = dploy.util.get_absolute_path(source_input)
            dest_absolute = dploy.util.get_absolute_path(dest_input)

            self.validate_input(source_input, dest_input)
            assert source_absolute.is_dir()
            assert source_absolute.is_absolute()
            assert dest_absolute.is_absolute()
            self.collect_commands(source_absolute, dest_absolute)

        self.check_for_conflicting_commands()
        self.execute_commands()

    def validate_input(self, source, dest):
        if not source.exists():
            print(self.invalid_source_message.format(file=source))
            sys.exit(1)

        if not dest.exists():
            print(self.invalid_dest_message.format(file=dest))
            sys.exit(1)

    def collect_commands(self, source, dest):
        """
        todo
        """
        pass

    def list_duplicates(self):
        tally = defaultdict(list)
        for i, item in enumerate(self.commands):
            if (isinstance(item, dploy.command.SymbolicLink)):
                tally[item.dest].append(i)
        return ((key,locs) for key,locs in tally.items()
                                if len(locs)>1)

    def check_for_conflicting_commands(self):
        """
        check for symbolic link commands that would cause conflicting symbolic
        links to the same destination.
        """
        dupes = []
        for dup in self.list_duplicates():
            dupes.append(dup)

        if len(dupes) == 0:
            return

        for dest, indicies in dupes:
            first_index = indicies[0]
            if self.commands[first_index].source.is_dir():
                self.unfold(self.commands[first_index].source, self.commands[first_index].dest)
                for index in indicies[1:]:
                    self.collect_commands(self.commands[index].source, self.commands[index].dest, is_unfolding=True)
            else:
                msg = "dploy stow: can not stow '{source}': Conflicts with another source"
                print(msg.format(source=self.commands[first_index].source))
                self.abort = True
                return

        for dest, indicies in dupes:
            for index in reversed(indicies[1:]):
                del(self.commands[index])

        self.check_for_conflicting_commands()



    def execute_commands(self):
        """
        todo
        """
        if self.abort:
            sys.exit(1)
        else:
            for cmd in self.commands:
                cmd.execute()


class UnStow(AbstractBaseStow):
    """
    todo
    """
    def __init__(self, source, dest):
        self.invalid_source_message =  "dploy stow: can not unstow from '{file}': No such directory"
        self.invalid_dest_message =   "dploy stow: can not unstow '{file}': No such directory"
        super().__init__(source, dest)

    def collect_commands(self, source, dest):
        """
        todo
        """

        sources = dploy.util.get_directory_contents(source)

        for source in sources:
            dest_path = dest / pathlib.Path(source.name)

            if dest_path.exists():
                if dploy.util.is_same_file(dest_path, source):
                    self.commands.append(
                        dploy.command.UnLink(dest_path))

                elif dest_path.is_dir() and source.is_dir:
                    if not dest_path.is_symlink():
                        self.collect_commands(source, dest_path)
                else:
                    msg = "dploy stow: can not unstow '{file}': Conflicts with existing file"
                    print(msg.format(file=dest_path))

            elif dest_path.is_symlink():
                    # TODO add test for this
                    msg = "dploy stow: can not unstow '{file}': Conflicts with a broken link"
                    print(msg.format(file=dest_path))

            elif not dest_path.parent.exists():
                pass
                msg = "dploy stow: can not unstow '{dest}': No such directory"
                print(msg.format(dest=dest_path.parent))
            else:
                pass


class Stow(AbstractBaseStow):
    """
    todo
    """
    def __init__(self, source, dest):
        self.invalid_source_message =  "dploy stow: can not stow '{file}': No such directory"
        self.invalid_dest_message =  "dploy stow: can not stow into '{file}': No such directory"
        super().__init__(source, dest)

    def unfold(self, source, dest):
        """
        todo
        """
        self.commands.append(dploy.command.UnLink(dest))
        self.commands.append(dploy.command.MakeDirectory(dest))
        self.collect_commands(source, dest, is_unfolding=True)

    def collect_commands(self, source, dest, is_unfolding=False):
        """
        todo
        """

        sources = dploy.util.get_directory_contents(source)

        for source in sources:
            dest_path = dest / pathlib.Path(source.name)
            if dest_path.exists():
                if dploy.util.is_same_file(dest_path, source):

                    if is_unfolding:
                        self.commands.append(
                            dploy.command.SymbolicLink(source, dest_path))
                    else:
                        self.commands.append(
                            dploy.command.SymbolicLinkExists(source,
                                                             dest_path))
                elif dest_path.is_dir() and source.is_dir:
                    if dest_path.is_symlink():
                        self.unfold(dest_path.resolve(), dest_path)
                    self.collect_commands(source, dest_path)
                else:
                    msg = "dploy stow: can not stow '{file}': Conflicts with existing file"
                    print(msg.format(file=dest_path))
                    self.abort = True

            elif dest_path.is_symlink():
                    # TODO add test for this
                    msg = "dploy stow: can not stow '{file}': Conflicts with a broken link"
                    print(msg.format(file=dest_path))
                    self.abort = True

            elif not dest_path.parent.exists() and not is_unfolding:
                msg = "dploy stow: can not stow into '{dest}': No such directory"
                print(msg.format(dest=dest_path.parent))
                self.abort = True

            else:
                self.commands.append(
                    dploy.command.SymbolicLink(source, dest_path))
