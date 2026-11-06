"""Run one program inside its environment.

This is the only place where LUCI starts a scientific program. The CLI calls
:func:`run_program`; the GUI runs the CLI in a QProcess, so both share it.
"""

from __future__ import annotations

import ast
import filecmp
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import NamedTuple

from .commands import GLOB_CHARS, flag_for
from .envs.manager import EnvError, EnvManager, python_runner_path
from .chem.structures import new_outputs, snapshot as structure_snapshot
from .inputs import (
    InputError, LuciInputs, Materialized, materialize, missing_outputs, native_input_flags,
    openbabel_converter,
)
from .proc import run_forwarding_signals
from .registry import ENV_BY_KEY, ProgramSpec, Variant
from .settings import Settings, current_platform


class Prepared(NamedTuple):
    """Everything needed to start a run (see :func:`prepare`)."""

    argv: list[str]
    outdir: Path
    run_dir: Path
    environ: dict[str, str]
    job: dict | None
    job_file: Path | None
    inputs: Materialized


def path_flags(program: ProgramSpec, variant: Variant) -> set[str]:
    """Native flags whose value is a file or folder (inputs and path options)."""
    # Typed inputs (SMILES) are text, not files: never turn them into paths.
    flags = {mode.flag for mode in program.input_modes
             if mode.flag and mode.dialog not in ("text", "none")}
    for option in program.options:
        if option.kind == "path":
            flags.add(flag_for(option.native_flag or option.key, variant.launch.flag_style))
    return flags


def absolutize(tokens: list[str], base: Path, flags: set[str],
               value_flags: set[str] | None = None) -> list[str]:
    """Make relative *file* arguments absolute before the working folder changes.

    Touched: values of ``flags`` (inputs and path options, also as
    ``--flag=value``) and positional arguments wherever they appear
    (``dbstep --sterimol a.xyz``). Left exactly as typed: the values of other
    options (``value_flags``), such as ``[[1,2,1.8]]``, SMILES or output names
    like ``--csv steric.csv``.
    """
    value_flags = value_flags or set()
    result = list(tokens)
    expecting: str | None = None
    for index, token in enumerate(result):
        if token.startswith("-") and not _looks_negative_number(token):
            name, equals, value = token.partition("=")
            if equals:
                if name in flags:
                    result[index] = f"{name}={_absolute(value, base)}"
                expecting = None
            else:
                expecting = name if (name in flags or name in value_flags) else None
            continue
        if expecting is not None:
            if expecting in flags:
                result[index] = _absolute(token, base)
            expecting = None
            continue
        result[index] = _absolute(token, base)
    return result


def _looks_negative_number(token: str) -> bool:
    try:
        float(token)
        return True
    except ValueError:
        return False


def value_flags_of(program: ProgramSpec, variant: Variant) -> set[str]:
    """Flags that consume the next token (every option that is not a bare switch)."""
    style = variant.launch.flag_style
    return {flag_for(o.native_flag or o.key, style) for o in program.options
            if not (o.kind == "bool" and o.flag_only) and not o.value_is_flag}


def _absolute(token: str, base: Path) -> str:
    if len(token) > 2 and token.startswith("[") and token.endswith("]"):
        # AQME's list syntax, "[a.sdf,b.sdf]": each item is a path.
        items = [item.strip().strip("'\"") for item in token[1:-1].split(",") if item.strip()]
        return "[" + ",".join(_absolute(item, base) for item in items) + "]"
    if not token or Path(token).is_absolute():
        return token
    candidate = base / token
    if candidate.exists():
        return str(candidate.resolve())
    if GLOB_CHARS.intersection(token) and candidate.parent.is_dir():
        return str(candidate.parent.resolve() / candidate.name)
    return token


def parse_runner_kwargs(tokens: list[str]) -> dict:
    """``--key value`` / ``--switch`` tokens -> keyword arguments for a runner.

    Values are parsed as Python literals when possible ("[1, 2]", "{'a': 1}",
    "5", "True") and kept as strings otherwise.
    """
    kwargs: dict = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if not token.startswith("--"):
            raise ValueError(f"Unexpected argument '{token}': use --name value")
        key, equals, value = token[2:].partition("=")
        key = key.replace("-", "_")
        if not equals:
            if index + 1 < len(tokens) and not tokens[index + 1].startswith("--"):
                value = tokens[index + 1]
                index += 1
            else:
                value = "True"
        kwargs[key] = _literal(value)
        index += 1
    return kwargs


