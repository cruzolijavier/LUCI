"""LUCI's standard inputs, turned into what each program expects.

The user gives LUCI one of three things, the same way for every program:

* ``--molecules mols.csv``   a CSV with ``smiles`` and ``code_name`` columns
* ``--molecule SMILES``      one SMILES (``--code-name`` names it)
* ``--structures folder``    a folder of 3D structures

:func:`materialize` checks them (the CSV, the names, the structure files),
reports problems in plain words, and writes the program's own input: AQME's
``SMILES,code_name`` CSV, ThermoMLIP's ``id,smiles``, a folder of SDF files
(converted by Open Babel inside the program's environment)... The tokens it
returns are prepended to the program's native arguments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import subprocess
import uuid

from .chem.issues import Issue
from .chem.molecules import (
    MoleculeSet, dropped_columns, format_report, read_molecules, single_molecule, write_native,
)
from .chem.structures import (
    FolderResult, StructureFile, format_folder_report, prepare_folder,
)
from .registry import ENV_BY_KEY, InputMode, ProgramSpec

KIND_LABELS = {
    "molecules": "a molecule CSV (smiles, code_name)",
    "smiles": "one SMILES",
    "structures": "a folder of 3D structures",
}
STRUCTURE_WORK_DIR = "input_sdf"
INPUT_COPY_DIR = Path(".luci") / "inputs"


class InputError(ValueError):
    """The input cannot be used; the message lists the problems and their fixes."""


@dataclass
class LuciInputs:
    molecules: str = ""
    molecule: str = ""
    code_name: str = ""
    structures: str = ""
    skip_invalid: bool = False

    def kind(self) -> str:
        if self.molecules:
            return "molecules"
        if self.molecule:
            return "smiles"
        if self.structures:
            return "structures"
        return ""

    def resolved(self, base: Path) -> "LuciInputs":
        """The same inputs with absolute paths (relative ones are read from ``base``)."""
        def absolute(value: str) -> str:
            if not value:
                return value
            path = Path(value).expanduser()
            return str((path if path.is_absolute() else base / path).resolve())
        return LuciInputs(absolute(self.molecules), self.molecule, self.code_name,
                          absolute(self.structures), self.skip_invalid)

    def source_folder(self) -> Path | None:
        """The folder the input lives in (decides AQME's CSEARCH/, CMIN/ subfolders)."""
        if self.molecules:
            return Path(self.molecules).expanduser().resolve().parent
        if self.structures:
            return Path(self.structures).expanduser().resolve()
        return None

    def as_args(self) -> list[str]:
        args: list[str] = []
        if self.molecules:
            args += ["--molecules", self.molecules]
        if self.molecule:
            args += ["--molecule", self.molecule]
            if self.code_name:
                args += ["--code-name", self.code_name]
        if self.structures:
            args += ["--structures", self.structures]
        if self.skip_invalid:
            args.append("--skip-invalid")
        return args


@dataclass
class Materialized:
    """What LUCI prepared: tokens for the program and what to tell the user."""

    tokens: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    # code_name of every molecule / stem of every structure file handed over.
    names: list[str] = field(default_factory=list)
    molecules: MoleculeSet | None = None
    structures: FolderResult | None = None


def accepted_kinds(program: ProgramSpec) -> list[str]:
    return [mode.kind for mode in program.input_modes if mode.kind]


def mode_for(program: ProgramSpec, kind: str) -> InputMode:
    for mode in program.input_modes:
        if mode.kind == kind:
            return mode
    accepted = [KIND_LABELS[k] for k in accepted_kinds(program)]
    takes = " or ".join(accepted) if accepted else "its own input flags only"
    raise InputError(f"{program.name} does not take {KIND_LABELS.get(kind, kind)}; it takes {takes}.")


def molecules_mode(program: ProgramSpec) -> InputMode | None:
    return next((m for m in program.input_modes if m.kind == "molecules"), None)


def native_input_flags(program: ProgramSpec) -> set[str]:
    """The program's own flags for its standard inputs (--input, --smi, --name...)."""
    flags = set()
    for mode in program.input_modes:
        if mode.kind:
            flags.update(f for f in (mode.flag, mode.name_flag) if f)
    return flags


def _input_tokens(mode: InputMode, glob_value: str) -> list[str]:
    return [mode.flag, glob_value] if mode.flag else [glob_value]


def _blocking(lines: list[str], what: str, skip_hint: bool) -> InputError:
    message = [f"The {what} has problems that would make the program fail:"]
    message += ["  " + line for line in lines]
    if skip_hint:
        message.append("Fix them, or add --skip-invalid to run without them.")
    return InputError("\n".join(message))


def materialize(program: ProgramSpec, inputs: LuciInputs, outdir: Path, *,
                structures_dir: Path | None = None, dry_run: bool = False,
                converter=None) -> Materialized:
    """Check the input and write the program's version of it."""
    kind = inputs.kind()
    result = Materialized()
    if kind in ("molecules", "smiles"):
        return _molecules(program, inputs, outdir, result, dry_run)
    if kind == "structures":
        return _structures(program, inputs, structures_dir or outdir, result, dry_run, converter)
    return result


def _file_name(stem: str) -> str:
    """A file name every program accepts (AQME splits paths on ',', '[' and ']')."""
    return re.sub(r"[^\w.-]+", "_", stem).strip("._") or "molecules"


def _molecules(program: ProgramSpec, inputs: LuciInputs, outdir: Path, result: Materialized,
               dry_run: bool) -> Materialized:
    kind = inputs.kind()
    mode = mode_for(program, kind)
    if kind == "smiles":
        molset = single_molecule(inputs.molecule, inputs.code_name)
    else:
        molset = read_molecules(inputs.molecules)
    result.molecules = molset
    report = format_report(molset)
    if not molset.file_ok:
        raise _blocking(report, "molecule CSV", False)
    if not molset.records:
        raise InputError("The molecule CSV has no molecules.")
    errors = [r for r in molset.records if not r.ok]
    if errors and (kind == "smiles" or not inputs.skip_invalid):
        raise _blocking(report, "molecule input" if kind == "smiles" else "molecule CSV",
                        kind == "molecules")
    valid = molset.valid()
    if not valid:
        raise InputError("None of the molecules can be used:\n" + "\n".join("  " + l for l in report))
    source = "typed SMILES" if kind == "smiles" else Path(inputs.molecules).name
    result.lines.append(f"Molecules ({source}): {molset.summary()}")
    result.lines += report
    if errors:
        result.lines.append(f"Left out {len(errors)} molecule(s) with errors: "
                            + ", ".join(r.code_name or r.where() for r in errors[:10])
                            + (" ..." if len(errors) > 10 else ""))
    result.names = [r.name for r in valid]
    if kind == "smiles" and mode.flag:
        record = valid[0]
        result.tokens = [mode.flag, record.smiles]
        if mode.name_flag:
            result.tokens += [mode.name_flag, record.name]
        elif inputs.code_name:
            result.lines.append(f"{program.name} does not use a code_name for one SMILES; "
                                f"'{inputs.code_name}' is ignored.")
        return result
    # A CSV in the program's layout (also for one typed SMILES when the program
    # only reads files).
    target_mode = mode if mode.kind == "molecules" else molecules_mode(program)
    if target_mode is None:  # pragma: no cover - registry validation forbids it
        raise InputError(f"{program.name} has no molecule CSV input.")
    dropped = dropped_columns(molset, target_mode.columns, target_mode.keep_extra)
    if dropped and kind == "molecules":
        result.lines.append(f"Columns not passed to {program.name}: {', '.join(dropped)}.")
    stem = Path(inputs.molecules).stem if kind == "molecules" else (valid[0].name or "molecule")
    target = outdir / INPUT_COPY_DIR / f"{_file_name(stem)}.csv"
    if not dry_run:
        write_native(molset, target, target_mode.columns, target_mode.keep_extra, skip_invalid=True)
    result.tokens = [target_mode.flag, str(target)] if target_mode.flag else [str(target)]
    return result


def _structures(program: ProgramSpec, inputs: LuciInputs, base: Path, result: Materialized,
                dry_run: bool, converter) -> Materialized:
    mode = mode_for(program, "structures")
    folder = Path(inputs.structures).expanduser()
    prepared = prepare_folder(folder, base / STRUCTURE_WORK_DIR, converter, dry_run=dry_run,
                              skip_invalid=inputs.skip_invalid)
    result.structures = prepared
    report = format_folder_report(prepared)
    if not prepared.files:
        raise _blocking(report or [prepared.summary()], "folder of structures", False)
    failed = [item for item in prepared.files if not item.ok]
    if failed and not inputs.skip_invalid:
        raise _blocking(report, "folder of structures", True)
    usable = [item for item in prepared.files if item.ok and item.target is not None]
    if not usable:
        raise InputError("None of the structure files can be used:\n" + "\n".join("  " + l for l in report))
    result.lines.append(f"Structures ({folder.name}): {prepared.summary()}")
    converted = [item for item in usable if item.action == "convert"]
    if converted:
        verb = "will be converted" if dry_run else "converted"
        result.lines.append(f"{len(converted)} file(s) {verb} to SDF with Open Babel in {prepared.folder}")
    result.lines += report
    if failed:
        result.lines.append(f"Left out {len(failed)} file(s) that cannot be used: "
                            + ", ".join(item.source.name for item in failed[:10]))
    result.names = [item.target.stem for item in usable]
    if set("[]*?") & set(str(prepared.folder)):
        raise InputError(f"The path {prepared.folder} contains [, ], * or ?, which the programs read "
                         "as wildcards, so they would not find the files. Rename the folder (or "
                         "choose an output folder) without those characters.")
    pattern = mode.pattern if mode.pattern and mode.pattern != "*" else "*.sdf"
    result.tokens = _input_tokens(mode, str(prepared.folder / pattern))
    return result


def openbabel_converter(manager, env_key: str):
    """Convert structure files with Open Babel inside ``env_key`` (see runners/to_sdf.py)."""
    from .envs.manager import python_runner_path

    def convert(items: list[StructureFile], work_dir: Path) -> None:
        scratch = work_dir / ".luci-tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        stamp = uuid.uuid4().hex[:12]  # two runs on the same folder never share these files
        job = scratch / f"to_sdf-{stamp}.json"
        results_file = scratch / f"to_sdf-{stamp}-results.json"
        job.write_text(json.dumps({
            "results": str(results_file),
            "files": [{"source": str(item.source), "text": item.text, "fmt": item.fmt,
                       "target": str(item.target), "name": item.source.stem,
                       "charge": item.charge, "mult": item.mult} for item in items],
        }), encoding="utf-8")
        argv = manager.run_argv(env_key, ["python", str(python_runner_path("to_sdf")), str(job)])
        title = ENV_BY_KEY[env_key].title if env_key in ENV_BY_KEY else env_key
        try:
            run = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=3600)
            results = json.loads(results_file.read_text(encoding="utf-8"))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            output = getattr(locals().get("run"), "stdout", b"") or b""
            detail = output.decode("utf-8", "replace").strip().splitlines()[-1:] or [str(exc)]
            raise InputError(f"Could not convert the structures to SDF with Open Babel in the "
                             f"{title} environment: {detail[0]}") from None
        finally:
            for path in (job, results_file):
                try:
                    path.unlink()
                except OSError:
                    pass
            try:
                scratch.rmdir()
            except OSError:
                pass
        if "_fatal" in results:
            raise InputError(f"{results['_fatal']} ({title}). Update the environment: Tools > "
                             f"Environments, or luci env update {env_key}.")
        for item in items:
            outcome = results.get(str(item.target), {"ok": False, "error": "Not converted."})
            if outcome.get("ok"):
                item.structures = outcome.get("structures", 1)
                for warning in outcome.get("warnings", []):
                    item.issues.append(Issue("warning", "charge", warning))
            else:
                item.issues.append(Issue("error", "convert", outcome.get("error", "Not converted.")))
    return convert


def missing_outputs(names: list[str], folder: Path, pattern: str) -> list[str]:
    """Inputs that produced no file matching ``pattern``.

    AQME 2.1 writes <name>_rdkit.sdf (CSEARCH), <name>.sdf (CMIN) and, for an
    SDF holding several molecules, <name>_1_rdkit.sdf, <name>_2_rdkit.sdf...
    """
    if not pattern or not names or not folder.is_dir():
        return []
    suffix = Path(pattern).suffix
    stems = [path.stem.lower() for path in folder.glob("*" + suffix)
             if path.is_file() and path.stat().st_size > 0]
    missing = []
    for name in names:
        key = name.lower()
        if not any(stem == key or stem.startswith(key + "_") for stem in stems):
            missing.append(name)
    return missing


def issue_lines(issues: list[Issue]) -> list[str]:
    return [f"{issue.level.upper()}: {issue.text()}" for issue in issues]
