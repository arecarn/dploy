"""Version string sourced from pyproject.toml via importlib.metadata."""

from importlib.metadata import version

__version__ = version("dploy")
