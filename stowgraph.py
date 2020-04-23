from collections import defaultdict

# Nodes
# Directory
# File
# Link (directory or file?)

# Data
# - type (file,link,directory)
# - list of files below it
# - path (matching key) ?

# {
#     'path1': Data
#     'path2':

# }


class File():
    def __init__(self, file_type):
        self.type = file_type
        self.children = []


class Graph():
    def __init__(self, a_dir):
        self.graph = defaultdict(set)
        self.create(a_dir)

    def create(self, a_dir):
        for child in a_dir.iterdir():
            print(child.name)
            if child.is_symlink():
                self.graph[a_dir.name].add(child.name)
            elif child.is_dir():
                self.create(child)
            else:
                self.graph[a_dir.name].add(child.name)
