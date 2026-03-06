#!/usr/bin/env python3
"""
The entry point when dploy is called as a module
"""

from dploy import cli


def main():
    """
    main entry point when using dploy from the command line
    """
    cli.run()


if __name__ == "__main__":
    main()
