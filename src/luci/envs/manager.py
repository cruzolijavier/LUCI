"""Create, inspect, remove and use the per-program pixi environments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
import os
import re
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

from .. import __version__
from ..proc import run_forwarding_signals
from ..registry import ENV_BY_KEY, EnvSpec
from ..settings import Settings, current_platform, luci_home, machine_arch

# Pinned so every machine resolves environments with the same pixi.
PIXI_VERSION = "0.83.0"
# Oldest pixi LUCI accepts from PATH: the pinned one. The pixi.lock files are written by
# it (lock format 7), and older pixi builds (e.g. the one Avogadro 2 puts on PATH) refuse
# them with "lock file version is 7, but only up to 6 is supported".
MIN_PIXI = tuple(int(n) for n in PIXI_VERSION.split("."))
MANIFESTS = Path(__file__).resolve().parent / "manifests"
MARKER = ".luci-installed.json"


def _log(message: str) -> None:
    print(f"[LUCI] {message}", flush=True)


def _on_rm_error(func, path, _exc):
    # Windows marks git objects read-only; clear the flag and retry.
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _rmtree(path: Path) -> None:
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_on_rm_error)
    else:
        shutil.rmtree(path, onerror=_on_rm_error)


@dataclass(frozen=True)
class EnvStatus:
    key: str
    title: str
    installed: bool
    outdated: bool
    supported: bool
    available: bool
    note: str
    size_hint: str


class EnvError(RuntimeError):
    """An environment problem with a message meant for the user."""


class EnvManager:
    def __init__(self, home: Path | None = None, settings: Settings | None = None):
        self.home = Path(home) if home else luci_home()
        self.settings = settings or Settings.load()

    # ------------------------------------------------------------- locations
    def workspace(self, key: str) -> Path:
        return self.home / "envs" / key

    def manifest(self, key: str) -> Path:
        return self.workspace(key) / "pixi.toml"

    def packaged_manifest(self, key: str) -> Path:
        return MANIFESTS / key / "pixi.toml"

    def source_dir(self, key: str) -> Path:
        return self.workspace(key) / "src"

    def prefix(self, key: str) -> Path:
        return self.workspace(key) / ".pixi" / "envs" / "default"

    def bin_dir(self, key: str) -> Path:
        prefix = self.prefix(key)
        return prefix / "Library" / "bin" if current_platform() == "windows" else prefix / "bin"

    # ------------------------------------------------------------------ pixi
    def pixi_path(self) -> Path | None:
        """The pixi binary LUCI will use, without downloading anything.

        A pixi on PATH is used only if it is recent enough for LUCI's manifests;
        an old one (from an earlier tutorial) would fail to read them.
        """
        for candidate in (self.settings.pixi_path, os.environ.get("LUCI_PIXI", "")):
            if candidate and Path(candidate).expanduser().is_file():
                return Path(candidate).expanduser()
        found = shutil.which("pixi")
        if found and pixi_version(found) >= MIN_PIXI:
            return Path(found)
        local = self.home / "bin" / ("pixi.exe" if current_platform() == "windows" else "pixi")
        # One downloaded by an older LUCI is replaced (ensure_pixi downloads the pinned one).
        return local if local.is_file() and pixi_version(local) >= MIN_PIXI else None

    def ensure_pixi(self) -> Path:
        """Return a usable pixi, downloading the pinned release on first use."""
        existing = self.pixi_path()
        if existing is not None:
            return existing
        system = current_platform()
        # Windows on ARM runs the x86-64 build (and its win-64 environments) emulated.
        arch = "x86_64" if system == "windows" else machine_arch()
        if system == "windows":
            asset = f"pixi-{arch}-pc-windows-msvc.zip"
        elif system == "macos":
            asset = f"pixi-{arch}-apple-darwin.tar.gz"
        else:
            asset = f"pixi-{arch}-unknown-linux-musl.tar.gz"
        url = f"https://github.com/prefix-dev/pixi/releases/download/v{PIXI_VERSION}/{asset}"
        target_dir = self.home / "bin"
        target_dir.mkdir(parents=True, exist_ok=True)
        name = "pixi.exe" if system == "windows" else "pixi"
        _log(f"Downloading pixi {PIXI_VERSION} (one time only)...")
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                payload = response.read()
        except OSError as exc:
            raise EnvError(f"Could not download pixi from {url}: {exc}. Check the internet "
                           "connection, or install pixi yourself (https://pixi.sh) and set its "
                           "path in Settings.") from exc
        partial = target_dir / (name + ".partial")
        try:
            if asset.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    member = next((m for m in archive.namelist() if m.endswith(name)), None)
                    if member is None:
                        raise EnvError("the downloaded archive does not contain pixi")
                    partial.write_bytes(archive.read(member))
            else:
                with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
                    member = next((m for m in archive.getmembers() if m.name.endswith(name)), None)
                    if member is None:
                        raise EnvError("the downloaded archive does not contain pixi")
                    partial.write_bytes(archive.extractfile(member).read())
        except (zipfile.BadZipFile, tarfile.TarError, OSError, EOFError) as exc:
            partial.unlink(missing_ok=True)
            raise EnvError(f"The pixi download from {url} is damaged ({exc}). A proxy or "
                           "firewall may have replaced it; try again, or install pixi yourself "
                           "and set its path in Settings.") from exc
        partial.chmod(partial.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        # Renamed only once complete: a cut download never leaves a broken pixi.
        binary = target_dir / name
        partial.replace(binary)
        _log(f"pixi saved to {binary}")
        return binary

    # ---------------------------------------------------------------- status
    def _manifest_text(self, key: str) -> str:
        text = self.packaged_manifest(key).read_text(encoding="utf-8")
        if self.settings.restricted_network and "conda-pypi-map" not in text:
            # Firewalls often block the conda<->PyPI name mapping download.
            text = text.replace("[workspace]\n", "[workspace]\nconda-pypi-map = false\n", 1)
        return text

    def _manifest_hash(self, key: str) -> str:
        # The packaged text only: switching "restricted network" is not an update.
        text = self.packaged_manifest(key).read_text(encoding="utf-8")
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def marker(self, key: str) -> dict:
        try:
            return json.loads((self.workspace(key) / MARKER).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def is_installed(self, key: str) -> bool:
        return bool(self.marker(key)) and self.prefix(key).is_dir()

    def is_outdated(self, key: str) -> bool:
        marker = self.marker(key)
        return bool(marker) and marker.get("manifest") != self._manifest_hash(key)

    def supported(self, spec: EnvSpec) -> bool:
        return current_platform() in spec.platforms

    def status(self, key: str) -> EnvStatus:
        spec = ENV_BY_KEY[key]
        installed = self.is_installed(key)
        return EnvStatus(key, spec.title, installed, installed and self.is_outdated(key),
                         self.supported(spec), spec.available, spec.note, spec.size_hint)

    def statuses(self) -> list[EnvStatus]:
        return [self.status(key) for key in ENV_BY_KEY]

    def check_usable(self, key: str) -> None:
        """Raise EnvError with a user-facing reason when ``key`` cannot run here."""
        spec = ENV_BY_KEY[key]
        if not spec.available:
            raise EnvError(f"{spec.title} is not available yet: {spec.note}")
        if not self.supported(spec):
            places = ", ".join(spec.platforms)
            raise EnvError(f"{spec.title} runs on {places} only. {spec.note}".strip())

    # --------------------------------------------------------------- install
    def _run(self, argv: list[str], cwd: Path | None = None, step: str = "",
             monitor: "DownloadMonitor | None" = None) -> None:
        _log("$ " + " ".join(str(a) for a in argv))
        if monitor is not None:
            monitor.start()
        try:
            code = run_forwarding_signals([str(a) for a in argv], cwd=cwd, env=pixi_environment())
        finally:
            if monitor is not None:
                monitor.stop()
        if code != 0:
            what = step or Path(str(argv[0])).name
            if code < 0:
                raise EnvError(f"{what} was stopped.")
            raise EnvError(f"{what} failed (exit code {code}). The reason is in the lines above.")

    def _fetch_source(self, spec: EnvSpec, refresh: bool = False) -> None:
        """Clone or download the program's code into ``src/``, atomically.

        The code lands in a temporary folder first and is renamed into place
        only when complete, so a stopped clone never looks like a finished one.
        Without Git, or when Git cannot reach GitHub (Git ignores the Windows
        proxy settings), the branch is downloaded as a zip archive instead.
        """
        target = self.source_dir(spec.key)
        if target.is_dir() and any(target.iterdir()) and not refresh:
            _log(f"Source already present in {target}")
            return
        source = spec.source
        staging = target.with_name("src.partial")
        if staging.exists():
            _rmtree(staging)
        git = shutil.which("git")
        cloned = False
        if git:
            try:
                self._run([git, "clone", "--depth", "1", "--branch", source.branch, source.repo,
                           staging], step="git clone")
                cloned = True
            except EnvError as exc:
                _log(f"{exc} Trying a zip download instead.")
                if staging.exists():
                    _rmtree(staging)
        if not cloned:
            url = f"{source.repo.rstrip('/')}/archive/refs/heads/{source.branch}.zip"
            _log(f"Downloading {url}")
            try:
                with urllib.request.urlopen(url, timeout=300) as response:
                    payload = response.read()
            except OSError as exc:
                raise EnvError(f"Could not download the code of {spec.title} from {url}: {exc}. "
                               "Check the internet connection (and proxy) and try again.") from exc
            with tempfile.TemporaryDirectory(dir=self.workspace(spec.key)) as tmp:
                try:
                    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                        _safe_extract(archive, Path(tmp))
                except zipfile.BadZipFile as exc:
                    raise EnvError(f"The download of {spec.title} is damaged ({exc}).") from exc
                roots = [p for p in Path(tmp).iterdir() if p.is_dir()]
                if len(roots) != 1:
                    raise EnvError(f"Unexpected archive layout for {spec.title}")
                shutil.move(str(roots[0]), str(staging))
        if target.exists():
            _rmtree(target)
        staging.rename(target)

    def _write_marker(self, key: str, pixi: Path) -> None:
        marker = self.workspace(key) / MARKER
        partial = marker.with_suffix(".partial")
        partial.write_text(json.dumps({
            "manifest": self._manifest_hash(key),
            "installed": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "luci": __version__,
            "pixi": ".".join(str(n) for n in pixi_version(pixi)) or PIXI_VERSION,
        }, indent=2), encoding="utf-8")
        partial.replace(marker)

    def install(self, key: str) -> None:
        """Create (or update) the environment ``key``; output streams to stdout.

        The environment counts as installed only once every step succeeded: the
        marker is removed first and written last, so a run killed half-way
        (even by a hard Stop) never leaves an environment that looks ready. On
        an ordinary failure the previous manifest and lock are restored and the
        previous environment is put back from them when possible.
        """
        spec = ENV_BY_KEY[key]
        self.check_usable(key)
        if spec.needs_git and not shutil.which("git"):
            raise EnvError(
                f"{spec.title} is installed from GitHub and needs Git. Install Git "
                "(on Windows: https://git-scm.com/download/win, default options), restart LUCI "
                "and try again.")
        pixi = self.ensure_pixi()
        workspace = self.workspace(key)
        workspace.mkdir(parents=True, exist_ok=True)
        _log(f"Preparing {spec.title} in {workspace}")
        lock = workspace / "pixi.lock"
        marker = workspace / MARKER
        previous_marker = self.marker(key)
        was_installed = self.is_installed(key)
        refresh_source = was_installed and self.is_outdated(key)
        if not previous_marker and self.prefix(key).exists():
            # Left over from a removal or install that did not finish: start clean,
            # pixi would otherwise trust its half-deleted metadata.
            _log("Removing an incomplete previous installation")
            try:
                _rmtree(self.prefix(key))
            except OSError as exc:
                raise EnvError(f"Could not clean up the previous, unfinished installation ({exc}). "
                               "Wait a few seconds (Windows may still be closing files) and "
                               "install again.") from exc
        backup = {path: path.read_bytes() for path in (self.manifest(key), lock) if path.is_file()}
        marker.unlink(missing_ok=True)
        try:
            self.manifest(key).write_text(self._manifest_text(key), encoding="utf-8")
            packaged_lock = self.packaged_manifest(key).with_name("pixi.lock")
            if packaged_lock.is_file():
                shutil.copyfile(packaged_lock, lock)
            if spec.source is not None:
                self._fetch_source(spec, refresh=refresh_source)
            command = [pixi, "install", "--manifest-path", self.manifest(key)]
            if lock.is_file():
                # The exact versions LUCI was tested with; nothing is solved here.
                command.append("--frozen")
            total = download_size(lock)
            if total:
                _log(f"Downloading up to {_human(total)} of packages (less if some are already in "
                     "pixi's cache) and unpacking them, about 3-4 times that on disk. pixi prints "
                     "nothing while it works; LUCI reports progress every 15 seconds.")
            self._run(command, step="pixi install",
                      monitor=DownloadMonitor(pixi, self.prefix(key), total))
            if spec.postinstall:
                self._run([pixi, "run", "--manifest-path", self.manifest(key), "--frozen",
                           "postinstall"], cwd=workspace, step="Post-install step")
        except BaseException as exc:
            self._roll_back(key, pixi, backup, previous_marker if was_installed else {})
            if (isinstance(exc, EnvError) and not self.settings.restricted_network
                    and "was stopped" not in str(exc)):
                raise EnvError(f"{exc} If the log mentions the conda-pypi mapping or a "
                               "network timeout, a firewall may be blocking it: turn on "
                               "'Restricted network' in Settings and install again.") from exc
            raise
        self._write_marker(key, pixi)
        _log(f"{spec.title} is ready.")

    def _roll_back(self, key: str, pixi: Path, backup: dict, previous_marker: dict) -> None:
        """Restore the previous manifest/lock and, if it was installed, that environment."""
        for path, content in backup.items():
            try:
                path.write_bytes(content)
            except OSError:
                pass
        if not previous_marker:
            return
        try:
            _log("Restoring the previous installation...")
            self._run([pixi, "install", "--manifest-path", self.manifest(key), "--frozen"],
                      step="Restoring the previous installation")
        except (EnvError, OSError) as exc:
            _log(f"{exc} Install {ENV_BY_KEY[key].title} again before using it.")
            return
        marker = self.workspace(key) / MARKER
        marker.write_text(json.dumps(previous_marker, indent=2), encoding="utf-8")

    def remove(self, key: str) -> None:
        workspace = self.workspace(key)
        if workspace.exists():
            _log(f"Removing {workspace}")
            # The marker goes first: a half-deleted folder must not look installed.
            try:
                (workspace / MARKER).unlink(missing_ok=True)
                _rmtree(workspace)
            except OSError as exc:
                raise EnvError(f"Could not remove {workspace} completely ({exc}). Close any "
                               "program using it and try again.") from exc
        _log(f"{ENV_BY_KEY[key].title} removed.")

    # ------------------------------------------------------------------- run
    def run_argv(self, key: str, command: list[str]) -> list[str]:
        """The argv that runs ``command`` inside environment ``key``."""
        pixi = self.pixi_path() or "pixi"
        # --frozen: use the lock file as installed, never re-solve during a run.
        return [str(pixi), "run", "--manifest-path", str(self.manifest(key)), "--frozen",
                "--no-install", "--executable", *command]


def _human(size: float) -> str:
    for unit in ("bytes", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit in ("bytes", "KB") else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def download_size(lock: Path) -> int:
    """Bytes of conda packages the lock file lists for this computer's platform."""
    platform_dir = {"windows": "win-64", "linux": "linux-64", "macos": "osx-arm64"}.get(
        current_platform(), "linux-64")
    if current_platform() == "macos" and machine_arch() != "aarch64":
        platform_dir = "osx-64"
    try:
        text = lock.read_text(encoding="utf-8")
    except OSError:
        return 0
    total = 0
    for block in text.split("\n- conda: ")[1:]:
        url = block.split("\n", 1)[0]
        if f"/{platform_dir}/" in url or "/noarch/" in url:
            match = re.search(r"\n  size: (\d+)", block)
            if match:
                total += int(match.group(1))
    return total


