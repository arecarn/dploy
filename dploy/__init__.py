"""
dploy script is an attempt at creating a clone of GNU stow that will work on
Windows as well as *nix
"""

from dploy import linkcmd
from dploy import stowcmd


def stow(sources, dest, is_silent=True, is_dry_run=False, ignore_patterns=None):
    """
    sub command stow
    """
    stowcmd.Stow(sources, dest, is_silent, is_dry_run, ignore_patterns)


def unstow(sources, dest, is_silent=True, is_dry_run=False, ignore_patterns=None):
    """
    sub command unstow
    """
    stowcmd.UnStow(sources, dest, is_silent, is_dry_run, ignore_patterns)


def clean(sources, dest, is_silent=True, is_dry_run=False, ignore_patterns=None):
    """
    sub command clean
    """
    stowcmd.Clean(sources, dest, is_silent, is_dry_run, ignore_patterns)


def link(source, dest, is_silent=True, is_dry_run=False, ignore_patterns=None):
    """
    sub command link
    """
    linkcmd.Link(source, dest, is_silent, is_dry_run, ignore_patterns)
