"""Updates of the LUCI executable (Windows), without Qt so it can be tested on its own.

LUCI lives in a public GitHub repository and the GitHub Action of ``.github/workflows/release.yml``
builds ``LUCI_windows.zip`` and a small ``version.json`` for every tag ``vX.Y.Z``. Both are
attached to the release. This module:

1. reads ``version.json`` of the latest release and says whether it is newer (``check``);
2. downloads the zip, verifies its size and SHA-256 and unpacks it (``download``);
3. replaces the installed files once LUCI has closed and opens LUCI again (``apply_and_restart``).

The download address is built here from the version; the manifest only gives the checksum, so a
manipulated ``version.json`` cannot send LUCI to another place. The user's data (environments,
settings) live in ``luci_home()``, outside the installation folder, and are never touched.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO = "cruzolijavier/LUCI"
BASE_RELEASES = f"https://github.com/{REPO}/releases"
MANIFEST_URL = f"{BASE_RELEASES}/latest/download/version.json"
ASSET = "LUCI_windows.zip"
TIMEOUT = 20
MAX_ZIP = 1_500_000_000          # nothing bigger than 1.5 GB is accepted
MAX_UNPACKED = 4_000_000_000


class UpdateError(Exception):
    """Something failed; the message is meant for the user."""


@dataclass(frozen=True)
class Update:
    version: str
    sha256: str
    size: int
    notes: str
    url: str


# ------------------------------------------------------------------- helpers
def current_version() -> str:
    from . import __version__
    return __version__


def parse_version(text: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", str(text).strip())
    return tuple(int(part) for part in match.groups()) if match else None


def is_newer(candidate: str, current: str) -> bool:
    a, b = parse_version(candidate), parse_version(current)
    return a is not None and b is not None and a > b


def work_dir() -> Path:
    from .settings import luci_home
    folder = luci_home() / "update"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def install_dir() -> Path:
    """Folder of LUCI.exe."""
    return Path(sys.executable).resolve().parent


def _log(message: str) -> None:
    try:
        from datetime import datetime
        from .settings import luci_home
        with (luci_home() / "update.log").open("a", encoding="utf-8") as handle:
            handle.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {message}\n")
    except Exception:
        pass


def can_update() -> tuple[bool, str]:
    """(True, '') if this LUCI can replace itself; otherwise why not."""
    if not getattr(sys, "frozen", False):
        return False, "LUCI is running from the source code, not from the executable."
    if sys.platform != "win32":
        return False, "Automatic updates are only available for the Windows executable."
    folder = install_dir()
    probe = folder / ".luci_write_test"
    try:
        probe.write_text("x", encoding="utf-8")
        probe.unlink()
    except OSError:
        return False, (f"LUCI cannot write in {folder}. Move the LUCI folder somewhere you can write "
                       "(for example Documents) and open it from there.")
    return True, ""


def _get(url: str, limit: int | None = None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "LUCI-updater"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        data = response.read(limit + 1 if limit else -1)
    if limit and len(data) > limit:
        raise UpdateError("The update information is too large.")
    return data


# --------------------------------------------------------------------- check
def check(manifest_url: str = MANIFEST_URL, current: str | None = None,
          base_releases: str = BASE_RELEASES) -> Update | None:
    """The newer version published on GitHub, or None if LUCI is up to date.

    Raises UpdateError if it cannot be found out (offline, no release yet...)."""
    current = current or current_version()
    try:
        raw = _get(manifest_url, limit=100_000)
        data = json.loads(raw.decode("utf-8-sig"))
        version = str(data["version"]).strip().lstrip("v")
        sha256 = str(data["sha256"]).strip().lower()
        size = int(data["size"])
        notes = str(data.get("notes") or "")[:2000]
    except urllib.error.HTTPError as exc:
        raise UpdateError("No published version was found "
                          f"(GitHub answered {exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UpdateError("Could not reach GitHub. Check the internet connection.") from exc
    except (ValueError, KeyError, TypeError) as exc:
        raise UpdateError("The update information is not valid.") from exc
    if parse_version(version) is None or not re.fullmatch(r"[0-9a-f]{64}", sha256) \
            or not 0 < size <= MAX_ZIP:
        raise UpdateError("The update information is not valid.")
    if not is_newer(version, current):
        return None
    return Update(version, sha256, size, notes, f"{base_releases}/download/v{version}/{ASSET}")


# ------------------------------------------------------------------ download
def download(update: Update, progress: Callable[[int, int, str], None] | None = None,
             folder: Path | None = None) -> Path:
    """Download, verify and unpack the zip. Returns the folder holding the new LUCI.exe,
    luci-cli.exe and _internal. ``progress(done, total, text)`` is called along the way."""
    say = progress or (lambda *_: None)
    folder = folder or work_dir()
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True, exist_ok=True)
    zip_path = folder / ASSET
    digest = hashlib.sha256()
    done = 0
    try:
        request = urllib.request.Request(update.url, headers={"User-Agent": "LUCI-updater"})
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response, zip_path.open("wb") as out:
            while True:
                block = response.read(1 << 20)
                if not block:
                    break
                out.write(block)
                digest.update(block)
                done += len(block)
                if done > MAX_ZIP:
                    raise UpdateError("The download is larger than expected.")
                say(done, update.size, "Downloading...")
    except UpdateError:
        raise
    except urllib.error.HTTPError as exc:
        raise UpdateError(f"The download is not available (GitHub answered {exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UpdateError(f"The download failed: {exc}") from exc
    if done != update.size:
        raise UpdateError("The downloaded file has not the expected size. Try again.")
    if digest.hexdigest() != update.sha256:
        zip_path.unlink(missing_ok=True)
        raise UpdateError("The downloaded file is corrupt or was modified (checksum mismatch). "
                          "Nothing was installed.")
    say(0, 0, "Unpacking...")
    target = folder / "new"
    try:
        _unpack(zip_path, target)
    except zipfile.BadZipFile as exc:
        raise UpdateError("The downloaded file is not a valid zip.") from exc
    zip_path.unlink(missing_ok=True)
    root = _find_root(target)
    if root is None:
        raise UpdateError("The update does not contain LUCI.exe, luci-cli.exe and _internal.")
    return root


def _unpack(zip_path: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    base = target.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        total = 0
        for info in archive.infolist():
            total += info.file_size
            destination = (target / info.filename).resolve()
            if base != destination and base not in destination.parents:
                raise UpdateError("The update contains an unsafe path.")
        if total > MAX_UNPACKED:
            raise UpdateError("The update is larger than expected.")
        archive.extractall(target)


def _find_root(target: Path) -> Path | None:
    for candidate in (target, *[p for p in target.iterdir() if p.is_dir()]):
        if (candidate / "LUCI.exe").is_file() and (candidate / "luci-cli.exe").is_file() \
                and (candidate / "_internal").is_dir():
            return candidate
    return None


# -------------------------------------------------------------------- apply
def swap_script(new_dir: Path, install: Path, exe: Path, work: Path, log: Path) -> str:
    """Batch file: wait for LUCI to close, copy the new files, open LUCI, remove itself."""
    return "\r\n".join([
        "@echo off",
        "chcp 65001 >nul",
        f'set "NEW={new_dir}"',
        f'set "DEST={install}"',
        f'set "LOG={log}"',
        "set N=0",
        ":wait",
        "ping -n 2 127.0.0.1 >nul",
        "set /a N+=1",
        "if %N% GEQ 90 goto copy",
        '(>>"%DEST%\\LUCI.exe" (call)) 2>nul && goto copy',
        "goto wait",
        ":copy",
        # Libraries first, executables last: if it stops half way LUCI.exe is still the old one.
        'robocopy "%NEW%\\_internal" "%DEST%\\_internal" /MIR /R:30 /W:2 /NFL /NDL /NJH /NJS /NP >nul',
        "if errorlevel 8 goto failed",
        'robocopy "%NEW%" "%DEST%" /E /XD _internal /R:30 /W:2 /NFL /NDL /NJH /NJS /NP >nul',
        "if errorlevel 8 goto failed",
        '>>"%LOG%" echo %date% %time%  update installed',
        "goto open",
        ":failed",
        '>>"%LOG%" echo %date% %time%  update failed: could not copy the new files',
        ":open",
        "set PYINSTALLER_RESET_ENVIRONMENT=1",
        f'start "" "{exe}"',
        f'rd /s /q "{work}" >nul 2>&1',
        '(goto) 2>nul & del "%~f0"',
        "",
    ])


def apply_and_restart(new_dir: Path) -> None:
    """Start the helper that installs ``new_dir`` after LUCI closes. The caller must then
    quit the application right away."""
    from .settings import luci_home
    install = install_dir()
    exe = Path(sys.executable).resolve()
    work = work_dir()
    script = work / "apply_update.bat"
    script.write_bytes(swap_script(new_dir, install, exe, work, luci_home() / "update.log")
                       .encode("utf-8"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("_PYI") and k != "_MEIPASS2"}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    flags = 0
    if sys.platform == "win32":
        flags = (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                 | subprocess.CREATE_NO_WINDOW)
    _log(f"applying update from {new_dir} to {install}")
    subprocess.Popen(["cmd.exe", "/c", str(script)], cwd=str(luci_home()), env=env,
                     creationflags=flags, close_fds=True)


def clean_leftovers() -> None:
    """At start-up: remove what an earlier update left in the work folder."""
    try:
        from .settings import luci_home
        shutil.rmtree(luci_home() / "update", ignore_errors=True)
    except Exception:
        pass