def _literal(value: str):
    """Python literal if the text is one ("[1, 2]", "{'a': 'x'}"), else the text.

    Backslashes are kept as typed, so Windows paths inside lists or dicts
    ("{'D:\\data\\new.csv': 'A'}") are not turned into escape sequences.
    """
    text = value.replace("\\", "\\\\") if "\\" in value else value
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError, MemoryError, RecursionError):
        return value
    if isinstance(parsed, (set, frozenset, tuple)):
        return list(parsed)
    if isinstance(parsed, complex):
        return value
    return parsed


class _Format(dict):
    def __missing__(self, key):
        return ""


def _expand(text: str, context: dict) -> str:
    return text.format_map(_Format(context))


def build_environment(variant: Variant, context: dict) -> dict[str, str]:
    """os.environ plus the variant's variables; PATH entries are prepended."""
    environ = dict(os.environ)
    for name, template in variant.env_vars:
        value = _expand(template, context)
        if not value.strip():
            continue
        if name.upper() == "PATH":
            environ["PATH"] = value + os.pathsep + environ.get("PATH", "")
        else:
            environ[name] = value
    return environ


def prepare(program: ProgramSpec, variant: Variant, native: list[str], output_dir: str = "",
            manager: EnvManager | None = None, cwd: Path | None = None,
            require_installed: bool = True, inputs: LuciInputs | None = None,
            dry_run: bool = False) -> Prepared:
    """Work out argv, folder and environment without running anything.

    ``inputs`` are LUCI's standard inputs (molecules, one SMILES, a folder of
    structures): they are checked here and written in the program's format
    (nothing is written with ``dry_run``).
    """
    manager = manager or EnvManager()
    settings: Settings = manager.settings
    env_key = variant.env
    manager.check_usable(env_key)
    if require_installed and not manager.is_installed(env_key):
        raise EnvError(
            f"{program.name} is not installed yet. Install it from the LUCI window, or run: "
            f"luci env install {program.key}")
    base = Path(cwd or Path.cwd())
    if inputs is not None and inputs.kind():
        inputs = inputs.resolved(base)
        clash = native_input_flags(program) & {t.split("=", 1)[0] for t in native if t.startswith("-")}
        if clash:
            raise InputError(f"{', '.join(sorted(clash))} is the program's own input; with "
                             f"--molecules, --molecule or --structures LUCI sets it. Remove it from "
                             "the program options.")
    source = inputs.source_folder() if inputs is not None else None
    # Without --output-dir results go next to the input, as in the window.
    outdir = Path(output_dir).expanduser() if output_dir else (source or base)
    if not outdir.is_absolute():
        outdir = base / outdir
    outdir = outdir.resolve()
    native = absolutize(list(native), base, path_flags(program, variant),
                        value_flags_of(program, variant))
    launch = variant.launch
    material = Materialized()
    if inputs is not None and inputs.kind():
        structures_base = outdir
        if launch.run_from_input and launch.output_subdir and source is not None and source == outdir:
            # Results go to CSEARCH/, CMIN/... next to the input, as AQME does.
            outdir = outdir / launch.output_subdir
        material = materialize(program, inputs, outdir, structures_dir=structures_base,
                               dry_run=dry_run, converter=openbabel_converter(manager, env_key))
        native = material.tokens + native
    context = {
        "runners": str(python_runner_path("_luci_job").parent),
        "source": str(manager.source_dir(env_key)),
        "env": str(manager.prefix(env_key)),
        "env_bin": str(manager.bin_dir(env_key)),
        "output": str(outdir),
        **settings.placeholders(),
    }
    present = {token.split("=", 1)[0] for token in native if token.startswith("-")}
    run_dir = outdir
    if launch.run_from_input:
        outdir = _aqme_layout(program, launch, native, outdir)
        run_dir = outdir
        context["output"] = str(outdir)
    if launch.copy_inputs:
        _copy_inputs(program, variant, native, outdir, dry_run=dry_run)
    if launch.output_flag and launch.output_flag not in present:
        native += [launch.output_flag, str(outdir)]
    for flag, value in launch.default_args:
        if flag not in present:
            native += [flag, _expand(value, context)]
    if launch.kind == "runner":
        job_dir = outdir / ".luci"
        job = {
            "program": program.key,
            "variant": variant.key,
            "output_dir": str(outdir),
            "source_dir": context["source"],
            "kwargs": parse_runner_kwargs(native),
        }
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        job_file = job_dir / f"{program.key}-{stamp}.json"
        command = ["python", str(python_runner_path(launch.runner)), str(job_file)]
    else:
        job = None
        job_file = None
        command = [_expand(token, context) for token in launch.command] + native
    argv = manager.run_argv(env_key, command)
    return Prepared(argv, outdir, run_dir, build_environment(variant, context), job, job_file,
                    material)


