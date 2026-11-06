"""Reading tools that run in a background thread: documentation, the user's files, environments."""

from __future__ import annotations

from pathlib import Path

from ..registry import PROGRAM_BY_KEY
from .tools import Tool, boolean, enum, integer, s

import itertools
import re

SECRET = re.compile(r"\b(sk-[A-Za-z0-9_\-]{8,}|hf_[A-Za-z0-9]{8,})")
MAX_SCAN = 200 * 1024 * 1024  # find_in_file reads at most this much of a file

TEXT_SUFFIXES = {".csv", ".txt", ".log", ".out", ".dat", ".xyz", ".sdf", ".mol", ".mol2", ".pdb", ".gjf", ".com",
                 ".json", ".md", ".inp", ".yaml", ".yml", ".toml", ".py", ".tsv", ".ini", ".cfg", ".sh", ".bat"}
MAX_READ = 6000


def program_details(program: str) -> str:
    from .knowledge import program_page
    spec = PROGRAM_BY_KEY.get(program)
    return program_page(spec) if spec else f"Unknown program '{program}'. Keys: {', '.join(PROGRAM_BY_KEY)}."


def _private(file: Path) -> bool:
    """Files that hold keys or tokens: never shown to the model."""
    from .config import BUNDLED_KEY_FILE, KEY_FILE, key_files
    if file.name.lower() in (KEY_FILE, BUNDLED_KEY_FILE, "settings.json", ".env") or file.suffix.lower() in (".pem", ".key"):
        return True
    try:
        resolved = file.resolve()
        return any(resolved == k.resolve() for k in key_files())
    except OSError:
        return True


def _hide(text: str) -> str:
    return SECRET.sub("[hidden]", text)


def _readable(path: str) -> tuple[Path | None, dict | None]:
    file = Path(path).expanduser()
    if not file.is_file():
        return None, {"error": f"{path} is not a file on this computer."}
    if _private(file):
        return None, {"error": "That file holds keys or tokens; the assistant does not read it."}
    if file.suffix.lower() not in TEXT_SUFFIXES:
        return None, {"error": f"{file.suffix or 'This file'} is not a text format LUCI reads "
                               f"({', '.join(sorted(TEXT_SUFFIXES))})."}
    return file, None


def read_file(path: str, part: str = "start", lines: int = 60) -> dict:
    """The start or the end of a text file (CSV, logs, structures...), never the whole of a big file."""
    file, error = _readable(path)
    if error:
        return error
    lines = max(1, min(int(lines or 60), 400))
    size = file.stat().st_size
    with file.open("r", encoding="utf-8", errors="replace") as handle:
        if part == "end":
            handle.seek(max(0, size - 200_000))
            rows = handle.read().splitlines()[-lines:]
        else:
            rows = []
            for row in handle:
                rows.append(row.rstrip("\n"))
                if len(rows) >= lines:
                    break
    text = _hide("\n".join(rows))
    return {"file": str(file), "size_bytes": size, "part": part,
            "text": text[-MAX_READ:] if part == "end" else text[:MAX_READ]}


def find_in_file(path: str, text: str, around: int = 2, limit: int = 30) -> dict:
    """Lines of a text file containing ``text`` (e.g. a code_name in CSEARCH_data.dat), read as a stream."""
    file, error = _readable(path)
    if error:
        return error
    needle = text.lower()
    hits, before, pending = [], [], []
    read = 0
    number = 0
    with file.open("r", encoding="utf-8", errors="replace") as handle:
        for number, row in enumerate(handle, start=1):
            read += len(row)
            row = row.rstrip("\n")
            for hit in pending:
                if hit["after"] > 0:
                    hit["lines"].append(row)
                    hit["after"] -= 1
            if needle in row.lower() and len(hits) < limit:
                hit = {"line": number, "lines": before[-around:] + [row], "after": around}
                hits.append(hit)
                pending.append(hit)
            pending = [h for h in pending if h["after"] > 0]
            before.append(row)
            before = before[-around:]
            if read > MAX_SCAN or (len(hits) >= limit and not pending):
                break
    return {"file": str(file), "matches": [{"line": h["line"], "text": _hide("\n".join(h["lines"]))[:800]}
                                           for h in hits],
            "lines_read": number, "stopped_early": read > MAX_SCAN}


