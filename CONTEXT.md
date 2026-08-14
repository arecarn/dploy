# dploy

dploy creates and removes symbolic links so that the contents of one directory
appear inside another, in the manner of GNU Stow, on Windows, Linux, and macOS.

## Language

### What gets linked

**Package**:
A directory whose contents are linked into a destination as a unit. Packages are
always named explicitly on the command line; dploy has no directory it searches
for them.
_Avoid_: source, source directory, stow package

**Destination**:
The directory a package's contents are linked into.
_Avoid_: target, target directory, dest

**Target**:
The path a symbolic link points at. A link's target is what it refers to, never
where it lives.
_Avoid_: referent, linked-to path

**Dangling link**:
A symbolic link whose target no longer exists.
_Avoid_: broken link, orphaned link, stale link

### Operations

**Stow**:
Linking the contents of a package into a destination. Stowing is idempotent:
stowing an already-stowed package reports the links as already in place.
_Avoid_: install, deploy, apply

**Unstow**:
Removing the links a stow produced. Also idempotent.
_Avoid_: uninstall, remove, undeploy

**Clean**:
Removing dangling links in a destination that point into a given package. Unlike
unstow, it acts on links whose targets are already gone.
_Avoid_: prune, sweep, garbage collect

**Link**:
Creating a single symbolic link at an exact path, rather than linking a whole
package's contents. Where the distinction matters, say "the link command" for
the operation and "a symbolic link" for the thing.
_Avoid_: symlink (as the name of the operation)

**Folding**:
Replacing a destination directory whose links all point into one package
directory with a single link to that directory.
_Avoid_: collapsing, compacting

**Unfolding**:
Replacing a link to a directory with a real directory containing links to that
directory's contents, so a second package can contribute entries alongside the
first.
_Avoid_: expanding, exploding

### How work is described

**Action**:
A single filesystem change dploy intends to make: creating a link, removing a
link, creating a directory, removing a directory. Actions are collected and
validated as a set before any of them run, so a command either applies fully or
not at all.
_Avoid_: operation, step, task, change

**Conflict**:
A reason a collected set of actions cannot be applied, such as a destination
entry that is not a link dploy created, or two packages claiming the same
destination path. Conflicts are reported together and abort the command before
any action runs.
_Avoid_: error, clash, collision

**Ignore pattern**:
A glob that excludes matching entries of a package from being linked. Patterns
come from the command line or from a `.dploystowignore` file beside the package.
_Avoid_: exclude pattern, skip pattern, filter
