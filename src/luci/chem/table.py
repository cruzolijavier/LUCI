"""Reading the CSV files users hand to LUCI, whatever program wrote them.

Pure Python (no RDKit, no pandas): LUCI reads every input table itself so it
can explain problems in plain words *before* a program fails on them, and then
hands the program a clean, comma-separated UTF-8 copy.

Handled here: Excel workbooks saved with a .csv name, UTF-8 with or without
BOM, Windows-1252 files (Excel on Windows), comma / semicolon / tab
separators (Excel in Spanish writes ';'), blank lines and rows with the wrong
number of values.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
import io
from pathlib import Path

from .issues import Issue

# First bytes of files that are not text tables.
EXCEL_XLSX = b"PK\x03\x04"
EXCEL_XLS = b"\xd0\xcf\x11\xe0"
SAVE_AS_CSV = ("In Excel use File > Save As and choose \"CSV UTF-8 (Comma delimited)\".")
DELIMITER_NAMES = {",": "comma", ";": "semicolon", "\t": "tab"}


@dataclass
class Table:
    """A CSV read into memory: header, rows (as lists) and what was found on the way."""

    path: Path
    header: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    # The file line each row came from (1 is the header), for messages.
    lines: list[int] = field(default_factory=list)
    delimiter: str = ","
    encoding: str = "utf-8"
    issues: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)

    def column(self, *names: str) -> int | None:
        """Index of the first header matching one of ``names`` (case and spaces ignored)."""
        wanted = {_norm(name) for name in names}
        for index, title in enumerate(self.header):
            if _norm(title) in wanted:
                return index
        return None


def _norm(text: str) -> str:
    return text.strip().lower().replace(" ", "_")


def read_text(path: Path) -> tuple[str, str, list[Issue]]:
    """File contents as text, the encoding used, and problems found."""
    issues: list[Issue] = []
    raw = path.read_bytes()
    if raw.startswith(EXCEL_XLSX) or raw.startswith(EXCEL_XLS):
        issues.append(Issue("error", "excel",
                            f"{path.name} is an Excel workbook, not a CSV file.", SAVE_AS_CSV))
        return "", "", issues
    # Excel's "Unicode text" export is UTF-16, usually with a byte-order mark.
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        encoding = "utf-16"
    elif len(raw) > 3 and raw[1:2] == b"\x00" and raw[0:1] != b"\x00":
        encoding = "utf-16-le"
    else:
        encoding = "utf-8-sig"
    try:
        return raw.decode(encoding), encoding, issues
    except UnicodeDecodeError:
        pass
    try:
        text = raw.decode("cp1252")
        issues.append(Issue("info", "encoding",
                            f"{path.name} is not UTF-8; it was read as Windows-1252 (Excel's default "
                            "on Windows). LUCI gives the program a UTF-8 copy."))
        return text, "cp1252", issues
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
        issues.append(Issue("warning", "encoding",
                            f"{path.name} is not UTF-8 and some characters may be wrong.", SAVE_AS_CSV))
        return text, "latin-1", issues


def sniff_delimiter(text: str) -> str:
    """',' unless the header line clearly uses ';' or tabs."""
    first = next((line for line in text.splitlines() if line.strip()), "")
    counts = {d: first.count(d) for d in (",", ";", "\t")}
    best = max(counts, key=lambda d: counts[d])
    return best if counts[best] > 0 else ","


def read_table(path: str | Path, *, what: str = "file") -> Table:
    """Read a CSV and report problems instead of raising."""
    path = Path(path).expanduser()
    table = Table(path=path)
    if not str(path).strip() or str(path) == ".":
        table.issues.append(Issue("error", "missing", f"No {what} chosen."))
        return table
    if path.is_dir():
        table.issues.append(Issue("error", "missing", f"{path} is a folder; choose a CSV {what}."))
        return table
    if not path.is_file():
        table.issues.append(Issue("error", "missing", f"{path} does not exist."))
        return table
    try:
        text, encoding, issues = read_text(path)
    except OSError as exc:
        table.issues.append(Issue("error", "unreadable", f"Cannot read {path.name}: {exc.strerror or exc}."))
        return table
    table.issues += issues
    table.encoding = encoding
    if not table.ok:
        return table
    if path.suffix.lower() in (".xlsx", ".xls", ".ods"):
        table.issues.append(Issue("error", "excel", f"{path.name} is a spreadsheet, not a CSV file.",
                                  SAVE_AS_CSV))
        return table
    if not text.strip():
        table.issues.append(Issue("error", "empty", f"{path.name} is empty."))
        return table
    first_line = text.lstrip().split("\n", 1)[0].strip()
    if first_line.lower().startswith("sep=") and len(first_line) >= 5:
        # Excel's "sep=;" line names the separator; it is not the header.
        table.delimiter = first_line[4]
        text = text.lstrip().split("\n", 1)[1] if "\n" in text.lstrip() else ""
    else:
        table.delimiter = sniff_delimiter(text)
    if table.delimiter not in DELIMITER_NAMES:
        table.issues.append(Issue("error", "format", f"{path.name} uses '{table.delimiter}' to "
                                  "separate columns.", SAVE_AS_CSV))
        return table
    if table.delimiter != ",":
        table.issues.append(Issue(
            "info", "delimiter",
            f"{path.name} is {DELIMITER_NAMES[table.delimiter]}-separated; LUCI gives the program a "
            "comma-separated copy."))
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=table.delimiter)
    header_seen = False
    try:
        for line_number, row in enumerate(reader, start=1):
            if not any(cell.strip() for cell in row):
                continue
            if not header_seen:
                table.header = [cell.strip() for cell in row]
                header_seen = True
                continue
            table.rows.append([cell.strip() for cell in row])
            table.lines.append(reader.line_num)
    except csv.Error as exc:
        table.issues.append(Issue("error", "format", f"{path.name} is not a valid CSV file ({exc})."))
        return table
    _check_header(table)
    _check_widths(table)
    _check_quotes(table)
    return table


def _check_quotes(table: Table) -> None:
    """A quote opened and never closed swallows the following lines into one cell."""
    for line, row in zip(table.lines, table.rows):
        if any("\n" in cell or "\r" in cell for cell in row):
            table.issues.append(Issue(
                "error", "quote",
                f"A quote (\") opened before line {line} is never closed, so several lines were "
                "read as one.", "Remove the stray quote or close it, then save the CSV again."))
            return


def _check_header(table: Table) -> None:
    seen: dict[str, int] = {}
    for index, title in enumerate(table.header):
        if not title:
            table.issues.append(Issue("warning", "header",
                                      f"Column {index + 1} of the header has no name."))
            continue
        key = _norm(title)
        if key in seen:
            table.issues.append(Issue("warning", "header",
                                      f"The column '{title}' appears twice in the header; only the "
                                      "first one is used."))
        seen.setdefault(key, index)
    if not table.rows:
        table.issues.append(Issue("error", "empty", f"{table.path.name} has a header but no rows."))


def _check_widths(table: Table) -> None:
    width = len(table.header)
    odd = [(line, len(row)) for line, row in zip(table.lines, table.rows) if len(row) != width]
    if not odd:
        return
    shown = ", ".join(f"line {line} ({count} values)" for line, count in odd[:5])
    more = f" and {len(odd) - 5} more" if len(odd) > 5 else ""
    table.issues.append(Issue(
        "warning", "width",
        f"{len(odd)} row(s) do not have {width} values like the header: {shown}{more}.",
        "A comma inside a name splits it in two; put that value between quotes or remove the comma."))


def write_table(path: Path, header: list[str], rows: list[list[str]]) -> Path:
    """A clean copy for the program: comma-separated, UTF-8, quoted only when needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    with partial.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    partial.replace(path)
    return path
