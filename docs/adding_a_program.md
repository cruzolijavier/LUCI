# Adding a program to LUCI

The answers from a *LUCI program request* form map almost one to one onto the
registry. Nothing outside the files below needs to change: the CLI, the GUI
card, the form, the preview, the install button and saved workflows follow.

## 1. Pick the layer by what the user gets

| The program gives back | Layer |
|---|---|
| 3D structures (conformers, optimized geometries, complexes) | `struct` |
| Energies, thermochemistry | `thermo` |
| Transition states, reaction paths | `react` |
| Descriptors | `feat` |
| Trained models, predictions from the user's data | `pred` |
| The next experiments to run | `design` |

## 2. Give it an environment

Each program gets its own environment (never share one between programs):

1. Add an `EnvSpec` in `registry/environments.py` (platforms, `source=` when it is
   installed from a repository, `postinstall=True` when it needs a setup step).
2. Create `envs/manifests/<key>/pixi.toml`. Conda-forge for compiled tools
   (xtb, openbabel, rdkit), `[pypi-dependencies]` for the rest. List only the
   platforms you can solve. Keep conda-side Python packages to what is needed:
   when a conda package and a PyPI pin name the same package (cffi, numpy),
   pin the conda one to the same version, or the solve fails.
3. Generate the lock with the real mapping and ship it next to the manifest:
   `MAPPING=<compressed_mapping.json> tools/lock_check.sh <key>` then copy
   `/tmp/luci_lock_check/<key>/pixi.lock` into the manifest folder.
4. When the code is cloned, it lives in `src/` next to the manifest; a
   `[tasks] postinstall` can `pip install -e src` or unpack data.

## 3. Describe it

In the layer file (`registry/<layer>.py`) add a `ProgramSpec`:

- `tags`: inputs, cost, mode.
- `variants`: usually one `Variant("default", ..., env="<key>", launch=...)`.
  - Command-line program: `Launch("cli", ("python", "-m", "tool"))`,
    or `("python", "{source}/script.py")` for a cloned script.
    `default_args` adds flags the program always needs (with `{source}`,
    `{output}`); `output_flag` names the flag receiving the output folder.
  - Python API only: `Launch("runner", runner="tool_runner")` and write
    `runners/tool_runner.py` (standard library + the program, Python 3.8 syntax).
- `input_modes`: one per kind of input. Use LUCI's standard inputs whenever the
  program starts from molecules or 3D structures, so it is checked and fed
  like every other program:
  - `molecules_input("--input", columns=(("code_name", "id"), ("smiles", "smiles")))`:
    the molecule CSV, rewritten with the program's column names
    (`keep_extra=False` drops the other columns);
  - `smiles_input("--smiles", name_flag="--mol-id")`: one typed SMILES; with no
    flag it is passed as a one-row CSV through the molecules input;
  - `structures_input("--files")`: a folder of 3D structures, given as SDF
    (`"{folder}/*.sdf"`, or positional with `""`). The program's environment
    must contain Open Babel (`openbabel = "*"` in its manifest), which does the
    conversion.

  For anything else, `InputMode(...)`: `flag=""` makes it positional,
  `dialog="directory"` with `pattern="*.log"` selects a folder, `dialog="none"`
  means no input file.
- In the `Launch`: `structure_outputs=("**/*.xyz",)` when the program writes
  structures in another format (LUCI adds SDF copies with the environment's
  Open Babel), and
  `per_input_output="{name}_*.sdf"` when each molecule gives one file (LUCI
  names the molecules that gave nothing).
- `options`: one `OptionSpec` per flag a researcher changes. `native_flag` for
  spellings like `input-file` or `-q`; `FLAG_ONLY` for "flag without value";
  `multi_value` for `nargs="+"`; `visible_if` to show options only for some
  inputs, variants or other option values; `required=True` to block the run
  while empty.
- `notes`, `citation`, `docs_url`.

Then add it to that file's `PROGRAMS` tuple.

## 4. Check

```bash
python -m pytest
python -c "from luci.registry import validate; print(validate())"
python tools/gen_programs_doc.py
QT_QPA_PLATFORM=offscreen python tools/gui_screenshots.py screenshots 1366x768 760x520
luci env install <program>
luci <layer> --backend <program> --dry-run -- <flags>
```

Compare the flags against the program's own `--help` (the tests do this for
DBSTEP, GoodVibes, AQME and ROBERT when their environments are installed).
