"""Windows current-user DPAPI protection shared by persisted credentials."""

import ctypes
from ctypes import wintypes


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def protect_bytes(plain: bytes) -> bytes:
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    source_buffer = ctypes.create_string_buffer(plain)
    source = _DATA_BLOB(
        len(plain), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_byte))
    )
    target = _DATA_BLOB()
    CRYPTPROTECT_UI_FORBIDDEN = 0x1

    if not crypt32.CryptProtectData(
        ctypes.byref(source),
        "DairyOS protected credential",
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(target),
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        kernel32.LocalFree(target.pbData)


def unprotect_bytes(cipher: bytes) -> bytes:
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    source_buffer = ctypes.create_string_buffer(cipher)
    source = _DATA_BLOB(
        len(cipher), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_byte))
    )
    target = _DATA_BLOB()
    CRYPTPROTECT_UI_FORBIDDEN = 0x1

    if not crypt32.CryptUnprotectData(
        ctypes.byref(source),
        None,
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(target),
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        kernel32.LocalFree(target.pbData)
