"""LUCI command line.

    luci <layer> --backend <program> [input] [--variant V] [--output-dir D] [--dry-run] -- <native flags>
    luci check molecules.csv | structures_folder
    luci programs [--layer L] [--have smiles,structures]
    luci env list | install <program> | update <program> | uninstall <program> | path
    luci --gui

Layers: struct, thermo, react, feat, pred, design. Everything after ``--`` (or
after the first option LUCI does not know) goes to the program unchanged.

Inputs, the same for every program (LUCI checks them and writes each
program's own format):
    --molecules FILE.csv        a CSV with the columns smiles and code_name
    --molecule SMILES           one SMILES (name it with --code-name NAME)
    --structures FOLDER         a folder of 3D structures (given to the program as SDF)
    --skip-invalid              leave out molecules or files with errors instead of stopping

LUCI 0.1 commands keep working: ``luci --conf --aqme ...``, ``luci gopt ...``,
``luci --pred --robert ...`` and ``luci conf --molsimplify ...``.
"""

from __future__ import annotations

from pathlib import Path
import sys

from . import __version__
from .envs.manager import EnvError, EnvManager
from .registry import (
    ENV_BY_KEY, INPUT_LABELS, LAYERS, LEGACY_LAYER_DEFAULT, PROGRAM_BY_KEY, layer, matches_inputs, program,
    program_available, program_platforms, programs_in,
)

LUCI_OPTIONS = {"--backend", "-b", "--variant", "--output-dir", "--dry-run", "--help", "-h"}
# LUCI's standard inputs: option -> key in the parsed result.
INPUT_OPTIONS = {"--molecules": "molecules", "--molecule": "molecule", "--code-name": "code_name",
                 "--structures": "structures"}
LEGACY_LAYER_FLAGS = {
    "--conf": "conf", "--luci-conf": "conf", "--luci-c": "conf",
    "--gopt": "gopt", "--luci-gopt": "gopt", "--luci-go": "gopt",
    "--feat": "feat", "--luci-feat": "feat", "--luci-f": "feat",
    "--pred": "pred", "--luci-pred": "pred", "--luci-p": "pred",
}
# Layer names of LUCI 0.1; without --backend they pick that step's old program.
LEGACY_LAYER_NAMES = {
    "conf": "conf", "c": "conf", "luci-conf": "conf", "luci-c": "conf",
    "gopt": "gopt", "go": "gopt", "luci-gopt": "gopt", "luci-go": "gopt",
    "feat": "feat", "f": "feat", "luci-feat": "feat", "luci-f": "feat",
    "pred": "pred", "p": "pred", "luci-pred": "pred", "luci-p": "pred",
}
LEGACY_BACKEND_FLAGS = {"--aqme": "aqme", "--robert": "robert", "--molsimplify": "molsimplify"}

HELP = __doc__


def _layer_help(layer_key: str) -> str:
    spec = layer(layer_key)
    lines = [f"{spec.title} - {spec.description}", "", "Programs (use --backend <key>):"]
    for prog in programs_in(spec.key):
        state = "" if program_available(prog) else "  [not available yet]"
        lines.append(f"  {prog.key:<14} {prog.name}: {prog.description}{state}")
    return "\n".join(lines)


def _legacy_program(legacy_layer: str, backend: str | None) -> str:
    if backend == "molsimplify":
        return "molsimplify"
    return LEGACY_LAYER_DEFAULT[legacy_layer]


def _uses_new_syntax(argv: list[str]) -> bool:
    head = argv[:argv.index("--")] if "--" in argv else argv
    return any(t in ("--backend", "-b") or t.startswith("--backend=") for t in head)