def _input_values(program: ProgramSpec, native: list[str]):
    """(index, flag, value) of every input-flag value in ``native``."""
    flags = {mode.flag for mode in program.input_modes
             if mode.flag and mode.dialog not in ("text", "none")}
    for index, token in enumerate(native):
        name, equals, value = token.partition("=")
        if equals and name in flags:
            yield index, name + "=", value
        elif token in flags and index + 1 < len(native):
            yield index + 1, "", native[index + 1]


def _split_list(value: str) -> list[str]:
    """AQME's list syntax '[a.sdf,b.sdf]' -> items; anything else -> [value]."""
    if value.startswith("[") and value.endswith("]") and "," in value:
        return [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]
    return [value]


def _aqme_layout(program: ProgramSpec, launch, native: list[str], outdir: Path) -> Path:
    """Prepare an AQME run: inputs relative to the output folder, which is the cwd.

    AQME only handles paths inside its working folder, so it runs from the
    output folder and receives its inputs as relative paths. When the output
    folder is the input's own folder, results go to a module subfolder
    (CSEARCH/, CMIN/, QDESCP/) as AQME does by default: CMIN would otherwise
    write ``<name>.sdf`` over the input SDF.
    """
    inputs = list(_input_values(program, native))
    folders = set()
    for _, _, value in inputs:
        for item in _split_list(value):
            folders.add(Path(item).parent if Path(item).is_absolute() else None)
    if launch.output_subdir and outdir in folders:
        outdir = outdir / launch.output_subdir
    for index, prefix, value in inputs:
        items = []
        for item in _split_list(value):
            path = Path(item)
            if path.is_absolute():
                try:
                    item = os.path.relpath(path, outdir)
                except ValueError:  # another drive on Windows: bring the file along
                    copy_dir = outdir / ".luci" / "inputs"
                    copy_dir.mkdir(parents=True, exist_ok=True)
                    for match in (path.parent.glob(path.name) if GLOB_CHARS.intersection(path.name)
                                  else [path]):
                        shutil.copy2(match, copy_dir / match.name)
                    item = os.path.relpath(copy_dir / path.name, outdir)
            items.append(item)
        joined = items[0] if len(items) == 1 and not value.startswith("[") else "[" + ",".join(items) + "]"
        native[index] = prefix + joined
    return outdir


def _copy_inputs(program: ProgramSpec, variant: Variant, native: list[str], outdir: Path,
                 dry_run: bool = False) -> None:
    """Copy input files into the output folder and pass their bare names.

    A different file already there under the same name is never overwritten.
    """
    flags = path_flags(program, variant)
    for index, token in enumerate(native[:-1]):
        if token in flags:
            path = Path(native[index + 1])
            if path.is_file():
                target = outdir / path.name
                if path.resolve() != target.resolve():
                    if target.exists() and not filecmp.cmp(path, target, shallow=False):
                        raise InputError(
                            f"{target} already exists and is a different file. LUCI needs to copy "
                            f"{path.name} there for {program.name}; choose another output folder or "
                            "rename one of the two files.")
                    if not dry_run:
                        outdir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(path, target)
                native[index + 1] = path.name


