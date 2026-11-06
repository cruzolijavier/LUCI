"""Where LUCI keeps its data, and the few settings a user configures once.

Settings live in ``<LUCI home>/settings.json`` so the CLI and the GUI share
them. The LUCI home folder holds the environments, the downloaded pixi binary
and the program sources; it can be moved with the ``LUCI_HOME`` variable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import json
import os
from pathlib import Path
import platform
import sys


def current_platform() -> str:
    """LUCI's platform name: windows, linux or macos."""
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def luci_home() -> Path:
    """Folder for environments, sources and settings (created on demand)."""
    override = os.environ.get("LUCI_HOME")
    if override:
        root = Path(override).expanduser().resolve()
    elif current_platform() == "windows":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "LUCI"
    elif current_platform() == "macos":
        root = Path.home() / "Library" / "Application Support" / "LUCI"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "luci"
    root.mkdir(parents=True, exist_ok=True)
    return root


def machine_arch() -> str:
    machine = platform.machine().lower()
    return "aarch64" if machine in ("arm64", "aarch64") else "x86_64"


@dataclass
class Settings:
    """User settings. Empty strings mean "not configured"."""

    # External programs LUCI cannot install (licensed or not packaged).
    gaussian_dir: str = ""
    orca_dir: str = ""
    gxtb_path: str = ""
    # Token for gated model weights (FairChem UMA) on Hugging Face.
    hf_token: str = ""
    # A pixi binary chosen by hand; otherwise LUCI looks on PATH, then downloads one.
    pixi_path: str = ""
    # Behind a firewall that blocks the conda <-> PyPI name mapping download.
    restricted_network: bool = False
    # Default folder for results when the input gives no folder of its own.
    results_dir: str = ""
    # OpenAI key for the LUCI assistant (also read from OPENAI_API_KEY or openai_key.txt).
    openai_api_key: str = ""

    @classmethod
    def path(cls) -> Path:
        return luci_home() / "settings.json"

    @classmethod
    def load(cls) -> "Settings":
        """Read settings.json; anything unreadable or of the wrong type falls back to defaults."""
        try:
            data = json.loads(cls.path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        values = {}
        for spec in fields(cls):
            if spec.name not in data:
                continue
            value = data[spec.name]
            if spec.type in (bool, "bool"):
                values[spec.name] = value is True or str(value).lower() in ("true", "1", "yes")
            elif value is not None:
                values[spec.name] = str(value)
        return cls(**values)

    def save(self) -> None:
        """Write atomically: a crash never leaves a half-written settings file."""
        target = self.path()
        partial = target.with_suffix(".partial")
        partial.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        partial.replace(target)

    def default_results_dir(self) -> Path:
        if self.results_dir:
            return Path(self.results_dir).expanduser()
        return Path.home() / "LUCI-results"

    def placeholders(self) -> dict[str, str]:
        """Values for {gaussian_dir}, {orca_dir}, {gxtb_path}, {hf_token} in env_vars."""
        return {
            "gaussian_dir": self.gaussian_dir,
            "orca_dir": self.orca_dir,
            "gxtb_path": self.gxtb_path,
            "hf_token": self.hf_token,
        }
