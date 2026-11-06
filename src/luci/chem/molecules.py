"""LUCI's one way of giving molecules to a program.

Every program that starts from SMILES receives them the same way:

* a CSV file with a ``smiles`` column and a ``code_name`` column (any other
  column, such as ``charge`` or ``mult``, is kept), or
* one SMILES typed in, with an optional name.

LUCI reads the file, checks what can be checked without chemistry software
(the columns, empty cells, names that would break file names, repeated
names) and writes the file the program wants (:func:`write_native`): AQME
gets ``SMILES,code_name``, ThermoMLIP ``id,smiles`` and so on. The SMILES
themselves are passed on as written. The ``code_name`` becomes the name of
each molecule's output files in every program, so results can be followed
from one layer to the next.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable

from .issues import LEVEL_ORDER, Issue, worst
from .table import Table, read_table, write_table

SMILES_COLUMN = "smiles"
NAME_COLUMN = "code_name"
# Column titles people use for the same thing; LUCI suggests renaming them.
NAME_ALIASES = ("name", "names", "id", "mol_id", "molecule", "molecule_name", "compound",
                "compound_name", "identifier", "label", "code", "title", "codename", "code-name")
SMILES_ALIASES = ("smi", "canonical_smiles", "isomeric_smiles", "smiles_string", "structure",
                  "molecule_smiles", "smile", "smiles_code")
FORBIDDEN_NAME_CHARS = '<>:"/\\|?*'
WINDOWS_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
                    *(f"lpt{i}" for i in range(1, 10))}
LONG_NAME = 80
DEFAULT_NAME = "molecule"


@dataclass
class MoleculeRecord:
    """One molecule: where it came from, its names, its SMILES and its problems."""

    line: int                      # line of the CSV (0 when typed in)
    code_name: str                 # as written by the user
    name: str                      # the name used for files (spaces replaced)
    smiles: str
    extra: dict[str, str] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)

    @property
    def status(self) -> str:
        return worst(self.issues)

    @property
    def ok(self) -> bool:
        return self.status != "error"

    def where(self) -> str:
        return f"line {self.line}" if self.line else "the typed SMILES"


@dataclass
class MoleculeSet:
    """The molecules of one input, with file-level problems kept apart."""

    source: Path | None = None
    records: list[MoleculeRecord] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    extra_columns: list[str] = field(default_factory=list)
    table: Table | None = None

    @property
    def file_ok(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)

    @property
    def ok(self) -> bool:
        return self.file_ok and all(record.ok for record in self.records) and bool(self.records)

    def valid(self) -> list[MoleculeRecord]:
        return [record for record in self.records if record.ok]

    def counts(self) -> dict[str, int]:
        counts = {"total": len(self.records), "ok": 0, "info": 0, "warning": 0, "error": 0}
        for record in self.records:
            counts[record.status] += 1
        return counts

    def summary(self) -> str:
        if not self.file_ok:
            return next(issue.message for issue in self.issues if issue.level == "error")
        counts = self.counts()
        total = counts["total"]
        if not total:
            return "No molecules."
        parts = [f"{total} molecule{'s' if total != 1 else ''}"]
        good = counts["ok"] + counts["info"]
        if counts["error"] or counts["warning"]:
            parts.append(f"{good} OK")
        if counts["warning"]:
            parts.append(f"{counts['warning']} with warnings")
        if counts["error"]:
            parts.append(f"{counts['error']} with errors")
        if not counts["error"] and not counts["warning"]:
            parts.append("all OK")
        return ", ".join(parts) + "."


# ------------------------------------------------------------------- names
def name_issues(name: str) -> tuple[str, list[Issue]]:
    """The file-safe version of a code_name and what is wrong with it."""
    issues: list[Issue] = []
    text = name.strip()
    if not text:
        issues.append(Issue("error", "name", "The code_name is empty.",
                            "Every molecule needs a code_name: it names its output files."))
        return "", issues
    safe = text
    if re.search(r"\s", text):
        safe = re.sub(r"\s+", "_", text)
        issues.append(Issue("warning", "name",
                            f"The code_name '{text}' contains spaces; LUCI uses '{safe}' instead.",
                            "Spaces in file names break several programs."))
    bad = sorted({char for char in text if char in FORBIDDEN_NAME_CHARS or ord(char) < 32})
    if bad:
        shown = " ".join(repr(char)[1:-1] for char in bad)
        issues.append(Issue("error", "name",
                            f"The code_name '{text}' contains {shown}, which cannot be used in file "
                            "names.", "Use letters, numbers, - and _ only."))
    if safe.lower().split(".")[0] in WINDOWS_RESERVED:
        issues.append(Issue("error", "name", f"'{text}' is a reserved name on Windows.",
                            "Choose another code_name (for example add a number)."))
    if safe.endswith("."):
        issues.append(Issue("error", "name", f"The code_name '{text}' ends with a dot.",
                            "Windows drops trailing dots from file names; remove it."))
    if any(ord(char) > 126 for char in safe):
        issues.append(Issue("warning", "name",
                            f"The code_name '{text}' has accented or special letters.",
                            "xTB, CREST and some Windows tools fail on them; prefer plain letters."))
    if safe.startswith("-"):
        issues.append(Issue("warning", "name", f"The code_name '{text}' starts with '-'.",
                            "Programs may read it as an option; start it with a letter."))
    if len(safe) > LONG_NAME:
        issues.append(Issue("warning", "name",
                            f"The code_name '{text[:20]}...' is {len(safe)} characters long.",
                            "Long names can exceed Windows' path limit; shorten it."))
    return safe, issues


def _missing_column_issue(table: Table, wanted: str, aliases: Iterable[str]) -> Issue:
    alias = table.column(*aliases)
    if alias is not None:
        title = table.header[alias]
        return Issue("error", "column", f"There is no '{wanted}' column.",
                     f"Rename the column '{title}' to {wanted}.")
    shown = ", ".join(f"'{title}'" for title in table.header if title) or "none"
    return Issue("error", "column", f"There is no '{wanted}' column (columns found: {shown}).",
                 "The molecule CSV needs a header with the columns smiles and code_name.")


# ------------------------------------------------------------------- reading
def read_molecules(path: str | Path) -> MoleculeSet:
    """Read and check a molecule CSV (smiles + code_name)."""
    table = read_table(path, what="molecule CSV")
    molset = MoleculeSet(source=table.path, issues=list(table.issues), table=table)
    if not table.ok:
        return molset
    smiles_index = table.column(SMILES_COLUMN)
    name_index = table.column(NAME_COLUMN)
    if smiles_index is None:
        molset.issues.append(_missing_column_issue(table, SMILES_COLUMN, SMILES_ALIASES))
    if name_index is None:
        molset.issues.append(_missing_column_issue(table, NAME_COLUMN, NAME_ALIASES))
    if smiles_index is None or name_index is None:
        return molset
    used = {smiles_index, name_index}
    seen_titles: set[str] = set()
    for index, title in enumerate(table.header):
        key = title.strip().lower()
        if index not in used and title and key not in seen_titles:
            molset.extra_columns.append(title)
        seen_titles.add(key)
    extra_positions = [table.header.index(title) for title in molset.extra_columns]
    for line, row in zip(table.lines, table.rows):
        cells = row + [""] * (len(table.header) - len(row))
        record = _record(line, cells[name_index], cells[smiles_index])
        record.extra = {table.header[i]: cells[i] for i in extra_positions}
        molset.records.append(record)
    _check_duplicates(molset.records)
    for record in molset.records:
        record.issues.sort(key=lambda issue: LEVEL_ORDER[issue.level])
    return molset


def _record(line: int, code_name: str, smiles: str) -> MoleculeRecord:
    safe, issues = name_issues(code_name)
    smiles = (smiles or "").strip()
    if not smiles:
        issues.append(Issue("error", "smiles", "The smiles cell is empty.",
                            "Write the molecule's SMILES, or delete the row."))
    return MoleculeRecord(line=line, code_name=code_name.strip(), name=safe, smiles=smiles,
                          issues=issues)


def _check_duplicates(records: list[MoleculeRecord]) -> None:
    names: dict[str, MoleculeRecord] = {}
    for record in records:
        key = record.name.lower()  # Windows file names ignore case
        if not key:
            continue
        if key in names:
            first = names[key]
            same = (f"'{first.code_name}'" if first.code_name == first.name
                    else f"'{first.code_name}' (used as '{first.name}')")
            record.issues.append(Issue(
                "error", "duplicate_name",
                f"The code_name '{record.code_name}' gives the same file names as {same} on "
                f"{first.where()}.",
                "Each molecule needs its own code_name, or their output files overwrite each other."))
        else:
            names[key] = record


def single_molecule(smiles: str, code_name: str = "") -> MoleculeSet:
    """One typed SMILES. Without a name, the output files are called 'molecule'."""
    name = code_name.strip()
    note: list[Issue] = []
    if not name:
        name = DEFAULT_NAME
        note.append(Issue("info", "name", f"No code_name given: the output files are called '{name}'."))
    record = _record(0, name, smiles)
    record.issues = note + record.issues
    record.issues.sort(key=lambda issue: LEVEL_ORDER[issue.level])
    return MoleculeSet(records=[record])


# ------------------------------------------------------------------- writing
def write_native(molset: MoleculeSet, path: Path, columns: tuple[tuple[str, str], ...],
                 keep_extra: bool = True, skip_invalid: bool = False) -> tuple[Path, int]:
    """Write the molecules in a program's own CSV layout; returns (path, rows written).

    ``columns`` maps LUCI fields to the program's headers, in order:
    (("smiles", "SMILES"), ("code_name", "code_name")) for AQME,
    (("code_name", "id"), ("smiles", "smiles")) for ThermoMLIP.
    Extra columns whose name starts with "smiles" are left out: programs such
    as AQME treat every smiles* column as more molecules.
    """
    records = molset.valid() if skip_invalid else molset.records
    native_titles = {native.lower() for _, native in columns}
    extras = [title for title in molset.extra_columns
              if keep_extra and title.lower() not in native_titles
              and not title.strip().lower().startswith("smiles")]
    header = [native for _, native in columns] + extras
    rows = []
    for record in records:
        fields = {"smiles": record.smiles, "code_name": record.name}
        rows.append([fields[luci] for luci, _ in columns] + [record.extra.get(t, "") for t in extras])
    return write_table(path, header, rows), len(rows)


def dropped_columns(molset: MoleculeSet, columns: tuple[tuple[str, str], ...],
                    keep_extra: bool = True) -> list[str]:
    """Extra columns :func:`write_native` leaves out, to tell the user."""
    native_titles = {native.lower() for _, native in columns}
    return [title for title in molset.extra_columns
            if title.lower() not in native_titles
            and (not keep_extra or title.strip().lower().startswith("smiles"))]


def format_report(molset: MoleculeSet, limit: int = 25, levels=("error", "warning")) -> list[str]:
    """Lines for the console: each problem with its fix."""
    lines = []
    for issue in molset.issues:
        if issue.level in levels or issue.level == "error":
            lines.append(f"{issue.level.upper()}: {issue.text()}")
    shown = 0
    for record in molset.records:
        for issue in record.issues:
            if issue.level not in levels:
                continue
            if shown == limit:
                lines.append("... (more problems not shown)")
                return lines
            label = f"{record.where()}, {record.code_name or '?'}"
            lines.append(f"{issue.level.upper()} [{label}] {issue.message}"
                         + (f" -> {issue.hint}" if issue.hint else ""))
            shown += 1
    return lines
