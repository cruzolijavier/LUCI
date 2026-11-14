"""Real runs of every LUCI program, as a user would start them.

Each test copies real inputs (molecule CSVs, SDF/XYZ/Gaussian files, QM
outputs, tables) from ``tests/programs/inputs`` into a temporary folder, runs
``luci <layer> --backend <program> ...`` in a separate process (the same path
the window takes) and checks the files the program wrote: number of
conformers, atoms, energies, descriptors in a sensible range, predictions...

The programs run inside their own pixi environments, so they must be installed
(``luci env install <program>``). A program that is not installed is skipped,
unless ``LUCI_REQUIRE_PROGRAMS`` says it must be there (CircleCI):

    LUCI_REQUIRE_PROGRAMS=all            every environment must be installed
    LUCI_REQUIRE_PROGRAMS=aqme,dbstep    only these

Run them with ``pytest -m programs`` (or one file: ``pytest tests/programs/test_feat.py``).
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
INPUTS = Path(__file__).resolve().parent / "inputs"
QM_DATA = ROOT / "tests" / "data"
# A program stuck for longer than this is a failure, not a slow machine.
TIMEOUT = int(os.environ.get("LUCI_TEST_TIMEOUT", "1800"))


def _required() -> set[str]:
    value = os.environ.get("LUCI_REQUIRE_PROGRAMS", "").strip().lower()
    if not value:
        return set()
    if value == "all":
        from luci.registry import ENVIRONMENTS
        return {env.key for env in ENVIRONMENTS if env.available}
    return {part.strip() for part in value.split(",") if part.strip()}


def require_env(key: str) -> None:
    """Skip the test when the environment is missing, or fail if CI requires it."""
    from luci.envs.manager import EnvManager
    manager = EnvManager()
    if manager.is_installed(key):
        return
    message = (f"the '{key}' environment is not installed in {manager.home} "
               f"(install it with: luci env install {key})")
    if key in _required():
        pytest.fail(message)
    pytest.skip(message)


class Run:
    """A finished ``luci`` command: exit code and everything it printed."""

    def __init__(self, completed: subprocess.CompletedProcess, cwd: Path):
        self.code = completed.returncode
        self.output = completed.stdout
        self.cwd = cwd

    def tail(self, lines: int = 60) -> str:
        return "\n".join(self.output.splitlines()[-lines:])

    def ok(self) -> "Run":
        assert self.code == 0, f"luci exited with {self.code}:\n{self.tail()}"
        return self

    def output_folder(self) -> Path:
        """The folder LUCI announced with '[LUCI] Output folder: ...'."""
        for line in self.output.splitlines():
            if line.startswith("[LUCI] Output folder: "):
                return Path(line.split(": ", 1)[1].strip())
        raise AssertionError("LUCI did not print its output folder:\n" + self.tail())


# ----------------------------------------------------------------------------- fixtures
# Imported by every test module (from program_helpers import luci, work).
@pytest.fixture
def work(tmp_path) -> Path:
    """A scratch copy of the test inputs (the programs never touch the originals)."""
    target = tmp_path / "work"
    shutil.copytree(INPUTS, target)
    qm = target / "qm_outputs"
    qm.mkdir()
    for name in ("methane_gaussian.log", "hcn_triplet_gaussian.out", "da_endo_orca.out"):
        shutil.copy2(QM_DATA / name, qm / name)
    return target


@pytest.fixture
def luci():
    """Run ``luci ...`` in a folder: ``luci(work, "struct", "--backend", ...)``."""
    def run(cwd: Path, *args: str, timeout: int = TIMEOUT) -> Run:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        env.setdefault("OMP_NUM_THREADS", "1")
        env["PYTHONIOENCODING"] = "utf-8"
        completed = subprocess.run([sys.executable, "-m", "luci", *args], cwd=cwd, env=env,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                   errors="replace", timeout=timeout)
        return Run(completed, cwd)
    return run



# ----------------------------------------------------------------------------- readers
def sdf_records(path: Path) -> list[list[str]]:
    """The records of an SDF file, each as its lines."""
    records, current = [], []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip() == "$$$$":
            records.append(current)
            current = []
        else:
            current.append(line)
    if any(line.strip() for line in current):
        records.append(current)
    return records


def sdf_atom_count(record: list[str]) -> int:
    return int(record[3][:3])


def sdf_property(record: list[str], name: str) -> str | None:
    for index, line in enumerate(record):
        if line.startswith(">") and f"<{name}>" in line and index + 1 < len(record):
            return record[index + 1].strip()
    return None


def xyz_frames(path: Path) -> list[tuple[str, list[str]]]:
    """(comment, atom lines) of every frame of a (multi-)XYZ file."""
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    frames, index = [], 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        count = int(lines[index].split()[0])
        frames.append((lines[index + 1], lines[index + 2:index + 2 + count]))
        index += 2 + count
    return frames


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def luci_data(folder: Path) -> str:
    """The LUCI_data.dat of a layer folder."""
    data = folder / "LUCI_data.dat"
    assert data.is_file(), f"no LUCI_data.dat in {folder}"
    return data.read_text(encoding="utf-8")
