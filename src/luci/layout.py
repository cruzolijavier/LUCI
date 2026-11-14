"""Where results go, and the LUCI_data.dat that explains them.

Every run writes into ``<results>/LUCI_<LAYER>/<Program>/``::

    results/
    ├── LUCI_STRUCT/
    │   ├── LUCI_data.dat        one block per run in this layer, oldest first
    │   └── AQME_CSEARCH/        the program's own output, unchanged
    └── LUCI_FEAT/
        ├── LUCI_data.dat
        └── Morfeus/

``<results>`` is the output folder the user chose or, by default, the folder
of the input. When the input is itself the output of an earlier LUCI step
(``results/LUCI_STRUCT/AQME_CSEARCH``), the next layer goes to the same
``results/`` folder, so a whole workflow stays side by side instead of nesting.
Running the same program again reuses its folder, as AQME does with CSEARCH/:
ROBERT's steps and the rounds of a design loop need that.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
import textwrap
import time

from . import __version__

DATA_FILE = "LUCI_data.dat"
LAYER_PREFIX = "LUCI_"
# Bookkeeping LUCI writes inside a program folder; never listed as results.
HIDDEN_PARTS = {".luci", ".luci-tmp", "__pycache__"}
RULE = "=" * 78


def layer_folder_name(layer_key: str) -> str:
    """``struct`` -> ``LUCI_STRUCT``."""
    return LAYER_PREFIX + layer_key.upper()


def program_folder_name(program) -> str:
    """The program's folder: its name as a safe file name (``AQME CSEARCH`` -> ``AQME_CSEARCH``)."""
    name = program.name.replace("+", "plus")
    return re.sub(r"[^\w-]+", "_", name).strip("_") or program.key


def _layer_folders() -> set[str]:
    from .registry import LAYERS
    return {layer_folder_name(spec.key).lower() for spec in LAYERS}


def is_layer_folder(path: Path) -> bool:
    return path.name.lower() in _layer_folders()


def results_root(folder: Path) -> Path:
    """The workflow folder that holds the ``LUCI_<LAYER>`` folders.

    ``results/LUCI_STRUCT/AQME_CSEARCH`` and ``results/LUCI_STRUCT`` both give
    ``results``; any other folder is returned unchanged.
    """
    folder = Path(folder)
    if is_layer_folder(folder):
        return folder.parent
    if folder.parent != folder and is_layer_folder(folder.parent):
        return folder.parent.parent
    return folder


def program_dir(root: Path, program) -> Path:
    """``root/LUCI_<LAYER>/<Program>``."""
    return Path(root) / layer_folder_name(program.layer) / program_folder_name(program)


def earlier_step(path: Path | str | None) -> str:
    """``LUCI_STRUCT/AQME_CSEARCH`` when ``path`` lies inside an earlier LUCI step, else ``""``."""
    if not path:
        return ""
    current = Path(path)
    for candidate in (current, *current.parents):
        if candidate.parent != candidate and is_layer_folder(candidate.parent):
            return f"{candidate.parent.name}/{candidate.name}"
    return ""


# ---------------------------------------------------------------------------
# LUCI_data.dat
# ---------------------------------------------------------------------------
def snapshot(folder: Path) -> dict[str, float]:
    """Relative path -> modification time of every result file under ``folder``."""
    found: dict[str, float] = {}
    if not folder.is_dir():
        return found
    for path in folder.rglob("*"):
        try:
            relative = path.relative_to(folder)
        except ValueError:
            continue
        if HIDDEN_PARTS.intersection(relative.parts) or not path.is_file():
            continue
        try:
            found[relative.as_posix()] = path.stat().st_mtime
        except OSError:
            continue
    return found


def changed_files(folder: Path, before: dict[str, float]) -> list[str]:
    """Files written or updated under ``folder`` since ``before``."""
    after = snapshot(folder)
    return sorted(name for name, mtime in after.items() if before.get(name) != mtime)


