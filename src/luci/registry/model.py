"""The vocabulary every LUCI program is described with.

LUCI is organised in *layers* named after what the user gets back (3D
structures, energies, transition states, descriptors, models, next
experiments). Each layer offers *programs*. A program may come in several
*variants* (TS-tools: xTB, g-xTB or MLIP), and every variant runs inside one
isolated *environment* managed by pixi.

Everything here is declarative. The CLI, the GUI, the command preview, the
environment manager and the saved workflows are all built from these
descriptions, so adding a program never means touching their code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Tags: the second axis next to the layers ("what can I do with what I have")
# ---------------------------------------------------------------------------
InputKind = Literal["smiles", "structures", "qm_output", "reaction", "table"]
Cost = Literal["cpu", "gpu", "hpc", "license"]
RunMode = Literal["oneshot", "loop"]
Platform = Literal["windows", "linux", "macos"]

ALL_PLATFORMS: tuple[Platform, ...] = ("windows", "linux", "macos")
# LUCI targets the group's laptops (Windows) and Linux workstations/clusters.
WINDOWS_LINUX: tuple[Platform, ...] = ("windows", "linux")
UNIX_ONLY: tuple[Platform, ...] = ("linux",)

INPUT_LABELS: dict[str, str] = {
    "smiles": "SMILES",
    "structures": "3D structures",
    "qm_output": "QM outputs",
    "reaction": "Reactions",
    "table": "CSV / tables",
}
INPUT_HELP: dict[str, str] = {
    "smiles": "Molecules as SMILES: one typed in, or a CSV with smiles and code_name columns.",
    "structures": "A folder of 3D structures (SDF, XYZ, MOL, MOL2, PDB, Gaussian or ORCA files); "
                  "LUCI hands them over as SDF.",
    "qm_output": "Finished quantum-chemistry calculations (Gaussian, ORCA, xTB .log/.out).",
    "reaction": "Atom-mapped reaction SMILES (reactants>>products).",
    "table": "A CSV table of datapoints, descriptors or experiments.",
}
COST_LABELS: dict[str, str] = {
    "cpu": "CPU",
    "gpu": "GPU helps",
    "hpc": "HPC cluster",
    "license": "Licensed software",
}
MODE_LABELS: dict[str, str] = {"oneshot": "Single run", "loop": "Iterative loop"}
PLATFORM_LABELS: dict[str, str] = {"windows": "Windows", "linux": "Linux", "macos": "macOS"}


@dataclass(frozen=True)
class Tags:
    """How a program is filtered and labelled across layers."""

    inputs: tuple[InputKind, ...]
    cost: tuple[Cost, ...] = ("cpu",)
    mode: RunMode = "oneshot"


# ---------------------------------------------------------------------------
# Form description (rendered by luci.gui.form, emitted by luci.commands)
# ---------------------------------------------------------------------------
# text/number  -> a single-line field
# choice       -> a dropdown; ``choices`` entries are "value" or ("Label", "value")
# bool         -> a checkbox
# path         -> a file or folder picker
# columns      -> a dropdown filled from the input CSV's header
# multi_columns-> the same, taking several columns at once
# multi_choice -> a grid of checkboxes emitted as a list
OptionKind = Literal[
    "text", "number", "choice", "bool", "path", "columns", "multi_columns", "multi_choice",
]

# Options in this group are rendered inside the Input section.
INPUT_GROUP = "@input"

# A choice value meaning "emit the flag with no value" (``--boltz`` alone).
FLAG_ONLY = "__flag__"


# LUCI's standard inputs, the same for every program (see luci.inputs):
#   molecules   a CSV with smiles and code_name columns
#   smiles      one SMILES typed in (and its code_name)
#   structures  a folder of 3D structures, handed to the program as SDF files
StandardInput = Literal["", "molecules", "smiles", "structures"]
STANDARD_COLUMNS: tuple[tuple[str, str], ...] = (("smiles", "smiles"), ("code_name", "code_name"))


@dataclass(frozen=True)
class InputMode:
    """One kind of input a program accepts.

    ``flag`` is the native flag that receives the value. An empty flag means
    the value is a positional argument (DBSTEP, GoodVibes).

    With ``kind`` set, LUCI checks the input and writes the program's version
    of it before the run: ``columns`` gives the program's CSV layout as
    (LUCI field, program header) pairs, ``name_flag`` receives the code_name of
    a typed SMILES. A ``smiles`` mode without a flag is run through the
    program's ``molecules`` mode as a one-row CSV.
    """

    key: str
    label: str
    flag: str
    file_filter: str = "All files (*)"
    dialog: Literal["file", "directory", "text", "none"] = "file"
    help: str = ""
    # For a directory input, the glob appended to the folder ("*" by default).
    pattern: str = "*"
    # Choosing this input selects the program variant with this key (ThermoMLIP:
    # a CSV runs the batch script, one SMILES the single-molecule script).
    variant: str = ""
    kind: StandardInput = ""
    columns: tuple[tuple[str, str], ...] = STANDARD_COLUMNS
    keep_extra: bool = True
    name_flag: str = ""


@dataclass(frozen=True)
class OptionSpec:
    """One native flag (or runner keyword) and how it is shown."""

    key: str
    label: str
    kind: OptionKind = "text"
    choices: tuple[Any, ...] = ()
    placeholder: str = ""
    tooltip: str = ""
    group: str = "Options"
    # The value that counts as untouched; only changed values are emitted.
    default: Any = ""
    # A bool emitted as a bare switch (``--sterimol``) instead of ``--x True``.
    flag_only: bool = False
    # ("<other option key>", "v1,v2"), ("@input", "mode_key") or ("@variant", "key").
    visible_if: tuple[str, str] | None = None
    same_row: bool = False
    row_label: str = ""
    file_filter: str = ""
    directory: bool = False
    # A path option naming a file the program will create (a "Save as" dialog).
    save: bool = False
    # Native spelling when it differs from ``key`` (e.g. "input-file", "2d").
    # A value starting with "-" is used verbatim ("-q", "-c").
    native_flag: str = ""
    # The run cannot start while this field is empty.
    required: bool = False
    # Split "a, b c" into separate tokens after the flag (argparse nargs="+").
    multi_value: bool = False
    # A choice whose value *is* the flag to emit (ROBERT: "curate" -> --curate).
    value_is_flag: bool = False


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Launch:
    """How a variant is started inside its environment.

    kind="cli"    -> ``command`` + the native flags, e.g. ("python", "-m", "aqme", "--csearch").
    kind="runner" -> a LUCI runner script (``luci/runners/<runner>.py``) executed
                     inside the environment; options travel as a JSON job file.
    kind="app"    -> a program with its own window; LUCI only launches it.

    ``{source}`` in ``command`` is replaced by the program's source checkout and
    ``{env}`` by the environment prefix.
    """

    kind: Literal["cli", "runner", "app"]
    command: tuple[str, ...] = ()
    runner: str = ""
    flag_style: Literal["gnu", "short"] = "gnu"
    # Native flag that receives the output folder (AQME: --destination).
    output_flag: str = ""
    # (flag, value) pairs added unless the user already set that flag. Values
    # may use {source}, {env} and {output}.
    default_args: tuple[tuple[str, str], ...] = ()
    # Run from the input's folder and pass the input relative to it. AQME only
    # expands paths relative to its working folder; results still go to the
    # output folder through ``output_flag``.
    run_from_input: bool = False
    # With run_from_input: subfolder used when the output folder is the input's own
    # folder (AQME's defaults: CSEARCH, CMIN, QDESCP).
    output_subdir: str = ""
    # Copy input files into the output folder and pass their bare names
    # (ROBERT rejects paths containing spaces).
    copy_inputs: bool = False
    # Globs (relative to the output folder) of 3D structures the program writes
    # in another format (XYZ); LUCI adds an SDF copy of each after the run.
    structure_outputs: tuple[str, ...] = ()
    # The file each input molecule or structure should produce ("{name}_*.sdf");
    # after the run LUCI lists the inputs that produced nothing.
    per_input_output: str = ""


@dataclass(frozen=True)
class Variant:
    """One way of running a program (most programs have exactly one)."""

    key: str
    label: str
    env: str
    launch: Launch
    description: str = ""
    # Extra environment variables; values may use {env}, {source} and the
    # settings placeholders {gaussian_dir}, {orca_dir}, {hf_token}.
    env_vars: tuple[tuple[str, str], ...] = ()
    # Requirements outside the environment, shown to the user (Gaussian, ORCA, ...).
    requires: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProgramSpec:
    """Everything LUCI knows about one program."""

    key: str
    name: str
    layer: str
    description: str
    tags: Tags
    variants: tuple[Variant, ...]
    docs_url: str = ""
    input_modes: tuple[InputMode, ...] = ()
    input_help: str = ""
    options: tuple[OptionSpec, ...] = ()
    # "field" shows an Output directory row that follows the input.
    output: Literal["none", "field"] = "field"
    citation: str = ""
    notes: str = ""
    # Names this program had in LUCI 0.1 saved workflows / CLI flags.
    legacy_keys: tuple[str, ...] = ()

    def variant(self, key: str | None = None) -> Variant:
        if key:
            for variant in self.variants:
                if variant.key == key:
                    return variant
            raise KeyError(f"{self.name} has no variant '{key}'")
        return self.variants[0]

    def groups(self) -> list[str]:
        seen: list[str] = []
        for option in self.options:
            if option.group != INPUT_GROUP and option.group not in seen:
                seen.append(option.group)
        return seen

    def input_options(self) -> tuple[OptionSpec, ...]:
        return tuple(o for o in self.options if o.group == INPUT_GROUP)

    def option(self, key: str) -> OptionSpec | None:
        return next((o for o in self.options if o.key == key), None)


@dataclass(frozen=True)
class LayerSpec:
    """One layer: a kind of result the user can obtain."""

    key: str
    title: str
    short_name: str
    name: str
    description: str
    delivers: str
    legacy_keys: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Environments
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SourceSpec:
    """A program that is installed from its repository rather than an index."""

    repo: str
    branch: str = "main"


@dataclass(frozen=True)
class EnvSpec:
    """One pixi environment, described by ``luci/envs/manifests/<key>/pixi.toml``."""

    key: str
    title: str
    platforms: tuple[Platform, ...] = WINDOWS_LINUX
    source: SourceSpec | None = None
    size_hint: str = ""
    # False while the code is not publicly available; ``note`` says why.
    available: bool = True
    note: str = ""
    # Installed but never verified end to end by the LUCI team.
    tested: bool = False
    # Manifest defines a ``postinstall`` task run once after ``pixi install``.
    postinstall: bool = False
    # Git dependencies in the manifest, or a cloned source: Git must be installed.
    needs_git: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