def run_program(program: ProgramSpec, variant: Variant, native: list[str], *,
                output_dir: str = "", dry_run: bool = False,
                manager: EnvManager | None = None, inputs: LuciInputs | None = None) -> int:
    """Run the program, streaming its output; return its exit code."""
    argv, outdir, run_dir, environ, job, job_file, material = prepare(
        program, variant, native, output_dir, manager, require_installed=not dry_run,
        inputs=inputs, dry_run=dry_run)
    env_title = ENV_BY_KEY[variant.env].title
    print(f"[LUCI] {program.name} ({variant.label}) in environment '{env_title}'", flush=True)
    for line in material.lines:
        print(f"[LUCI] {line}", flush=True)
    print(f"[LUCI] Output folder: {outdir}", flush=True)
    if job is not None:
        print("[LUCI] Job: " + json.dumps(job["kwargs"]), flush=True)
    print("[LUCI] $ " + quote_command(argv), flush=True)
    if dry_run:
        return 0
    outdir.mkdir(parents=True, exist_ok=True)
    if job_file is not None:
        job_file.parent.mkdir(parents=True, exist_ok=True)
        job_file.write_text(json.dumps(job, indent=2), encoding="utf-8")
    before = _snapshot(run_dir) if run_dir != outdir else {}
    launch = variant.launch
    structures_before = (structure_snapshot(outdir, (*launch.structure_outputs, "**/*.sdf"))
                         if launch.structure_outputs else {})
    try:
        code = run_forwarding_signals(argv, cwd=run_dir, env=environ)
    except FileNotFoundError as exc:
        raise EnvError(f"Could not start {argv[0]}: pixi was not found. Reinstall the "
                       "environment or set the pixi path in Settings.") from exc
    if run_dir != outdir:
        _collect_logs(run_dir, outdir, before)
    print(f"\n[LUCI] {program.name} finished with exit code {code}.", flush=True)
    if code in CRASH_CODES:
        print(f"[LUCI] {program.name} crashed (it was killed by the system, not stopped by LUCI). "
              "This is a bug or a missing library in the program, not a problem with your input.",
              flush=True)
    if code >= 0 or code in CRASH_CODES:
        _after_run(program, variant, outdir, material, structures_before, manager)
    # sys.exit() cannot carry a negative code: use the shell's 128 + signal convention.
    return 128 - code if code < 0 else code


def _after_run(program: ProgramSpec, variant: Variant, outdir: Path, material: Materialized,
               structures_before: dict[str, float], manager: EnvManager | None) -> None:
    """Tell the user which inputs gave nothing, and add SDF copies of new structures."""
    launch = variant.launch
    missing = missing_outputs(material.names, outdir, launch.per_input_output)
    if missing:
        shown = ", ".join(missing[:15]) + (" ..." if len(missing) > 15 else "")
        logs = ", ".join(sorted(p.name for p in outdir.glob("*_data.dat"))) or "the console above"
        print(f"[LUCI] No result for {len(missing)} of {len(material.names)} input(s): {shown}.",
              flush=True)
        print(f"[LUCI] Look for their names in {logs} to see why.", flush=True)
    if not launch.structure_outputs:
        return
    items = new_outputs(outdir, launch.structure_outputs, structures_before)
    if not items:
        return
    try:
        openbabel_converter(manager or EnvManager(), variant.env)(items, outdir)
    except InputError as exc:
        print(f"[LUCI] No SDF copies of the new structures: {exc}", flush=True)
        return
    made = [item for item in items if item.ok]
    if made:
        print(f"[LUCI] SDF copies written next to {len(made)} new structure file(s).", flush=True)
    for item in items:
        for issue in item.issues:
            if issue.level == "error":
                print(f"[LUCI] {item.source.name}: {issue.text()}", flush=True)


# Windows exit codes of a crash: access violation, stack overflow, illegal instruction.
# On Linux: killed by SIGSEGV, SIGABRT, SIGILL, SIGBUS or SIGFPE (a stop is SIGTERM, -15).
CRASH_CODES = {0xC0000005, 0xC00000FD, 0xC000001D, -1073741819, -1073741571, -11, -6, -4, -7, -8}

# Log files AQME always writes into its working folder.
STRAY_LOGS = ("*_data.dat", "AQME_run.csv")


def _snapshot(folder: Path) -> dict[str, float]:
    found = {}
    for pattern in STRAY_LOGS:
        for path in folder.glob(pattern):
            found[path.name] = path.stat().st_mtime
    return found


def _collect_logs(run_dir: Path, outdir: Path, before: dict[str, float]) -> None:
    """Move the logs a run left next to the input into the output folder."""
    for pattern in STRAY_LOGS:
        for path in run_dir.glob(pattern):
            if before.get(path.name) == path.stat().st_mtime:
                continue
            try:
                shutil.move(str(path), str(outdir / path.name))
            except OSError:
                pass


def quote_command(argv: list[str]) -> str:
    """A command line the user can copy and paste into their shell."""
    if current_platform() == "windows":
        return subprocess.list2cmdline(argv)
    return shlex.join(argv)