def parse(argv: list[str]) -> dict:
    """Split argv into LUCI's own options and the program's native ones."""
    argv = list(argv)
    result = {"layer": None, "backend": None, "variant": "", "output_dir": "", "dry_run": False,
              "help": False, "native": [], "legacy": None, "notice": "",
              "molecules": "", "molecule": "", "code_name": "", "structures": "",
              "skip_invalid": False, "given": set()}
    # LUCI 0.1 flags may appear anywhere, but only in commands without --backend:
    # with --backend, "--aqme" or "--robert" are the programs' own options.
    legacy_syntax = not _uses_new_syntax(argv)
    legacy_layer = None
    legacy_backend = None
    remaining = []
    seen_separator = False
    for token in argv:
        if token == "--":
            seen_separator = True
        if legacy_syntax and not seen_separator and token in LEGACY_LAYER_FLAGS:
            legacy_layer = LEGACY_LAYER_FLAGS[token]
            continue
        if legacy_syntax and not seen_separator and token in LEGACY_BACKEND_FLAGS:
            legacy_backend = LEGACY_BACKEND_FLAGS[token]
            continue
        remaining.append(token)
    if remaining and not remaining[0].startswith("-"):
        result["layer"] = remaining.pop(0)
        if legacy_syntax:
            legacy_layer = legacy_layer or LEGACY_LAYER_NAMES.get(result["layer"].lower())
    if legacy_layer and not result["layer"]:
        result["layer"] = legacy_layer
    index = 0
    while index < len(remaining):
        token = remaining[index]
        if token == "--":
            result["native"] += remaining[index + 1:]
            break
        name, equals, value = token.partition("=")
        if name in ("--backend", "-b", "--variant", "--output-dir", *INPUT_OPTIONS):
            if not equals:
                if index + 1 >= len(remaining):
                    raise SystemExit(f"luci: {name} needs a value")
                value = remaining[index + 1]
                index += 1
            key = {"--backend": "backend", "-b": "backend", "--variant": "variant",
                   "--output-dir": "output_dir", **INPUT_OPTIONS}[name]
            result[key] = value
            result["given"].add(key)
        elif token == "--dry-run":
            result["dry_run"] = True
        elif token == "--skip-invalid":
            result["skip_invalid"] = True
        elif token in ("--help", "-h") and result["backend"] is None and not legacy_backend:
            result["help"] = True
        elif name.startswith("--back") or name.startswith("--varia") or name.startswith("--output-d"):
            raise SystemExit(f"luci: unknown option {name}; did you mean --backend, --variant or "
                             "--output-dir?")
        else:
            # First unknown token: the rest belongs to the program. LUCI's own
            # options written later (a trailing --dry-run) are still LUCI's,
            # unless the program arguments were introduced with "--".
            rest = remaining[index:]
            if "--" not in rest:
                rest = _pull_luci_options(rest, result)
            result["native"] += rest
            break
        index += 1
    if legacy_layer and not result["help"] and result["backend"] is None:
        result["legacy"] = legacy_layer
        result["backend"] = _legacy_program(legacy_layer, legacy_backend)
        if not legacy_backend and legacy_layer in ("feat", "pred"):
            result["notice"] = (f"No --backend given: using {result['backend']} (the LUCI 0.1 "
                                f"default for '{legacy_layer}'). Choose with --backend.")
        _legacy_options(result)
        if legacy_layer == "pred" and legacy_backend == "robert" and "--predict" not in result["native"]:
            # LUCI 0.1 translated --pred to ROBERT's --predict.
            result["native"].insert(0, "--predict")
    return result


def _pull_luci_options(tokens: list[str], result: dict) -> list[str]:
    """Take LUCI's own options (--dry-run, --output-dir, inputs...) out of the program's arguments."""
    kept: list[str] = []
    index = 0
    keys = {"--output-dir": "output_dir", "--variant": "variant", **INPUT_OPTIONS}
    while index < len(tokens):
        token = tokens[index]
        name, equals, value = token.partition("=")
        if token == "--dry-run":
            result["dry_run"] = True
        elif token == "--skip-invalid":
            result["skip_invalid"] = True
        elif name in keys:
            if not equals:
                if index + 1 >= len(tokens):
                    raise SystemExit(f"luci: {name} needs a value")
                value = tokens[index + 1]
                index += 1
            result[keys[name]] = value
            result.setdefault("given", set()).add(keys[name])
        else:
            kept.append(token)
        index += 1
    return kept


def _legacy_options(result: dict) -> None:
    """LUCI 0.1 accepted --dry-run and --destination anywhere; honour that."""
    native = result["native"]
    if "--" in native:
        return
    if "--files" in native:
        # LUCI 0.1 passed "--files a.sdf b.sdf"; AQME takes one value: [a.sdf,b.sdf].
        start = native.index("--files") + 1
        end = start
        while end < len(native) and not native[end].startswith("-"):
            end += 1
        if end - start > 1:
            native[start:end] = ["[" + ",".join(native[start:end]) + "]"]
    while "--dry-run" in native:
        native.remove("--dry-run")
        result["dry_run"] = True
    for index, token in enumerate(list(native)):
        name, equals, value = token.partition("=")
        if name == "--destination" and not result["output_dir"]:
            if equals:
                del native[index]
            elif index + 1 < len(native):
                value = native[index + 1]
                del native[index:index + 2]
            else:
                break
            result["output_dir"] = str(Path(value).expanduser().resolve())
            break


def _inputs(parsed: dict):
    from .inputs import LuciInputs
    return LuciInputs(molecules=parsed["molecules"], molecule=parsed["molecule"],
                      code_name=parsed["code_name"], structures=parsed["structures"],
                      skip_invalid=parsed["skip_invalid"])


