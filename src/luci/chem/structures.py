"""3D structures: LUCI always hands programs SDF files.

A folder of structures may hold SDF, MOL, MOL2, XYZ, PDB, Gaussian inputs
(.gjf/.com) and finished Gaussian or ORCA outputs (.log/.out, last
geometry). LUCI itself has no chemistry library: it reads what plain text
parsing can (which files there are, Gaussian/ORCA geometries with their
charge and multiplicity, the comment line of an XYZ file) and the conversion
to SDF is done by Open Babel inside the program's own environment
(``runners/to_sdf.py``), only for files that are not SDF already and only
when they changed since the last conversion.

Converted SDF records carry the ``Real charge`` and ``Mult`` properties AQME
reads whenever the file states them.

Safety: LUCI only ever writes or deletes files inside its work folder, and
only the ones listed in that folder's manifest (``.luci-structures.json``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

from .issues import Issue

SDF_SUFFIXES = {".sdf", ".sd"}
# Read as text by LUCI, handed to Open Babel as XYZ.
PARSED = {".gjf", ".com", ".log", ".out"}
# Handed to Open Babel as they are.
OPENBABEL_FORMATS = {".xyz": "xyz", ".mol": "mol", ".mol2": "mol2", ".pdb": "pdb", ".ent": "pdb"}
CONVERTIBLE = PARSED | set(OPENBABEL_FORMATS)
STRUCTURE_SUFFIXES = SDF_SUFFIXES | CONVERTIBLE
# When two files share a name (methane.gjf and methane.log), the first in this
# order is used: an SDF, then a finished calculation, then plain geometries.
PREFERENCE = [".sdf", ".sd", ".log", ".out", ".xyz", ".mol2", ".mol", ".pdb", ".ent", ".gjf", ".com"]
SUFFIX_LIST = "SDF, MOL, MOL2, XYZ, PDB, Gaussian .gjf/.com or Gaussian/ORCA .log/.out"
MANIFEST = ".luci-structures.json"
# Bump when the conversion changes, so earlier SDF files are made again.
CONVERTER_VERSION = 1

ELEMENTS = (
    "X H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As "
    "Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd "
    "Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am "
    "Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og"
).split()
SYMBOLS = {symbol.lower(): symbol for symbol in ELEMENTS[1:]}


class StructureError(ValueError):
    """A file that holds no usable structure; the message says why."""


@dataclass
class Geometry:
    """Atoms and coordinates read from a text file."""

    symbols: list[str]
    coords: list[tuple[float, float, float]]
    charge: int | None = None
    mult: int | None = None

    def xyz(self, title: str = "") -> str:
        lines = [str(len(self.symbols)), title]
        lines += [f"{s} {x:.6f} {y:.6f} {z:.6f}" for s, (x, y, z) in zip(self.symbols, self.coords)]
        return "\n".join(lines) + "\n"


@dataclass
class StructureFile:
    """One file of the folder and what LUCI will do with it."""

    source: Path
    action: str = "use"            # use (already SDF), convert, skip
    fmt: str = ""                  # Open Babel input format when converting
    charge: int | None = None
    mult: int | None = None
    text: str = ""                 # XYZ text LUCI wrote from a .gjf/.log/.out
    target: Path | None = None
    structures: int = 0
    issues: list[Issue] = field(default_factory=list)
    converted: bool = False        # converted in this run (not reused)

    @property
    def ok(self) -> bool:
        return self.action != "skip" and not any(i.level == "error" for i in self.issues)

    def label(self) -> str:
        if not self.ok:
            return "cannot be used"
        if self.action == "use":
            return "SDF"
        return f"{self.source.suffix.lstrip('.').upper()} -> SDF"


@dataclass
class FolderResult:
    """A folder of structures made ready (or planned) for a program."""

    folder: Path                      # where the SDF files the program reads are
    files: list[StructureFile] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (not any(i.level == "error" for i in self.issues)
                and any(item.ok for item in self.files))

    def to_convert(self) -> list[StructureFile]:
        return [item for item in self.files if item.ok and item.action == "convert"]

    def counts(self) -> dict[str, int]:
        return {
            "files": len(self.files),
            "sdf": sum(1 for f in self.files if f.ok and f.action == "use"),
            "convert": len(self.to_convert()),
            "failed": sum(1 for f in self.files if not f.ok),
        }

    def summary(self) -> str:
        if not self.files:
            return next((i.message for i in self.issues if i.level == "error"), "No structures.")
        counts = self.counts()
        parts = [f"{counts['files']} file{'s' if counts['files'] != 1 else ''}"]
        if counts["sdf"]:
            parts.append(f"{counts['sdf']} SDF")
        if counts["convert"]:
            parts.append(f"{counts['convert']} to convert to SDF")
        if counts["failed"]:
            parts.append(f"{counts['failed']} cannot be used")
        return ", ".join(parts) + "."


# ------------------------------------------------------------------ text readers
def element(token: str) -> str:
    """'C', 'c', '6', 'C1', 'Cl(Fragment=1)' -> the element symbol."""
    token = token.strip()
    if token.isdigit():
        number = int(token)
        if 0 < number < len(ELEMENTS):
            return ELEMENTS[number]
        raise StructureError(f"'{token}' is not an atomic number.")
    match = re.match(r"([A-Za-z]{1,2})", token)
    if match:
        letters = match.group(1).lower()
        if letters in SYMBOLS:
            return SYMBOLS[letters]
        if letters[0] in SYMBOLS:
            return SYMBOLS[letters[0]]
    raise StructureError(f"'{token}' is not an element.")


def _float(token: str) -> float:
    return float(token.replace("D", "E").replace("d", "e"))


def charge_mult_from_comment(comment: str) -> tuple[int | None, int | None]:
    """'charge=1 mult=2' (also 'charge: -1', 'multiplicity=3', 'uhf=1') in an XYZ comment."""
    charge = re.search(r"\b(?:charge|chrg)\s*[=:]\s*([+-]?\d+)\b", comment, re.I)
    mult = re.search(r"\b(?:multiplicity|mult)\s*[=:]\s*(\d+)\b", comment, re.I)
    uhf = re.search(r"\buhf\s*[=:]\s*(\d+)\b", comment, re.I)
    value = int(mult.group(1)) if mult else (int(uhf.group(1)) + 1 if uhf else None)
    if value is not None and value < 1:
        value = None
    return (int(charge.group(1)) if charge else None), value


def read_gaussian_input(text: str) -> Geometry:
    """Cartesian coordinates, charge and multiplicity of a .gjf/.com file."""
    lines = text.replace("\r", "").splitlines()
    index = 0
    while index < len(lines) and not lines[index].lstrip().startswith("#"):
        index += 1
    if index == len(lines):
        raise StructureError("No route line (starting with #) was found.")
    while index < len(lines) and lines[index].strip():  # route
        index += 1
    index += 1
    while index < len(lines) and lines[index].strip():  # title
        index += 1
    index += 1
    if index >= len(lines):
        raise StructureError("No charge and multiplicity line was found.")
    numbers = lines[index].replace(",", " ").split()
    try:
        charge, mult = int(numbers[0]), int(numbers[1])
    except (ValueError, IndexError):
        raise StructureError("The line after the title should be 'charge multiplicity'.") from None
    symbols, coords = [], []
    for line in lines[index + 1:]:
        if not line.strip():
            break
        parts = line.replace(",", " ").split()
        label = parts[0]
        if "bq" in label.lower().replace("(", "-").split("-"):
            continue  # ghost atoms (Bq, H-Bq) carry no nucleus
        values = []
        for token in parts[1:]:
            try:
                values.append(_float(token))
            except ValueError:
                continue
        if len(parts) >= 5 and parts[1] in ("0", "-1", "-2", "-3") and len(values) >= 4:
            values = values[1:]  # freeze flag: "C 0 x y z"
        if len(values) < 3:
            raise StructureError("The coordinates are a Z-matrix; LUCI needs Cartesian coordinates.")
        symbols.append(element(label.split("(")[0].split("-")[0]))
        coords.append((values[0], values[1], values[2]))
    if not symbols:
        raise StructureError("No atoms were found after the charge and multiplicity line.")
    return Geometry(symbols, coords, charge, mult)


def read_qm_output(text: str) -> tuple[Geometry, list[Issue]]:
    """Last geometry of a Gaussian or ORCA output, with the charge and spin of that job."""
    issues: list[Issue] = []
    head = text[:30000]
    if "Gaussian, Inc" in head or "Entering Gaussian System" in head:
        geometry = _gaussian_geometry(text)
        if "Normal termination" not in text[-3000:]:
            issues.append(Issue("warning", "unfinished",
                                "The calculation did not finish normally; its last geometry is used."))
        return geometry, issues
    if "O   R   C   A" in head or "ORCA TERMINATED" in text[-5000:]:
        geometry = _orca_geometry(text)
        if "ORCA TERMINATED NORMALLY" not in text[-5000:]:
            issues.append(Issue("warning", "unfinished",
                                "The calculation did not finish normally; its last geometry is used."))
        return geometry, issues
    if "x T B" in head or "xtb version" in head:
        raise StructureError("xTB output files have no coordinates; use xtbopt.xyz or xtbopt.sdf.")
    raise StructureError("Not a Gaussian or ORCA output.")


def _gaussian_geometry(text: str) -> Geometry:
    blocks = list(re.finditer(r"Standard orientation:", text)) or list(re.finditer(r"Input orientation:", text))
    if not blocks:
        raise StructureError("No geometry (Standard or Input orientation) in this Gaussian output.")
    last = blocks[-1]
    lines = text[last.end():].splitlines()
    symbols, coords = [], []
    for line in lines[5:]:
        if line.strip().startswith("---"):
            break
        parts = line.split()
        if len(parts) < 6:
            break
        number = int(parts[1])
        if number <= 0:
            continue  # ghost atoms and dummies
        symbols.append(ELEMENTS[number])
        coords.append((_float(parts[3]), _float(parts[4]), _float(parts[5])))
    # The charge of the job that wrote this geometry (Link1 jobs may change it).
    # Within a job the first line is the whole system: fragment (counterpoise)
    # and ONIOM layer lines follow it.
    starts = [m.start() for m in re.finditer(r"Entering Gaussian System", text[:last.start()])]
    job = text[(starts[-1] if starts else 0):last.start()]
    found = re.search(r"Charge\s*=\s*(-?\d+)\s+Multiplicity\s*=\s*(\d+)", job)
    charge, mult = (int(found.group(1)), int(found.group(2))) if found else (None, None)
    if not symbols:
        raise StructureError("The last Gaussian geometry block is empty.")
    return Geometry(symbols, coords, charge, mult)


def _orca_geometry(text: str) -> Geometry:
    blocks = list(re.finditer(r"CARTESIAN COORDINATES \(ANGSTROEM\)", text))
    if not blocks:
        raise StructureError("No CARTESIAN COORDINATES (ANGSTROEM) block in this ORCA output.")
    last = blocks[-1]
    lines = text[last.end():].splitlines()
    symbols, coords = [], []
    for line in lines[2:]:
        parts = line.split()
        if len(parts) != 4:
            break
        if parts[0].endswith(">") or parts[0].lower().startswith("dummy"):
            continue  # ORCA ghost/point-charge markers
        symbols.append(element(parts[0]))
        coords.append((_float(parts[1]), _float(parts[2]), _float(parts[3])))
    before = text[:last.start()] or text
    charges = list(re.finditer(r"Total Charge\s+Charge\s+\.+\s+(-?\d+)", before))
    mults = list(re.finditer(r"Multiplicity\s+Mult\s+\.+\s+(\d+)", before))
    if not symbols:
        raise StructureError("The last ORCA geometry block is empty.")
    return Geometry(symbols, coords, int(charges[-1].group(1)) if charges else None,
                    int(mults[-1].group(1)) if mults else None)


def xyz_comment(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            handle.readline()
            return handle.readline()
    except OSError:
        return ""


def check_xyz(path: Path) -> None:
    """The first frame of an XYZ file: an atom count, a comment, then 'element x y z' lines."""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        lines = handle.read().replace("\r", "").split("\n")
    try:
        count = int(lines[0].split()[0])
    except (ValueError, IndexError):
        raise StructureError("The first line should be the number of atoms.") from None
    atoms = [line for line in lines[2:2 + count]]
    if len(atoms) < count or any(not line.strip() for line in atoms):
        raise StructureError(f"The file says {count} atoms but has fewer.")
    for offset, line in enumerate(atoms, start=3):
        parts = line.split()
        if len(parts) < 4:
            raise StructureError(f"Line {offset} is not 'element x y z'.")
        token = parts[0]
        if not token.isdigit() and token.lower() not in SYMBOLS:
            raise StructureError(f"Line {offset}: '{token}' is not an element.")
        try:
            [_float(value) for value in parts[1:4]]
        except ValueError:
            raise StructureError(f"Line {offset}: the coordinates are not numbers.") from None


def sdf_dimension(path: Path) -> tuple[int, bool]:
    """(records, is a 2D drawing) of an SDF/MOL file, read as text."""
    records, flat = 0, False
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().replace("\r", "").split("\n")
    except OSError:
        return 0, False
    index = 0
    first = True
    while index + 3 < len(lines):
        header = lines[index + 1]
        counts = lines[index + 3]
        try:
            atoms = int(counts[0:3])
        except ValueError:
            break
        if first:
            coords = lines[index + 4:index + 4 + atoms]
            all_zero = all(abs(_float(line[20:30])) < 1e-4 for line in coords if len(line) >= 30)
            flat = atoms > 3 and header[20:22] == "2D" and all_zero
            first = False
        records += 1
        try:
            index = lines.index("$$$$", index) + 1
        except ValueError:
            break
    if records == 0 and any(line.strip() == "M  END" for line in lines):
        records = 1
    return records, flat


# ------------------------------------------------------------------ planning
def structure_files(folder: Path) -> list[Path]:
    return sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in STRUCTURE_SUFFIXES
                   and not p.name.startswith(".")), key=lambda p: p.name.lower())


def plan_file(path: Path) -> StructureFile:
    """What LUCI will do with one file (nothing is converted here)."""
    item = StructureFile(source=path)
    suffix = path.suffix.lower()
    try:
        if path.stat().st_size == 0:
            raise StructureError("The file is empty.")
        if suffix in SDF_SUFFIXES or suffix == ".mol":
            records, flat = sdf_dimension(path)
            if records == 0:
                raise StructureError("No structure could be read from this file.")
            if flat:
                raise StructureError("The structure is flat (a 2D drawing, all z = 0), not a 3D "
                                     "geometry.")
            item.structures = records
            item.action = "use" if suffix == ".sdf" else "convert"
            item.fmt = "sdf" if suffix == ".sd" else "mol"
        elif suffix in (".gjf", ".com"):
            geometry = read_gaussian_input(path.read_text(encoding="utf-8", errors="replace"))
            _from_geometry(item, geometry)
        elif suffix in (".log", ".out"):
            geometry, item.issues = read_qm_output(path.read_text(encoding="utf-8", errors="replace"))
            _from_geometry(item, geometry)
        else:
            item.action = "convert"
            item.fmt = OPENBABEL_FORMATS[suffix]
            if suffix == ".xyz":
                check_xyz(path)
                item.charge, item.mult = charge_mult_from_comment(xyz_comment(path))
    except StructureError as exc:
        item.action = "skip"
        item.issues.append(Issue("error", "unreadable", str(exc)))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        item.action = "skip"
        item.issues.append(Issue("error", "unreadable", f"Cannot read the file: {exc}."))
    if item.action == "convert" and item.charge is None and item.fmt == "xyz":
        item.issues.append(Issue("info", "charge",
                                 "No charge in the XYZ comment line; programs will assume a neutral "
                                 "closed-shell molecule.", "Write charge=1 mult=2 (for example) in "
                                 "the comment line if it is charged or a radical."))
    return item


def _from_geometry(item: StructureFile, geometry: Geometry) -> None:
    item.action = "convert"
    item.fmt = "xyz"
    item.text = geometry.xyz(item.source.stem)
    item.charge, item.mult = geometry.charge, geometry.mult
    item.structures = 1


def plan_folder(folder: str | Path) -> FolderResult:
    """Look at a folder of structures without converting anything (fast, no Open Babel)."""
    folder = Path(folder).expanduser()
    result = FolderResult(folder=folder)
    if not str(folder).strip() or not folder.is_dir():
        result.issues.append(Issue("error", "missing",
                                   f"{folder} is not a folder." if str(folder).strip()
                                   else "No folder of structures chosen."))
        return result
    files = structure_files(folder)
    if not files:
        others = sorted({p.suffix.lower() for p in folder.iterdir() if p.is_file() and p.suffix})
        found = f" (found: {', '.join(others[:6])})" if others else ""
        result.issues.append(Issue("error", "empty", f"No structure files in {folder.name}{found}.",
                                   f"LUCI reads {SUFFIX_LIST}."))
        return result
    rank = {suffix: position for position, suffix in enumerate(PREFERENCE)}
    chosen: dict[str, Path] = {}
    for path in sorted(files, key=lambda p: (p.stem.lower(), rank.get(p.suffix.lower(), 99))):
        key = path.stem.lower()
        if key in chosen:
            result.issues.append(Issue("warning", "same_name",
                                       f"{path.name} has the same name as {chosen[key].name}; only "
                                       f"{chosen[key].name} is used."))
            continue
        chosen[key] = path
    result.files = [plan_file(path) for path in sorted(chosen.values(), key=lambda p: p.name.lower())]
    return result


# ------------------------------------------------------------------ manifest
def _fingerprint(path: Path) -> dict:
    stat = path.stat()
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        digest.update(handle.read(1 << 20))
    return {"source": str(path.resolve()), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns,
            "head": digest.hexdigest(), "version": CONVERTER_VERSION}


def _load_manifest(work_dir: Path) -> dict:
    try:
        data = json.loads((work_dir / MANIFEST).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_manifest(work_dir: Path, manifest: dict) -> None:
    partial = work_dir / (MANIFEST + ".partial")
    partial.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    os.replace(partial, work_dir / MANIFEST)


def work_folder_for(folder: Path, work_dir: Path) -> Path:
    """Never convert into the user's own folder: a separate subfolder instead."""
    if work_dir.resolve() == folder.resolve():
        return folder / "input_sdf"
    return work_dir


