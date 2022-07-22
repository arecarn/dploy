# Change Log

The format of this change log is based on [Keep a Changelog](http://keepachangelog.com/)

All changes documented here should be written with the goal give the end-user
(not other developers) a summarized view of the changes since the last release,
organized by order of importance.

## [Unreleased] - YYYY-MM-DD

### Added

### Changed

### Fixed

### Removed

## [0.1.3] - 2022-07-22

### Added

- Added a `dploy clean` subcommand.

### Changed

- Switch to Poetry for packaging instead of setuptools.
- Require at least python >= 3.7.2.
- Use black for auto formatting instead of yapf.
- Use custom *DployError* exceptions.

### Fixed

- Print syntax help if no valid subcommand was provided.
- Fixed pytest.

## [0.1.2] - 2017-10-26

### Changed

- Renamed the CLI --quiet option to --silent because it better reflects the
  effect of the option

### Fixed

- Fix bug causing unstow to delete dest directory when unfolding.
  When unstowing and nearly all actions have been collected additional checking
  to find candidates for folding i.e. when a directory contains symlinks to
  files that all share the same parent directory. It just so happens that the
  dest directory passed into unstow could also meet this same criteria and would
  be deleted in error.

- Produce a helpful error when stowing or unstowing with duplicate sources.
  Before stow would fail, when conflicts were found, and unstow would succeed in
  unstowing a duplicate source the first time, but fail after trying to unstow
  nothing. By catching the bug before hand the error message is much clearer.

- Fix bug stowing or linking paths that cannot be relative to each other and
  caused a silent failure.
  e.g. with windows paths: `dploy stow C:\some\path D:\other\Path`
  Since the symbolic links can't use a relative path fallback to the absolute
  version of the path passed in.

### Removed

## [0.1.1] - 2016-12-29

### Fix

- Added a MANIFEST.in to fix installation via PyPi

## [0.1.0] - 2016-12-29

### Changed

- Added Dates to Change log releases

### Fixed

- Fixed change log formatting
- Fix PyPi Package so it can be installed

## [0.0.5] - 2016-12-28

### Added

- Added --ignore argument to stow and unstow commands, to specify patterns file
  to ignore.
- Added reading of .dploystowignore files in the directories of sources for
  ignore patterns that are additional to those specified via --ignore
- Added optional is_silent & is_dry_run arguments to dploy.stow() dploy.unstow()
  and dploy.link(), This is analogous to the --dry-run and --quiet command line
  arguments. These function arguments default to is_silent=True and
  is_dry_run=False.
- Added redundant check to make sure dploy never deletes anything other than a
  symbolic link
- Check for source and dest new consideration was taken for sources
  and dests directories that have invalid execute permissions.

### Changed

- Check for additional issues with sub commands that are similar to the initial
  checks done on the input of stow and unstow
- Prevent redundant errors when the src or dest are not directories
- Clarify some error messages
- Display the user inputted source and dest paths instead of absolute paths in
  the output
- Clarify error messages for file and symbolic link conflicts
- Make the output of dploy stow and unstow deterministic across file systems
- Changed the output of failing dploy sub commands so they print as many
  detected issues as possible before aborting
- Print all conflicts while stowing instead of just the first conflict, and
  print what exactly the conflict is

### Fixed

- Fixed issue when unstowing where some stowed packages directories created
  during the stowing process via unfolding would not be deleted.
- Fix issue unstowing a folded dir with a stray link
  - This fixed the following scenario: Given a dest directory with stowed
    packages that share a folded directory, that also contains a stray link
    along with the links created by stowing. When the stowed packages are
    unstowed Then the folded directory was re-folded using the parent
    directory of the single stray link and possibly linking new files that
    were never intended to be linked there. When what was desired was the
    directory to just remain with the single stray symlink.
- Fix an improperly handled expetion that occurred when unstowing a package that
  had it's destination directories execute permission unset.

## [0.0.4] - 2016-09-13

### Added

- Add folding of the remaining links that would be around after calling unstow
- Add Checks for conflicts between multiple sources for stow
- Add checking to see if args are directories for stow and unstow
- Add check the permissions for source and dest before running a command
- Add error handling for source permissions errors for stow and unstow
- CLI: Add a --dry-run flag to show what would be done
- CLI: Add a --quiet option to suppress normal output
- CLI: Add handling for canceling the program with CTRL-C
- CLI: Add a message for case when a source is already unlinked

### Changed

- Relicense under MIT
- Make dploy module usage silent
- Clarify message when a source argument is the same the dest argument
- Have the dploy module throw exceptions that the CLI module would handle
  instead of just printing to stdout

### Fixed

- CLI: Fix link to take only take one source
- Fix link source arg so it takes a string not a list
- Fix console output to print the correct command name e.g. stow, link, and
  unstow
- Fix issue where files could be deleted during unstow folding
- Fix bug that would cause an unexpected and unhanded exception when there was
  link in the destination directory that pointed to a non existing location in
  the source.
- Fix issue in stow and unstow where source and dest could be the same. This
  issue made it possible to delete files when unstow had the same
  parameters for both source and dest. It also didn't make sense to try to stow
  a directory into itself, since there will always be conflicts.

## [0.0.3] - 2016-04-11

### Added

- Adds support for python 3.3
- Add an unstow command to undo stowing

### Changed

- Stow command is run in two passes and check for conflicts first before making
  any changes

- General bug fixes and improvements.
