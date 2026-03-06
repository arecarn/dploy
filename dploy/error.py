"""
All the exceptions and their messages used by the program
"""

import sys

ERROR_HEAD = "dploy {subcmd}: can not {subcmd} "


class Errors:
    """
    A class that collects and executes action objects
    """

    def __init__(self, is_silent) -> None:
        self.exceptions = []
        self.is_silent = is_silent

    def add(self, error) -> None:
        """
        Adds an error
        """
        self.exceptions.append(error)

    def handle(self) -> None:
        """
        Prints and handles errors
        """
        if len(self.exceptions) > 0:
            if not self.is_silent:
                for exception in self.exceptions:
                    print(exception, file=sys.stderr)
            raise self.exceptions[0]


class DployError(Exception):
    pass


class SourceIsSameAsDest(DployError):
    def __init__(self, subcmd, file) -> None:
        self.msg = (
            ERROR_HEAD + "'{file}': A source argument is the same as the dest argument"
        )
        self.msg = self.msg.format(subcmd=subcmd, file=file)
        # self.exception = ValueError(self.msg)

    def __str__(self) -> str:
        return self.msg


class ConflictsWithAnotherSource(DployError):
    def __init__(self, subcmd, files) -> None:
        self.msg = ERROR_HEAD + "the following: Conflicts with other source {files}"
        files_list = "\n    " + "\n    ".join(files)
        self.msg = self.msg.format(subcmd=subcmd, files=files_list)
        # self.exception = ValueError(self.msg)

    def __str__(self) -> str:
        return self.msg


class ConflictsWithExistingFile(DployError):
    def __init__(self, subcmd, source, dest) -> None:
        self.msg = ERROR_HEAD + "'{source}': Conflicts with existing file '{dest}'"
        self.msg = self.msg.format(subcmd=subcmd, source=source, dest=dest)
        # self.exception = ValueError(self.msg)

    def __str__(self) -> str:
        return self.msg


class ConflictsWithExistingLink(DployError):
    def __init__(self, subcmd, source, dest) -> None:
        self.msg = ERROR_HEAD + "'{source}': Conflicts with existing symlink '{dest}'"
        self.msg = self.msg.format(subcmd=subcmd, source=source, dest=dest)
        # self.exception = ValueError(self.msg)

    def __str__(self) -> str:
        return self.msg


class InsufficientPermissions(DployError):
    def __init__(self, subcmd, file) -> None:
        self.msg = ERROR_HEAD + "'{file}': Insufficient permissions"
        self.msg = self.msg.format(subcmd=subcmd, file=file)
        # self.exception = PermissionError(self.msg)

    def __str__(self) -> str:
        return self.msg


class NoSuchDirectory(DployError):
    def __init__(self, subcmd, file) -> None:
        self.msg = ERROR_HEAD + "'{file}': No such directory"
        self.msg = self.msg.format(subcmd=subcmd, file=file)
        # self.exception = NotADirectoryError(self.msg)

    def __str__(self) -> str:
        return self.msg


class PermissionDenied(DployError):
    def __init__(self, subcmd, file) -> None:
        self.msg = ERROR_HEAD + "'{file}': Permission denied"
        self.msg = self.msg.format(subcmd=subcmd, file=file)
        # self.exception = PermissionError(self.msg)

    def __str__(self) -> str:
        return self.msg


class InsufficientPermissionsToSubcmdFrom(DployError):
    def __init__(self, subcmd, file) -> None:
        self.msg = ERROR_HEAD + "from '{file}': Insufficient permissions"
        self.msg = self.msg.format(subcmd=subcmd, file=file)
        # self.exception = PermissionError(self.msg)

    def __str__(self) -> str:
        return self.msg


class NoSuchDirectoryToSubcmdInto(DployError):
    def __init__(self, subcmd, file) -> None:
        self.msg = ERROR_HEAD + "into '{file}': No such directory"
        self.msg = self.msg.format(subcmd=subcmd, file=file)
        # self.exception = NotADirectoryError(self.msg)

    def __str__(self) -> str:
        return self.msg


class InsufficientPermissionsToSubcmdTo(DployError):
    def __init__(self, subcmd, file) -> None:
        self.msg = ERROR_HEAD + "to '{file}': Insufficient permissions"
        self.msg = self.msg.format(subcmd=subcmd, file=file)
        # self.exception = PermissionError(self.msg)

    def __str__(self) -> str:
        return self.msg


class NoSuchFileOrDirectory(DployError):
    def __init__(self, subcmd, file) -> None:
        self.msg = ERROR_HEAD + "'{file}': No such file or directory"
        self.msg = self.msg.format(subcmd=subcmd, file=file)
        # self.exception = FileNotFoundError(self.msg)

    def __str__(self) -> str:
        return self.msg


class DuplicateSource(DployError):
    def __init__(self, subcmd, file) -> None:
        self.msg = ERROR_HEAD + "'{file}': Duplicate source argument"
        self.msg = self.msg.format(subcmd=subcmd, file=file)
        # self.exception = ValueError(self.msg)

    def __str__(self) -> str:
        return self.msg