def _tree_size(path: Path, newer_than: float = 0.0) -> int:
    """Total size of files under ``path`` (only top-level entries newer than a time)."""
    total = 0
    try:
        entries = list(os.scandir(path))
    except OSError:
        return 0
    for entry in entries:
        try:
            if newer_than and entry.stat(follow_symlinks=False).st_mtime < newer_than:
                continue
            if entry.is_file(follow_symlinks=False):
                total += entry.stat(follow_symlinks=False).st_size
            elif entry.is_dir(follow_symlinks=False):
                for root, _dirs, files in os.walk(entry.path):
                    for name in files:
                        try:
                            total += os.lstat(os.path.join(root, name)).st_size
                        except OSError:
                            pass
        except OSError:
            continue
    return total


class DownloadMonitor:
    """Reports, every 15 s, how much pixi has downloaded and unpacked.

    pixi shows no progress when its output is not a terminal (the LUCI window),
    so long installs looked frozen. The monitor measures the new packages in
    pixi's cache and the size of the environment folder.
    """

    def __init__(self, pixi: Path, prefix: Path, expected: int = 0, interval: float = 15.0):
        import threading
        self.prefix = prefix
        self.expected = expected
        self.interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._cache = None
        self._pixi = pixi

    def _cache_dir(self) -> Path | None:
        try:
            out = subprocess.run([str(self._pixi), "info", "--json"], capture_output=True,
                                 text=True, timeout=30, env=pixi_environment()).stdout
            return Path(json.loads(out)["cache_dir"])
        except (OSError, ValueError, KeyError, subprocess.SubprocessError):
            return None

    def start(self):
        import time
        self._started = time.time()
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        import time
        self._cache = self._cache_dir()
        while not self._stop.wait(self.interval):
            elapsed = int(time.time() - self._started)
            parts = [f"{elapsed // 60}:{elapsed % 60:02d}"]
            if self._cache is not None:
                downloaded = sum(_tree_size(self._cache / sub, self._started - 5)
                                 for sub in ("pkgs", "uv-cache"))
                # The cache holds unpacked packages, larger than the download itself.
                parts.append(f"{_human(downloaded)} of packages downloaded and unpacked")
            if self.prefix.is_dir():
                parts.append(f"environment folder {_human(_tree_size(self.prefix))}")
            _log("Still working (" + ", ".join(parts) + ")")