def list_folder(path: str, pattern: str = "*") -> dict:
    folder = Path(path).expanduser()
    if not folder.is_dir():
        return {"error": f"{path} is not a folder on this computer."}
    pattern = pattern or "*"
    if "**" in pattern:
        return {"error": "Recursive patterns (**) are not allowed: list one folder at a time."}
    entries = []
    found = itertools.islice(folder.glob(pattern), 400)
    for item in sorted(found, key=lambda p: p.name.lower())[:200]:
        try:
            info = item.stat()
        except OSError:
            continue
        entries.append({"name": item.name + ("/" if item.is_dir() else ""),
                        "size": info.st_size if item.is_file() else None})
    return {"folder": str(folder.resolve()), "entries": entries,
            "note": "Only the first 200 entries are listed." if len(entries) == 200 else ""}


# Files the assistant may create: inputs and tables, never programs or scripts.
WRITABLE_SUFFIXES = {".csv", ".tsv", ".txt", ".smi", ".xyz", ".sdf", ".mol", ".mol2", ".pdb", ".gjf", ".com",
                     ".inp", ".json", ".yaml", ".yml", ".dat", ".md"}
MAX_WRITE = 2 * 1024 * 1024


def _protected_folder(target: Path) -> str:
    """Why a folder is off limits for writing ('' when it is fine)."""
    from ..settings import luci_home
    package = Path(__file__).resolve().parents[1]
    places = [(luci_home() / "envs", "LUCI's program environments"), (package, "LUCI's own code")]
    try:
        resolved = target.resolve()
    except OSError:
        return "the path cannot be resolved"
    for folder, what in places:
        try:
            folder = folder.resolve()
        except OSError:
            continue
        if resolved == folder or folder in resolved.parents:
            return what
    return ""


def _quick_check(file: Path) -> dict:
    """What LUCI can say about a file just written (molecule CSVs, XYZ, SDF)."""
    suffix = file.suffix.lower()
    try:
        if suffix == ".csv":
            header = file.open(encoding="utf-8-sig").readline().lower()
            if "smiles" in header:
                return {"molecule_csv_check": check_input(str(file))}
            return {}
        text = file.read_text(encoding="utf-8", errors="replace")
        if suffix == ".xyz":
            lines, index, frames = text.splitlines(), 0, 0
            while index < len(lines) and lines[index].strip():
                count = int(lines[index].split()[0])
                atoms = [row for row in lines[index + 2:index + 2 + count] if len(row.split()) >= 4]
                if len(atoms) != count:
                    return {"xyz_check": f"structure {frames + 1}: the first line says {count} atoms, "
                                         f"{len(atoms)} atom lines follow"}
                frames += 1
                index += count + 2
            return {"xyz_check": f"{frames} structure(s), atom counts consistent"}
        if suffix == ".sdf":
            records = text.count("$$$$")
            ends = text.count("M  END")
            return {"sdf_check": f"{records} record(s)" + ("" if ends >= max(records, 1) else
                                                         "; some records lack 'M  END'")}
    except (OSError, ValueError, IndexError) as exc:
        return {"check": f"could not check the file ({exc})"}
    return {}


def write_file(session, path: str, content: str, overwrite: bool = False) -> dict:
    """Create a text file (an input for a program, a merged table...) where the user asked."""
    target = Path(path).expanduser()
    if not target.is_absolute():
        return {"error": "Give the full path of the file (for example C:\\Users\\me\\project\\mols.csv). "
                         "If the user did not say where, ask them, or propose the folder of the input on screen."}
    if target.suffix.lower() not in WRITABLE_SUFFIXES:
        return {"error": f"The assistant only writes input and data files ({', '.join(sorted(WRITABLE_SUFFIXES))}), "
                         "not programs or scripts."}
    if _private(target):
        return {"error": "That name is reserved for keys and settings; choose another one."}
    protected = _protected_folder(target)
    if protected:
        return {"error": f"That folder belongs to {protected}; write the file in the user's own folders."}
    if len(content.encode("utf-8")) > MAX_WRITE:
        return {"error": "The content is larger than 2 MB: split it, or let a program write it."}
    written_before = session.written_files
    if target.exists():
        if target.is_dir():
            return {"error": f"{target} is a folder."}
        if not overwrite:
            return {"error": f"{target.name} already exists: choose another name (for example with _v2)."}
        if str(target.resolve()) not in written_before:
            return {"error": f"{target.name} was not created by the assistant; it is never replaced. Write a new "
                             "file with another name."}
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        text = content.replace("\r\n", "\n")
        text = text if text.endswith("\n") else text + "\n"
        if target.suffix.lower() in (".gjf", ".com") and not text.endswith("\n\n"):
            text += "\n"  # Gaussian needs a blank line after the geometry
        with target.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    except OSError as exc:
        return {"error": f"Could not write {target}: {exc}"}
    written_before.add(str(target.resolve()))
    report = {"written": str(target.resolve()), "bytes": target.stat().st_size,
              "lines": text.count("\n")}
    report.update(_quick_check(target))
    return report


