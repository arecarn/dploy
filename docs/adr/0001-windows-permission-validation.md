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

- The Windows permission code is about 100 lines of `ctypes` that only
  `windows-latest` CI exercises. Wrong struct layouts fail there, not on
  Linux. Tests in `tests/test_utils.py` deny access with real ACL entries
  through `icacls`.
- The check is a point-in-time answer. A permission changed between the two
  passes can still fail execution, on every platform.
- Traverse (`is_directory_executable`) will nearly always pass on Windows, as
  users hold the "bypass traverse checking" privilege that `AccessCheck`
  does not model. The OS bypasses the same check, so the answer matches the
  operation.
- The permission tests run on Windows. Their `remove_*_permission` helpers set
  a deny entry with `icacls` there, and teardown clears them first. Three
  tests stay skipped because they need the OS itself to refuse traversal,
  which the bypass above prevents (`skip_on_windows_traverse_bypass`).
