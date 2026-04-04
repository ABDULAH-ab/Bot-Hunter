"""
Installed Chrome major version for undetected_chromedriver.

With version_main=None, uc downloads the latest Stable driver from Google's JSON,
which can be newer than the browser on disk (e.g. driver 147 vs Chrome 146).
"""

from __future__ import annotations

import re
import subprocess
import sys
from typing import Optional


def chrome_major_version(browser_executable_path: Optional[str] = None) -> int:
    import undetected_chromedriver as uc

    exe = browser_executable_path or uc.find_chrome_executable()
    if not exe:
        raise RuntimeError("Chrome executable not found")

    if sys.platform == "win32":
        try:
            import winreg

            for hive, subkey in (
                (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon"),
                (
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon",
                ),
            ):
                try:
                    with winreg.OpenKey(hive, subkey) as k:
                        ver, _ = winreg.QueryValueEx(k, "version")
                    return int(str(ver).split(".")[0])
                except OSError:
                    continue
        except Exception:
            pass
        maj = _windows_exe_file_major(exe)
        if maj:
            return maj
    else:
        for args in (
            [exe, "--product-version"],
            [exe, "--version"],
        ):
            try:
                r = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
                text = (r.stdout or "") + (r.stderr or "")
                m = re.search(r"(\d+)\.", text.strip())
                if m:
                    return int(m.group(1))
            except Exception:
                continue

    raise RuntimeError(f"Could not determine Chrome major version for {exe!r}")


def _windows_exe_file_major(path: str) -> Optional[int]:
    try:
        import ctypes
        from ctypes import wintypes

        class VS_FIXEDFILEINFO(ctypes.Structure):
            _fields_ = [
                ("dwSignature", wintypes.DWORD),
                ("dwStrucVersion", wintypes.DWORD),
                ("dwFileVersionMS", wintypes.DWORD),
                ("dwFileVersionLS", wintypes.DWORD),
            ]

        size = ctypes.windll.version.GetFileVersionInfoSizeW(path, None)
        if not size:
            return None
        buf = ctypes.create_string_buffer(size)
        if not ctypes.windll.version.GetFileVersionInfoW(path, 0, size, buf):
            return None
        ulen = wintypes.UINT()
        ptr = ctypes.c_void_p()
        if not ctypes.windll.version.VerQueryValueW(
            buf, "\\", ctypes.byref(ptr), ctypes.byref(ulen)
        ):
            return None
        ffi = ctypes.cast(ptr, ctypes.POINTER(VS_FIXEDFILEINFO)).contents
        return int(ffi.dwFileVersionMS >> 16)
    except Exception:
        return None