def check_input(path: str) -> dict:
    """LUCI's own check of a molecule CSV or a folder of structures (as `luci check`)."""
    from ..chem.molecules import format_report, read_molecules
    from ..chem.structures import format_folder_report, plan_folder
    target = Path(path).expanduser()
    if target.is_dir():
        result = plan_folder(target)
        return {"summary": result.summary(), "problems": format_folder_report(result, 40),
                "files": [{"file": f.source.name, "what": f.label()} for f in result.files[:60]]}
    molset = read_molecules(target)
    return {"summary": molset.summary(), "problems": format_report(molset, 40),
            "columns_kept": molset.extra_columns}


def environments() -> list[dict]:
    from ..envs.manager import EnvManager
    manager = EnvManager()
    rows = []
    for status in manager.statuses():
        if not status.available:
            state = "not available yet"
        elif not status.supported:
            state = "not supported on this system"
        elif status.installed:
            state = "installed (update available)" if status.outdated else "installed"
        else:
            state = "not installed"
        rows.append({"environment": status.key, "title": status.title, "state": state, "size": status.size_hint})
    return rows


def data_tools(session) -> list[Tool]:
    return [
        Tool("program_details", "Everything LUCI knows about a program: inputs, every option with its native "
             "flag, default and help, methods, environment and notes.",
             {"program": enum(sorted(PROGRAM_BY_KEY), "Program key.")}, ("program",), program_details,
             label="Reading the program's description..."),
        Tool("search_docs", "Search the documentation (LUCI and the upstream documentation of every program: "
             "READMEs, manuals, parameter lists). Use it for specific flags, errors, examples or theory.",
             {"query": s("What to look for (keywords or a question)."),
              "program": s("Program key to favour (optional).")}, ("query",),
             lambda query, program=None: session.search_docs(query, program), label="Searching the documentation..."),
        Tool("read_file", "Read the start or the end of a text file on this computer (CSV, .log/.out, "
             "*_data.dat logs, .xyz/.sdf, .json...). Use it to look at the user's input or a run's results.",
             {"path": s("File path."), "part": enum(["start", "end"], "Start (default) or end of the file."),
              "lines": integer("Lines (60 by default, at most 400).")}, ("path",), read_file,
             label="Reading the file..."),
        Tool("find_in_file", "Lines of a text file that contain a text (e.g. a code_name in CSEARCH_data.dat, "
             "'Error', 'x  ').", {"path": s("File path."), "text": s("Text to find (case ignored).")},
             ("path", "text"), lambda path, text: find_in_file(path, text), label="Searching the file..."),
        Tool("list_folder", "List a folder on this computer (names and sizes), optionally with a pattern like "
             "*.sdf.", {"path": s("Folder path."), "pattern": s("Glob pattern (optional).")}, ("path",),
             list_folder, label="Looking at the folder..."),
        Tool("check_input", "LUCI's check of a molecule CSV (columns, names, empty cells) or of a folder of "
             "structures (which files can be used and how), without running anything.",
             {"path": s("CSV file or folder.")}, ("path",), check_input, label="Checking the input..."),
        Tool("write_file", "Create a text file on this computer: an input for a program (molecule CSV with "
             "smiles and code_name, XYZ/SDF/Gaussian input, a settings JSON/YAML...), a table merged from several "
             "results (descriptors + measured y for ROBERT), or notes. Only where the user said (or agreed to). "
             "Never replaces a file the user already had; folders are created as needed. Returns LUCI's check of "
             "the file (molecule CSVs, XYZ, SDF).",
             {"path": s("Full path of the new file, with its extension."),
              "content": s("The whole text of the file."),
              "overwrite": boolean("Replace a file the assistant itself wrote earlier in this conversation.")},
             ("path", "content"), lambda path, content, overwrite=False: write_file(session, path, content, overwrite),
             control=True, label="Writing the file..."),
        Tool("environments", "State of every program environment on this computer (installed, update available, "
             "not installed, not supported).", {}, (), environments, label="Looking at the environments..."),
    ]