def prepare_folder(folder: str | Path, work_dir: Path, convert=None, *, dry_run: bool = False,
                   skip_invalid: bool = False) -> FolderResult:
    """Make a folder of structures ready: one SDF file per structure file.

    A folder holding only usable SDF files is used as it is. Otherwise the
    SDF files go to ``work_dir``: usable SDF files are copied, the rest are
    converted by ``convert(jobs)`` (Open Babel in the program's environment,
    see :func:`luci.inputs.openbabel_converter`), and files unchanged since
    the last run are reused. With ``skip_invalid`` the files that cannot be
    used are simply not handed over. Nothing is written with ``dry_run``.
    """
    result = plan_folder(folder)
    if not result.files:
        return result
    source = Path(folder).expanduser()
    unusable = [item for item in result.files if not item.ok]
    if not result.to_convert() and not unusable:
        for item in result.files:
            item.target = item.source
        return result  # every file is SDF already: nothing to copy or convert
    if unusable and not skip_invalid:
        return result
    work_dir = work_folder_for(source, work_dir)
    result.folder = work_dir
    if dry_run:
        for item in result.files:
            if item.ok:
                item.target = work_dir / (item.source.stem + ".sdf")
        return result
    work_dir.mkdir(parents=True, exist_ok=True)
    with _FolderLock(work_dir):
        return _convert_into(result, work_dir, convert)


