"""
Windows access checks that consult the ACL, as `os.access` does not

`os.access` on Windows only reflects the read-only attribute. `has_access`
asks the OS the question Windows itself asks when a file is opened: it runs
the Win32 `AccessCheck` over the path's security descriptor with the current
user's token. See docs/adr/0001-windows-permission-validation.md.

Only import this module on Windows; it needs `ctypes.WinDLL`.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes

# Generic-to-specific right mapping for files, from winnt.h.
_FILE_GENERIC_READ = 0x120089
_FILE_GENERIC_WRITE = 0x120116
_FILE_GENERIC_EXECUTE = 0x1200A0
_FILE_ALL_ACCESS = 0x1F01FF

_OWNER_GROUP_DACL_SECURITY_INFORMATION = 0x1 | 0x2 | 0x4
_TOKEN_QUERY = 0x0008
_TOKEN_DUPLICATE = 0x0002
_SECURITY_IMPERSONATION = 2

_ERROR_FILE_NOT_FOUND = 2
_ERROR_PATH_NOT_FOUND = 3
_ERROR_ACCESS_DENIED = 5
_ERROR_INSUFFICIENT_BUFFER = 122


class _GenericMapping(ctypes.Structure):
    _fields_ = (
        ("GenericRead", wintypes.DWORD),
        ("GenericWrite", wintypes.DWORD),
        ("GenericExecute", wintypes.DWORD),
        ("GenericAll", wintypes.DWORD),
    )


class _LuidAndAttributes(ctypes.Structure):
    _fields_ = (
        ("LowPart", wintypes.DWORD),
        ("HighPart", wintypes.LONG),
        ("Attributes", wintypes.DWORD),
    )


class _PrivilegeSet(ctypes.Structure):
    _fields_ = (
        ("PrivilegeCount", wintypes.DWORD),
        ("Control", wintypes.DWORD),
        ("Privilege", _LuidAndAttributes * 1),
    )


_advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_advapi32.GetFileSecurityW.argtypes = (
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
)
_advapi32.GetFileSecurityW.restype = wintypes.BOOL
_advapi32.OpenProcessToken.argtypes = (
    wintypes.HANDLE,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.HANDLE),
)
_advapi32.OpenProcessToken.restype = wintypes.BOOL
_advapi32.DuplicateToken.argtypes = (
    wintypes.HANDLE,
    ctypes.c_int,
    ctypes.POINTER(wintypes.HANDLE),
)
_advapi32.DuplicateToken.restype = wintypes.BOOL
_advapi32.AccessCheck.argtypes = (
    ctypes.c_void_p,
    wintypes.HANDLE,
    wintypes.DWORD,
    ctypes.POINTER(_GenericMapping),
    ctypes.POINTER(_PrivilegeSet),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.BOOL),
)
_advapi32.AccessCheck.restype = wintypes.BOOL
_kernel32.GetCurrentProcess.argtypes = ()
_kernel32.GetCurrentProcess.restype = wintypes.HANDLE
_kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
_kernel32.CloseHandle.restype = wintypes.BOOL

_FILE_GENERIC_MAPPING = _GenericMapping(
    _FILE_GENERIC_READ,
    _FILE_GENERIC_WRITE,
    _FILE_GENERIC_EXECUTE,
    _FILE_ALL_ACCESS,
)


def _raise_last_error() -> None:
    raise ctypes.WinError(ctypes.get_last_error())


def _security_descriptor(path: str) -> ctypes.Array[ctypes.c_char] | None:
    """
    read the owner, group and DACL of a path; None if it cannot be read

    A missing path or one whose security descriptor is unreadable yields None,
    matching `os.access`, which answers False rather than raising for both.
    """
    needed = wintypes.DWORD(0)
    # the first call only measures: it fails with ERROR_INSUFFICIENT_BUFFER
    _advapi32.GetFileSecurityW(
        path, _OWNER_GROUP_DACL_SECURITY_INFORMATION, None, 0, ctypes.byref(needed)
    )
    error = ctypes.get_last_error()
    if error in (_ERROR_FILE_NOT_FOUND, _ERROR_PATH_NOT_FOUND, _ERROR_ACCESS_DENIED):
        return None
    if error != _ERROR_INSUFFICIENT_BUFFER:
        _raise_last_error()

    buffer = ctypes.create_string_buffer(needed.value)
    if not _advapi32.GetFileSecurityW(
        path,
        _OWNER_GROUP_DACL_SECURITY_INFORMATION,
        buffer,
        needed,
        ctypes.byref(needed),
    ):
        _raise_last_error()
    return buffer


def _impersonation_token() -> wintypes.HANDLE:
    """
    open an impersonation token for the current process; the caller closes it

    `AccessCheck` rejects a primary token, so the process token is duplicated.
    """
    primary = wintypes.HANDLE()
    if not _advapi32.OpenProcessToken(
        _kernel32.GetCurrentProcess(),
        _TOKEN_QUERY | _TOKEN_DUPLICATE,
        ctypes.byref(primary),
    ):
        _raise_last_error()
    try:
        impersonation = wintypes.HANDLE()
        if not _advapi32.DuplicateToken(
            primary, _SECURITY_IMPERSONATION, ctypes.byref(impersonation)
        ):
            _raise_last_error()
        return impersonation
    finally:
        _kernel32.CloseHandle(primary)


def has_access(path: str, rights: int) -> bool:
    """
    check whether the current user is granted every right in `rights` on a path

    `rights` is a mask of specific file rights, e.g. FILE_READ_DATA from winnt.h. Follows
    symlinks, like `os.access`. Returns False for a path that does not exist
    or whose security descriptor cannot be read. Raises OSError if the check
    itself fails, as that means the answer is unknown rather than "no".
    """
    descriptor = _security_descriptor(path)
    if descriptor is None:
        return False

    token = _impersonation_token()
    try:
        privileges = _PrivilegeSet()
        privileges_length = wintypes.DWORD(ctypes.sizeof(privileges))
        granted = wintypes.DWORD(0)
        allowed = wintypes.BOOL(False)
        if not _advapi32.AccessCheck(
            descriptor,
            token,
            rights,
            ctypes.byref(_FILE_GENERIC_MAPPING),
            ctypes.byref(privileges),
            ctypes.byref(privileges_length),
            ctypes.byref(granted),
            ctypes.byref(allowed),
        ):
            _raise_last_error()
        return bool(allowed.value)
    finally:
        _kernel32.CloseHandle(token)
