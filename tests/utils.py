"""
todo
"""

import os
import stat
import shutil


def remove_tree(tree):
    """
    todo
    """
    os.chmod(tree, 0o777)
    shutil.rmtree(tree)

def remove_file(file_name):
    """
    todo
    """
    os.chmod(file_name, 0o777)
    os.remove(file_name)

def create_file(file_name):
    """
    todo
    """
    return open(file_name, 'w').close()

def create_directory(directory_name):
    """
    todo
    """
    os.makedirs(directory_name)

class ChangeDirectory:
    # pylint: disable=too-few-public-methods
    """
    Context manager for changing the current working directory
    """
    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)
        self.saved_path = os.getcwd()

    def __enter__(self):
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)

def create_tree(tree):
    """
    todo
    """
    for branch in tree:
        if isinstance(branch, str):
            create_file(branch)

        elif isinstance(branch, dict):
            for directory, file_objs in branch.items():
                create_directory(directory)

                with ChangeDirectory(directory):
                    create_tree(file_objs)


def write_only(path):
    """
    change users permissions to a path to write only
    """
    mode = os.stat(path)[stat.ST_MODE]
    os.chmod(path, mode & ~stat.S_IRUSR & ~stat.S_IRGRP & ~stat.S_IROTH)


def read_only(path):
    """
    change users permissions to a path to read only
    """
    mode = os.stat(path)[stat.ST_MODE]
    os.chmod(path, mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)