class _FolderLock:
    """One LUCI run at a time converts into a work folder (two pages may share one)."""

    STALE = 3600

    def __init__(self, folder: Path, timeout: float = 600):
        self.path = folder / ".luci-structures.lock"
        self.timeout = timeout

    def __enter__(self):
        import time
        start = time.monotonic()
        while True:
            try:
                handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(handle, str(os.getpid()).encode())
                os.close(handle)
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > self.STALE:
                        self.path.unlink()  # left by a run that was killed
                        continue
                except OSError:
                    continue
                if time.monotonic() - start > self.timeout:
                    raise StructureError(f"Another LUCI run is converting structures in {self.path.parent}; "
                                         "wait for it to finish.") from None
                time.sleep(0.2)

    def __exit__(self, *_exc):
        try:
            self.path.unlink()
        except OSError:
            pass


def _convert_into(result: FolderResult, work_dir: Path, convert) -> FolderResult:
    manifest = _load_manifest(work_dir)
    expected: dict[str, dict] = {}
    jobs = []
    for item in result.files:
        if not item.ok:
            continue
        target = work_dir / (item.source.stem + ".sdf")
        if target.exists() and target.name not in manifest:
            # Not LUCI's file: never overwrite it.
            item.issues.append(Issue("error", "exists",
                                     f"{target} exists and was not made by LUCI; it is left alone.",
                                     "Move it, or choose another output folder."))
            continue
        item.target = target
        fingerprint = _fingerprint(item.source)
        expected[target.name] = fingerprint
        previous = manifest.get(target.name, {})
        if target.exists() and {k: previous.get(k) for k in fingerprint} == fingerprint:
            item.issues += [Issue(**issue) for issue in previous.get("issues", [])
                            if not any(i.message == issue.get("message") for i in item.issues)]
            item.structures = previous.get("structures", item.structures)
            continue  # unchanged since the last run
        if item.action == "use":
            shutil.copy2(item.source, target)
            continue
        jobs.append(item)
    if jobs:
        if convert is None:
            raise StructureError("No converter available for these structures.")
        convert(jobs, work_dir)
        for item in jobs:
            item.converted = item.ok
            if item.ok:
                expected[item.target.name]["issues"] = [
                    {"level": i.level, "code": i.code, "message": i.message, "hint": i.hint}
                    for i in item.issues]
                expected[item.target.name]["structures"] = item.structures
    for item in result.files:
        if item.target is not None and item.target.name in expected and item.target.name in manifest \
                and "issues" not in expected[item.target.name]:
            expected[item.target.name]["issues"] = manifest[item.target.name].get("issues", [])
            expected[item.target.name]["structures"] = manifest[item.target.name].get("structures", 0)
    # Remove only LUCI's own files that are stale or broken.
    keep = {item.target.name for item in result.files if item.ok and item.target is not None}
    for name in list(manifest):
        if name not in keep:
            stale = work_dir / name
            try:
                if stale.is_file():
                    stale.unlink()
            except OSError:
                pass
    _save_manifest(work_dir, {name: data for name, data in expected.items() if name in keep})
    for item in result.files:
        if item.target is not None and not item.ok:
            item.target = None
    return result


