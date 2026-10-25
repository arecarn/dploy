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

# How AccessCheck expands generic rights into file rights (winnt.h). Only the
# desired rights passed to has_access matter to dploy, but AccessCheck requires
# a full mapping: the last value is what GENERIC_ALL becomes.
_FILE_GENERIC_READ = 0x120089
_FILE_GENERIC_WRITE = 0x120116
_FILE_GENERIC_EXECUTE = 0x1200A0
_FILE_ALL_ACCESS = 0x1F01FF

# AccessCheck needs the owner and group as well as the DACL to evaluate
# CREATOR OWNER entries and the owner's implicit rights.
_OWNER_SECURITY_INFORMATION = 0x1
_GROUP_SECURITY_INFORMATION = 0x2
_DACL_SECURITY_INFORMATION = 0x4
_OWNER_GROUP_DACL_SECURITY_INFORMATION = (
    _OWNER_SECURITY_INFORMATION
    | _GROUP_SECURITY_INFORMATION
    | _DACL_SECURITY_INFORMATION
)
_TOKEN_QUERY = 0x0008
_TOKEN_DUPLICATE = 0x0002
_SECURITY_IMPERSONATION = 2

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

    Any failure to examine the path yields None, matching `os.access`, which
    answers False rather than raising for a missing path, a bad name, a
    filesystem without ACLs, an unreadable descriptor and so on.
    """
    needed = wintypes.DWORD(0)
    # the first call only measures: it fails with ERROR_INSUFFICIENT_BUFFER
    _advapi32.GetFileSecurityW(
        path, _OWNER_GROUP_DACL_SECURITY_INFORMATION, None, 0, ctypes.byref(needed)
    )
    if ctypes.get_last_error() != _ERROR_INSUFFICIENT_BUFFER:
        return None

    buffer = ctypes.create_string_buffer(needed.value)
    if not _advapi32.GetFileSecurityW(
        path,
        _OWNER_GROUP_DACL_SECURITY_INFORMATION,
        buffer,
        needed,
        ctypes.byref(needed),
    ):
        return None
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

    `rights` is a mask of specific file rights from winnt.h; dploy/utils.py
    holds the ones it asks for. Every right in the mask must be granted. Follows
    symlinks, like `os.access`. Returns False for a path it cannot examine (see
    `_security_descriptor`). Raises OSError only if the token or `AccessCheck`
    call itself fails, as that means the answer is unknown rather than "no".
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