def _variant_from_input(spec, native: list[str], kind: str = "") -> str:
    """For programs whose input picks the variant (ThermoMLIP: --csv batch, --smiles single)."""
    if kind:
        mode = next((m for m in spec.input_modes if m.kind == kind), None)
        return mode.variant if mode is not None else ""
    flags = {token.split("=", 1)[0] for token in native if token.startswith("-")}
    for mode in spec.input_modes:
        if mode.variant and mode.flag in flags:
            return mode.variant
    return ""


def _cmd_programs(args: list[str]) -> int:
    have: set[str] = set()
    only_layer = None
    index = 0
    while index < len(args):
        if args[index] == "--have" and index + 1 < len(args):
            aliases = {"molecules": "smiles", "molecule": "smiles", "qm_outputs": "qm_output",
                       "reactions": "reaction", "tables": "table", "csv": "table"}
            have = {aliases.get(part.strip().lower(), part.strip().lower())
                    for part in args[index + 1].split(",") if part.strip()}
            unknown = have - set(INPUT_LABELS)
            if unknown:
                print(f"luci: unknown input kind(s) {', '.join(sorted(unknown))}; "
                      f"use {', '.join(INPUT_LABELS)}", file=sys.stderr)
                return 2
            index += 1
        elif args[index] == "--layer" and index + 1 < len(args):
            try:
                only_layer = layer(args[index + 1]).key
            except KeyError as exc:
                print(f"luci: {exc.args[0]}", file=sys.stderr)
                return 2
            index += 1
        index += 1
    for spec in LAYERS:
        if only_layer and spec.key != only_layer:
            continue
        listed = [p for p in programs_in(spec.key) if matches_inputs(p, have)]
        if not listed:
            continue
        print(f"{spec.title} ({spec.delivers})")
        for prog in listed:
            inputs = ",".join(prog.tags.inputs) or "-"
            platforms = ",".join(program_platforms(prog))
            state = "" if program_available(prog) else " [not available yet]"
            print(f"  {prog.key:<14} inputs={inputs:<28} cost={','.join(prog.tags.cost):<12} "
                  f"mode={prog.tags.mode:<8} platforms={platforms}{state}")
    return 0


def _env_keys(name: str) -> list[str]:
    """An environment key, or the environments a program's variants use."""
    if name in ENV_BY_KEY:
        return [name]
    spec = program(name)
    keys: list[str] = []
    for variant in spec.variants:
        if variant.env not in keys and ENV_BY_KEY[variant.env].available:
            keys.append(variant.env)
    return keys or [spec.variants[0].env]


def _cmd_env(args: list[str]) -> int:
    manager = EnvManager()
    action = args[0] if args else "list"
    if action == "list":
        pixi = manager.pixi_path()
        print(f"LUCI home: {manager.home}")
        print(f"pixi: {pixi or 'not found (downloaded automatically on first install)'}")
        for status in manager.statuses():
            if not status.available:
                state = "not available yet"
            elif not status.supported:
                state = "not supported on this system"
            elif status.installed:
                state = "installed (update available)" if status.outdated else "installed"
            else:
                state = "not installed"
            print(f"  {status.key:<13} {status.title:<24} {state:<30} {status.size_hint}")
        return 0
    if action == "path":
        print(manager.home)
        return 0
    if action == "uninstall":
        action = "remove"
    if action in ("install", "update", "remove") and len(args) >= 2:
        try:
            for key in _env_keys(args[1]):
                if action == "remove":
                    manager.remove(key)
                else:
                    manager.install(key)
        except (EnvError, KeyError, OSError) as exc:
            print(f"[LUCI] Error: {exc}", file=sys.stderr, flush=True)
            return 1
        return 0
    print("usage: luci env list | install <program> | update <program> | uninstall <program> | path",
          file=sys.stderr)
    return 2


def _cmd_check(args: list[str]) -> int:
    """Check a molecule CSV or a folder of structures without running anything."""
    from .chem.molecules import format_report, read_molecules
    from .chem.structures import format_folder_report, plan_folder
    targets = []
    index = 0
    while index < len(args):
        token = args[index]
        if token in ("--molecules", "--structures") and index + 1 < len(args):
            targets.append(args[index + 1])
            index += 1
        elif token == "--skip-invalid":
            pass
        elif token.startswith("-"):
            print(f"luci check: unknown option {token}", file=sys.stderr)
            return 2
        else:
            targets.append(token)
        index += 1
    if len(targets) != 1:
        print("usage: luci check molecules.csv | structures_folder", file=sys.stderr)
        return 2
    target = Path(targets[0]).expanduser()
    if target.is_dir():
        result = plan_folder(target)
        print(result.summary())
        for line in format_folder_report(result):
            print("  " + line)
        return 0 if result.files and all(f.ok for f in result.files) else 1
    molset = read_molecules(target)
    print(molset.summary())
    for line in format_report(molset, limit=200):
        print("  " + line)
    return 0 if molset.ok else 1