_VERSIONS: dict[tuple[str, int], tuple[int, ...]] = {}


def pixi_version(binary) -> tuple[int, ...]:
    """(major, minor, patch) of a pixi binary, or () if it cannot be asked."""
    try:
        key = (str(binary), Path(binary).stat().st_mtime_ns)
    except OSError:
        return ()
    if key not in _VERSIONS:
        _VERSIONS[key] = _ask_version(binary)
    return _VERSIONS[key]


def _ask_version(binary) -> tuple[int, ...]:
    try:
        out = subprocess.run([str(binary), "--version"], capture_output=True, text=True,
                             timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return ()
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    return tuple(int(n) for n in match.groups()) if match else ()


def pixi_environment() -> dict[str, str]:
    """The environment for pixi: certificate variables pointing nowhere are dropped.

    Anaconda environments set SSL_CERT_DIR to a folder that may be empty; pixi
    then prints a warning on every call.
    """
    environ = dict(os.environ)
    for name in ("SSL_CERT_DIR", "SSL_CERT_FILE"):
        value = environ.get(name)
        if value and not (Path(value).is_file() or (Path(value).is_dir() and any(Path(value).iterdir()))):
            environ.pop(name)
    return environ


def _safe_extract(archive: zipfile.ZipFile, target: Path) -> None:
    """Extract a zip, refusing members that would land outside ``target``."""
    root = target.resolve()
    for member in archive.namelist():
        destination = (root / member).resolve()
        if root != destination and root not in destination.parents:
            raise EnvError(f"Refusing to extract {member}: outside the target folder")
    archive.extractall(root)


def python_runner_path(name: str) -> Path:
    """Absolute path of a runner script executed inside an environment."""
    return Path(__file__).resolve().parent.parent / "runners" / f"{name}.py"


__all__ = ["EnvError", "EnvManager", "EnvStatus", "PIXI_VERSION", "python_runner_path"]
