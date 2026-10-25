# Validate permissions on Windows with an ACL check, not os.access

Status: accepted (issue #28)

## Context

dploy runs in two passes. The collect pass validates the whole command and the
execute pass applies it, so a command either completes or changes nothing. The
README states this as a reason to use dploy over GNU Stow.

The collect pass checks permissions with `os.access`. On Windows that call only
reflects the read-only attribute and ignores ACLs, so a directory the user
cannot read passes validation and raises `PermissionError` during execution,
after actions have started applying.

The guarantee is cross-platform. A check that cannot be made honest on one
platform narrows the guarantee there instead of being quietly excepted.

## Decision

On Windows the five permission helpers in `dploy/utils.py` ask the OS the
question it asks when a path is opened: Win32 `AccessCheck` over the path's
security descriptor, using the current user's token. POSIX keeps `os.access`.

The Win32 calls are made through `ctypes` in `dploy/_winaccess.py`, so dploy
keeps no runtime dependencies.

## Options considered

- **ACL check via `pywin32`.** Rejected: `pywin32` does not expose
  `AccessCheck`. Its `GetEffectiveRightsFromAcl` ignores privileges and
  logon-session groups, and fails on an ACL with an inherited deny entry, which
  is the common case.
- **Try the operation and handle the failure.** Rejected: the collect pass
  exists so that nothing is touched before the command is known to succeed.
- **Probe with a cheap reversible access attempt.** Rejected: it makes the
  collect pass write to the filesystem, and still races with the execute pass.
- **Accept and document the gap.** Rejected: it makes the atomicity claim
  conditional on the platform.

## Consequences

- The Windows permission code is one `ctypes` module that only `windows-latest`
  CI exercises. Wrong struct layouts fail there, not on Linux. Tests in
  `tests/test_utils.py` deny access with real ACL entries through `icacls`.
- The check is a point-in-time answer. A permission changed between the two
  passes can still fail execution, on every platform.
- A path that cannot be examined (missing, bad name, no ACL support) counts as
  not accessible, as with `os.access`. Failures of the token or `AccessCheck`
  calls raise `OSError`, because the answer is then unknown rather than "no".
- A writable directory needs both the add-file and the add-subdirectory right,
  because stow creates files, directories and directory links. Removing an
  entry is not checked: it depends on `DELETE` on the entry itself, which the
  parent's ACL does not show.
- The execute (traverse) check is stricter than the OS. Users hold the
  "bypass traverse checking" privilege, which `AccessCheck` does not model, so
  the OS reaches through a directory whose traverse right is denied. dploy
  refuses it instead, because the ACL says no. A refusal in the collect pass
  never breaks the all-or-nothing promise; only a failure in the execute pass
  would.
- `AccessCheck` ignores privileges such as backup and restore, so an elevated
  user can be refused where the OS would allow the open. This is the same kind
  of stricter answer.
- The permission tests run on Windows. Their `remove_*_permission` helpers set
  a deny entry with `icacls` there, and teardown clears them first. Three
  tests stay skipped because they need the OS itself to refuse traversal,
  which the bypass above prevents (`skip_on_windows_traverse_bypass`).
- Each check opens and duplicates a process token. This is not cached because
  the cost is small next to the file system calls; cache it if profiling says
  otherwise.
