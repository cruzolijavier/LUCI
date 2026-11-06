"""Updates of the LUCI executable (Windows), without Qt so it can be tested on its own.

LUCI lives in a public GitHub repository and the GitHub Action of ``.github/workflows/release.yml``
builds ``LUCI_windows.zip`` and a small ``version.json`` for every tag ``vX.Y.Z``. Both are
attached to the release. This module:

1. reads ``version.json`` of the latest release and says whether it is newer (``check``);
2. downloads the zip, verifies its size and SHA-256 and unpacks it (``download``);
3. replaces the installed files once LUCI has closed and opens LUCI again (``apply_and_restart``).
   The work is done by the NEW LUCI.exe, started from the unpacked update with ``--apply-update``
   (``helper_main``): no batch file, no console window, and it never depends on a script host.
   Updates published before that existed fall back to a hidden batch file (``swap_script``).

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
import time
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


HELPER_FLAG = "--apply-update"
# A file of the luci package: if the unpacked update has it, its LUCI.exe can apply the update itself.
HELPER_MARKER = "apply_helper.txt"


def supports_helper(new_dir: Path) -> bool:
    return (new_dir / "_internal" / "luci" / HELPER_MARKER).is_file()


def _clean_env() -> dict:
    """The environment for a program started from a PyInstaller LUCI: without its private variables."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("_PYI") and k != "_MEIPASS2"}
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env


def _spawn(argv: list[str], cwd: Path, flags: int, env: dict) -> subprocess.Popen:
    """Start a process that outlives LUCI. It tries to leave LUCI's job object first (so closing LUCI
    cannot take it down); if the system does not allow that it starts it normally."""
    extra = dict(cwd=str(cwd), env=env, close_fds=True, stdin=subprocess.DEVNULL,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if sys.platform != "win32":
        return subprocess.Popen(argv, start_new_session=True, **extra)
    flags |= subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        return subprocess.Popen(argv, creationflags=flags | subprocess.CREATE_BREAKAWAY_FROM_JOB, **extra)
    except OSError:
        return subprocess.Popen(argv, creationflags=flags, **extra)


def apply_and_restart(new_dir: Path, restart: bool = True) -> None:
    """Start the helper that installs ``new_dir`` after LUCI closes (and opens LUCI again if
    ``restart``). The caller must then quit the application right away. Raises if the helper
    could not be started, so the caller can keep LUCI open."""
    from .settings import luci_home
    install = install_dir()
    exe = Path(sys.executable).resolve()
    work = work_dir()
    log = luci_home() / "update.log"
    env = _clean_env()
    _log(f"applying update from {new_dir} to {install} (restart={restart})")
    if supports_helper(new_dir):
        argv = [str(new_dir / "LUCI.exe"), HELPER_FLAG, "--install", str(install), "--pid", str(os.getpid()),
                "--log", str(log)]
        if not restart:
            argv.append("--no-restart")
        flags = getattr(subprocess, "DETACHED_PROCESS", 0)   # a window program: it needs no console
        process = _spawn(argv, work, flags, env)
    else:
        # Update published before the helper existed: hidden batch file (no ping window).
        script = work / "apply_update.bat"
        script.write_bytes(swap_script(new_dir, install, exe, work, log).encode("utf-8"))
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        process = _spawn(["cmd.exe", "/c", str(script)], luci_home(), flags, env)
    time.sleep(1.5)
    if process.poll() is not None:
        # The helper waits for LUCI to close, so it must still be running: it died at once.
        raise UpdateError("The update helper could not start (see update.log).")


# --------------------------------------------------- helper (runs in the NEW LUCI.exe)
def _wait_for_exit(pid: int, seconds: int = 120) -> None:
    """Wait until the process ``pid`` (the old LUCI) is gone."""
    if sys.platform == "win32":
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(0x00100000, False, pid)       # SYNCHRONIZE
        if handle:
            kernel.WaitForSingleObject(handle, seconds * 1000)
            kernel.CloseHandle(handle)
        return
    for _ in range(seconds * 5):
        try:
            os.kill(pid, 0)
        except OSError:
            return
        time.sleep(0.2)


def _retry(action: Callable[[], None], tries: int = 40, pause: float = 0.5) -> None:
    """Run ``action``, trying again for a while: an antivirus or the dying LUCI may hold a file."""
    for attempt in range(tries):
        try:
            action()
            return
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(pause)


def swap_files(source: Path, install: Path) -> None:
    """Put the files of ``source`` (unpacked update) into ``install``. If anything fails the old
    files are put back, so the installation is never left half way."""
    current, old, fresh = install / "_internal", install / "_internal.old", source / "_internal"
    shutil.rmtree(old, ignore_errors=True)
    moved = False
    try:
        if current.exists():
            _retry(lambda: os.replace(current, old))
            moved = True
        _retry(lambda: shutil.copytree(fresh, current, dirs_exist_ok=True))
        files = [p for p in source.iterdir() if p.is_file()]
        for path in files:
            _retry(lambda p=path: shutil.copy2(p, install / (p.name + ".new")))
        # Executables last, and all at once: a failure before this point leaves the old LUCI.exe.
        for path in sorted(files, key=lambda p: p.suffix.lower() == ".exe"):
            _retry(lambda p=path: os.replace(install / (p.name + ".new"), install / p.name))
    except Exception:
        shutil.rmtree(current, ignore_errors=True)
        if moved and old.exists():
            try:
                os.replace(old, current)
            except OSError:
                pass
        for leftover in install.glob("*.new"):
            leftover.unlink(missing_ok=True)
        raise
    shutil.rmtree(old, ignore_errors=True)


def helper_main(argv: list[str]) -> int:
    """Entry of ``LUCI.exe --apply-update``: wait for the old LUCI, replace the files, open LUCI.
    It runs from the unpacked update, never from the folder it replaces."""
    import traceback

    def value(flag: str) -> str:
        return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else ""

    install = Path(value("--install"))
    log = Path(value("--log")) if value("--log") else None
    restart = "--no-restart" not in argv

    def say(text: str) -> None:
        if log is not None:
            try:
                from datetime import datetime
                with log.open("a", encoding="utf-8") as handle:
                    handle.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  helper: {text}\n")
            except OSError:
                pass

    source = Path(sys.executable).resolve().parent
    error = ""
    try:
        if not install.is_dir() or source == install.resolve():
            raise UpdateError(f"Wrong installation folder: {install}")
        try:
            pid = int(value("--pid"))
        except ValueError:
            pid = 0
        say(f"waiting for LUCI (pid {pid}) to close")
        if pid:
            _wait_for_exit(pid)
        swap_files(source, install)
        say("update installed")
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        say("update failed: " + traceback.format_exc().strip().replace("\n", " | "))
    if error and sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0, "LUCI could not be updated, so the previous version was kept.\n\n" + error + "\n\nDetails: "
                + str(log or "update.log"), "Update LUCI", 0x10)
        except Exception:
            pass
    target = install / ("LUCI.exe" if sys.platform == "win32" else "LUCI")
    if restart and target.is_file():
        try:
            _spawn([str(target)], install, getattr(subprocess, "DETACHED_PROCESS", 0), _clean_env())
            say("LUCI opened again")
        except Exception as exc:
            say(f"could not open LUCI: {exc}")
    return 1 if error else 0


def clean_leftovers() -> None:
    """At start-up: remove what an earlier update left in the work folder."""
    try:
        from .settings import luci_home
        shutil.rmtree(luci_home() / "update", ignore_errors=True)
    except Exception:
        pass