def run(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("--help", "-h", "help"):
        print(HELP)
        return 0
    if argv[0] in ("--version", "version"):
        print(f"LUCI {__version__}")
        return 0
    if argv[0] == "programs":
        return _cmd_programs(argv[1:])
    if argv[0] == "env":
        return _cmd_env(argv[1:])
    if argv[0] == "check":
        return _cmd_check(argv[1:])
    parsed = parse(argv)
    if not parsed["layer"]:
        print(HELP)
        return 2
    try:
        layer_spec = layer(parsed["layer"])
    except KeyError as exc:
        print(f"luci: {exc.args[0]}", file=sys.stderr)
        return 2
    if parsed["help"] and not parsed["backend"]:
        print(_layer_help(layer_spec.key))
        return 0
    backend = parsed["backend"]
    if not backend:
        choices = programs_in(layer_spec.key)
        if len(choices) != 1:
            print(_layer_help(layer_spec.key), file=sys.stderr)
            print("\nluci: choose a program with --backend <key>", file=sys.stderr)
            return 2
        backend = choices[0].key
    try:
        spec = program(backend)
    except KeyError as exc:
        print(f"luci: {exc.args[0]}", file=sys.stderr)
        return 2
    if spec.layer != layer_spec.key and not parsed["legacy"]:
        print(f"luci: {spec.name} belongs to {layer(spec.layer).title}, not {layer_spec.title}",
              file=sys.stderr)
        return 2
    inputs = _inputs(parsed)
    empty = [k for k in ("molecules", "molecule", "structures", "code_name")
             if k in parsed.get("given", set()) and not str(parsed[k]).strip()]
    if empty:
        print(f"luci: --{empty[0].replace('_', '-')} needs a value", file=sys.stderr)
        return 2
    given = [k for k in ("molecules", "molecule", "structures") if parsed[k]]
    if len(given) > 1:
        print("luci: give one input: --molecules, --molecule or --structures", file=sys.stderr)
        return 2
    if parsed["code_name"] and not parsed["molecule"]:
        print("luci: --code-name names a --molecule; in a CSV the names are its code_name column",
              file=sys.stderr)
        return 2
    implied = _variant_from_input(spec, parsed["native"], inputs.kind()) if inputs.kind() else ""
    if parsed["variant"] and implied and parsed["variant"] != implied:
        print(f"luci: {spec.name} runs '{implied}' for this input, not '{parsed['variant']}'; "
              "leave out --variant", file=sys.stderr)
        return 2
    variant_key = parsed["variant"] or implied or _variant_from_input(spec, parsed["native"])
    try:
        variant = spec.variant(variant_key or None)
    except KeyError as exc:
        print(f"luci: {exc.args[0]}", file=sys.stderr)
        return 2
    from .execution import run_program
    if parsed["notice"]:
        print(f"[LUCI] {parsed['notice']}", file=sys.stderr, flush=True)
    try:
        return run_program(spec, variant, parsed["native"], output_dir=parsed["output_dir"],
                           dry_run=parsed["dry_run"], inputs=inputs)
    except (EnvError, ValueError) as exc:
        print(f"[LUCI] Error: {exc}", file=sys.stderr, flush=True)
        return 1


def gui_main(argv: list[str] | None = None) -> int:
    """Start the window, or explain how to get PySide6 when it is missing."""
    args = argv if argv is not None else sys.argv
    if "--apply-update" in args:
        # The new LUCI.exe, started by the old one to install an update. No window, no Qt.
        from .updater import helper_main
        return helper_main(list(args))
    try:
        from .gui.app import main as app_main
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("PySide6"):
            print("The LUCI window needs PySide6. Install it with:\n\n"
                  "    python -m pip install \"PySide6>=6.7\"\n", file=sys.stderr)
            return 1
        raise
    return app_main(argv if argv is not None else sys.argv)


def main() -> int:
    if "--gui" in sys.argv[1:]:
        return gui_main([arg for arg in sys.argv if arg != "--gui"])
    return run()


def _legacy(layer_key: str) -> int:
    return run([layer_key, *sys.argv[1:]])


def conf_main() -> int: return _legacy("conf")
def gopt_main() -> int: return _legacy("gopt")
def feat_main() -> int: return _legacy("feat")
def pred_main() -> int: return _legacy("pred")


__all__ = ["main", "parse", "run", "PROGRAM_BY_KEY"]

if __name__ == "__main__":
    raise SystemExit(main())