def format_folder_report(result: FolderResult, limit: int = 25) -> list[str]:
    lines = [f"{i.level.upper()}: {i.text()}" for i in result.issues if i.level != "info"]
    shown = 0
    for item in result.files:
        for issue in item.issues:
            if issue.level == "info":
                continue
            if shown == limit:
                lines.append("... (more problems not shown)")
                return lines
            lines.append(f"{issue.level.upper()} [{item.source.name}] {issue.text()}")
            shown += 1
    return lines


# ------------------------------------------------------------------ outputs
def snapshot(folder: Path, patterns: tuple[str, ...]) -> dict[str, float]:
    """mtimes of the files matching ``patterns`` (taken before a run)."""
    found: dict[str, float] = {}
    if not folder.is_dir():
        return found
    for pattern in patterns:
        for path in folder.glob(pattern):
            if path.is_file():
                found[str(path)] = path.stat().st_mtime
    return found


def new_outputs(folder: Path, patterns: tuple[str, ...], before: dict[str, float]) -> list[StructureFile]:
    """Structures a run wrote (new or changed files) that need an SDF copy next to them."""
    items = []
    if not folder.is_dir():
        return items
    for pattern in patterns:
        for path in sorted(folder.glob(pattern)):
            if not path.is_file() or path.suffix.lower() not in CONVERTIBLE:
                continue
            if before.get(str(path)) == path.stat().st_mtime:
                continue
            target = path.with_suffix(".sdf")
            if target.exists():
                if str(target) in before:
                    continue  # an SDF that was there before the run is never overwritten
                if target.stat().st_mtime >= path.stat().st_mtime:
                    continue  # the program wrote its own SDF
            item = plan_file(path)
            if item.ok and item.action == "convert":
                item.target = target
                items.append(item)
    return items