@dataclass
class RunRecord:
    """Everything LUCI_data.dat says about one run."""

    program: object
    variant: object
    env_title: str
    outdir: Path
    root: Path
    command: str = ""
    luci_command: str = ""
    input_lines: list[str] = field(default_factory=list)
    input_source: str = ""
    native: list[str] = field(default_factory=list)
    started: float = field(default_factory=time.time)
    started_at: datetime = field(default_factory=datetime.now)
    before: dict[str, float] = field(default_factory=dict)

    def begin(self) -> None:
        self.before = snapshot(self.outdir)
        self.started = time.time()
        self.started_at = datetime.now()

    def finish(self, code: int, *, missing: list[str] | None = None,
               stopped: bool = False, crashed: bool = False, extra: list[str] | None = None) -> Path:
        """Append this run to ``LUCI_<LAYER>/LUCI_data.dat``; return the file."""
        from .registry import layer
        layer_spec = layer(self.program.layer)
        data = self.outdir.parent / DATA_FILE
        new_file = not data.exists()
        lines: list[str] = []
        if new_file:
            lines += [RULE, f"LUCI_data.dat - {layer_spec.title} ({layer_spec.delivers})",
                      *textwrap.wrap(layer_spec.description, 78), "",
                      "One block per program run in this folder, oldest first. Each program's own",
                      "output is in the folder named after it, next to this file.",
                      RULE, ""]
        elapsed = time.time() - self.started
        if stopped:
            outcome = f"stopped (exit code {code})"
        elif crashed:
            outcome = f"crashed (exit code {code}): the program was killed by the system"
        elif code == 0:
            outcome = "finished correctly (exit code 0)"
        else:
            outcome = f"failed (exit code {code}); see the program's messages in its log or console"
        written = changed_files(self.outdir, self.before)
        try:
            folder = self.outdir.relative_to(self.root).as_posix()
        except ValueError:
            folder = str(self.outdir)
        title = f"{self.program.name}"
        if len(self.program.variants) > 1:
            title += f" ({self.variant.label})"
        lines += [
            "-" * 78,
            f"{self.started_at:%Y-%m-%d %H:%M:%S}  {title}",
            "-" * 78,
            *_field("What it does", self.program.description),
            f"Layer        : {layer_spec.title} ({layer_spec.delivers})",
            f"Environment  : {self.env_title}",
            f"LUCI version : {__version__}",
            f"Result       : {outcome}",
            f"Duration     : {_duration(elapsed)}",
            f"Output folder: {folder}",
        ]
        if self.input_source:
            lines.append(f"Input from   : {self.input_source} (an earlier LUCI step)")
        if self.input_lines:
            lines.append("Input        : " + self.input_lines[0])
            lines += ["               " + line for line in self.input_lines[1:8]]
        if self.native:
            lines.append("Options      : " + " ".join(self.native))
        if self.luci_command:
            lines.append("LUCI command : " + self.luci_command)
        if self.command:
            lines.append("Program call : " + self.command)
        if written:
            shown = written[:25]
            lines.append(f"Files written: {len(written)}")
            lines += ["               " + name for name in shown]
            if len(written) > len(shown):
                lines.append(f"               ... and {len(written) - len(shown)} more")
        else:
            lines.append("Files written: none")
        if missing:
            lines.append(f"No result for: {len(missing)} input(s): " + ", ".join(missing[:20])
                         + (" ..." if len(missing) > 20 else ""))
        for line in extra or []:
            lines.append("Note         : " + line)
        if self.program.citation:
            lines.append("Cite         : " + self.program.citation)
        if self.program.docs_url:
            lines.append("Docs         : " + self.program.docs_url)
        lines.append("")
        data.parent.mkdir(parents=True, exist_ok=True)
        with open(data, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        return data


def _field(label: str, text: str) -> list[str]:
    """``Label        : text`` wrapped at 78 columns, continuation lines aligned."""
    wrapped = textwrap.wrap(text, 78 - 15) or [""]
    return [f"{label:<13}: {wrapped[0]}"] + [" " * 15 + line for line in wrapped[1:]]


def _duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, secs = divmod(int(round(seconds)), 60)
    if minutes < 60:
        return f"{minutes} min {secs:02d} s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes:02d} min"
