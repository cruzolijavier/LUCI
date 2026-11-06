"""Turn form values into command lines.

Two levels, both pure functions so the CLI, the GUI and the tests share them:

* :func:`native_args` - the flags the program itself receives (AQME's
  ``--smi CCO --program rdkit``, DBSTEP's ``mol.xyz --sterimol``...). Only the
  options the user changed are emitted, so defaults stay the program's own.
* :func:`luci_command` - the ``luci <layer> --backend <program> -- <native>``
  call that the GUI runs and shows in its preview. Everything goes through the
  LUCI CLI, which owns environments and execution.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any

from .registry import FLAG_ONLY, InputMode, LayerSpec, ProgramSpec, Variant

GLOB_CHARS = set("*?[]")


def flag_for(name: str, style: str = "gnu") -> str:
    """Native spelling of an option: verbatim if it starts with '-', else styled."""
    if name.startswith("-"):
        return name
    return ("-" if style == "short" else "--") + name


def split_multi(value: str) -> list[str]:
    """'0, 1.2 1.3' -> ['0', '1.2', '1.3'] for options taking several values."""
    return [part for part in re.split(r"[,\s]+", value.strip()) if part]


def parse_advanced(text: str) -> list[str]:
    """Split the free-text flag box like a shell, but never fail while typing.

    Quotes group words and are removed (``--name="a b"`` -> ``--name=a b``),
    backslashes are kept as typed (Windows paths), and an unclosed quote just
    runs to the end of the text.
    """
    tokens: list[str] = []
    current: list[str] = []
    quote = ""
    started = False
    for char in text:
        if quote:
            if char == quote:
                quote = ""
            else:
                current.append(char)
        elif char in "\"'" and (not current or current[-1] == "="):
            # A quote opens a group only at the start of a token or after "="
            # (so O'Brien in a path stays a plain apostrophe).
            quote = char
            started = True
        elif char.isspace():
            if started or current:
                tokens.append("".join(current))
            current, started = [], False
        else:
            current.append(char)
            started = True
    if started or current:
        tokens.append("".join(current))
    return tokens


def input_tokens(mode: InputMode | None, value: str) -> tuple[list[str], list[str]]:
    """Return (positional, flagged) tokens for the selected input.

    LUCI's standard inputs (``mode.kind``) are not native tokens: they travel
    as LUCI options (:func:`luci_input_args`) and LUCI writes the program's
    version of them before the run.
    """
    value = value.strip()
    if mode is None or mode.kind or mode.dialog == "none" or not value:
        return [], []
    if mode.dialog == "directory" and not GLOB_CHARS.intersection(value):
        value = str(Path(value) / (mode.pattern or "*"))
    if not mode.flag:
        return [value], []
    return [], [mode.flag, value]


def native_args(
    program: ProgramSpec,
    variant: Variant,
    *,
    input_mode: InputMode | None = None,
    input_value: str = "",
    values: dict[str, Any] | None = None,
    advanced: str = "",
) -> list[str]:
    """Build the native argument list from what the user changed."""
    values = values or {}
    style = variant.launch.flag_style
    positional, tokens = input_tokens(input_mode, input_value)
    for option in program.options:
        value = values.get(option.key)
        if value is None or value == "" or value is False:
            continue
        flag = flag_for(option.native_flag or option.key, style)
        if option.value_is_flag:
            tokens.append(flag_for(str(value), style))
        elif value is True or value == FLAG_ONLY:
            tokens.append(flag)
        elif option.multi_value:
            tokens.extend([flag, *split_multi(str(value))])
        else:
            tokens.extend([flag, str(value)])
    return [*positional, *tokens, *parse_advanced(advanced)]


def luci_input_args(mode: InputMode | None, value: str, code_name: str = "",
                    skip_invalid: bool = False) -> list[str]:
    """LUCI options for a standard input: --molecules, --molecule/--code-name, --structures."""
    value = value.strip()
    if mode is None or not mode.kind or not value:
        return []
    if mode.kind == "molecules":
        args = ["--molecules", value]
    elif mode.kind == "smiles":
        args = ["--molecule", value]
        if code_name.strip():
            args += ["--code-name", code_name.strip()]
    else:
        args = ["--structures", value]
    if skip_invalid and mode.kind != "smiles":
        args.append("--skip-invalid")
    return args


def luci_command(
    layer: LayerSpec,
    program: ProgramSpec,
    native: list[str],
    *,
    variant: str = "",
    output_dir: str = "",
    python: str | None = None,
    inputs: list[str] | None = None,
) -> list[str]:
    """The LUCI CLI call that runs ``program`` with ``native`` arguments."""
    from .frozen import cli_interpreter
    command = [python or cli_interpreter(), "-m", "luci", layer.key, "--backend", program.key]
    if variant and len(program.variants) > 1:
        command += ["--variant", variant]
    command += inputs or []
    if output_dir.strip():
        command += ["--output-dir", output_dir.strip()]
    return [*command, "--", *native]


def preview_command(command: list[str]) -> str:
    """Render a command for display, as a user would type it."""
    shown = list(command)
    for index in range(len(shown) - 1):
        if shown[index:index + 2] == ["-m", "luci"]:
            shown = ["luci", *shown[index + 2:]]
            break
    return " ".join(_quote(token) for token in shown)


def _quote(token: str) -> str:
    if token and not re.search(r"[\s\"'<>|&;()]", token):
        return token
    return '"' + token.replace('"', '\\"') + '"'
