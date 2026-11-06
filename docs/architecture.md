# LUCI architecture

```text
src/luci/
├── registry/            single source of truth (declarative)
│   ├── model.py         LayerSpec, ProgramSpec, Variant, Launch, OptionSpec, Tags, EnvSpec
│   ├── struct.py ...    one file per layer: the programs it offers
│   ├── environments.py  the pixi environments
│   └── __init__.py      LAYERS, PROGRAMS, lookups, legacy names, validate()
├── commands.py          form values -> native flags -> `luci <layer> --backend ...`
├── execution.py         run one program inside its environment (the only place that does)
├── envs/
│   ├── manager.py       locate/download pixi, install/update/remove, run argv
│   └── manifests/<env>/pixi.toml
├── runners/             scripts run *inside* an environment for Python-API-only programs
├── settings.py          LUCI home folder and user settings (Gaussian, ORCA, HF token...)
├── cli.py               `luci` command line (and LUCI 0.1 compatibility)
└── gui/                 PySide6 interface built from the registry
```

## Principles

1. **Layers are named after results.** STRUCT, THERMO, REACT, FEAT, PRED,
   DESIGN. A program that runs a pipeline goes where its output belongs.
2. **Tags are a second axis.** Inputs, cost, mode (single run or loop) and
   platform. The GUI filter and `luci programs --have` use them.
3. **LUCI never imports a scientific program.** Each one runs with `pixi run`
   in its own environment, in a separate process. Communication goes through
   files and, for programs without a command line, a JSON job read by a runner.
4. **Only changed options are sent.** Upstream defaults stay authoritative.
5. **One execution path.** The GUI runs the LUCI CLI in a QProcess; the CLI
   calls `execution.run_program`. What the preview shows is what runs.

## How a run works

```text
GUI form ──values──▶ commands.native_args ──▶ luci <layer> --backend P [--variant V] [--molecules F | --molecule S | --structures D] --output-dir D -- <native>
                                                         │
                                                  cli.parse / run
                                                         │
                                         execution.prepare(program, variant, native)
                                           • environment installed and supported?
                                           • standard inputs checked and written in the program's format (luci.inputs)
                                           • relative files made absolute
                                           • AQME: run from the input folder (it only expands relative paths)
                                           • output flag, default_args, {source} / {env} / {output}
                                           • runner programs: JSON job in <output>/.luci/
                                           • env vars: Gaussian/ORCA on PATH, XTB_PATH, HF_TOKEN
                                                         │
                         pixi run --manifest-path <home>/envs/<env>/pixi.toml --no-install --executable <command>
```

## Standard inputs

Every program that starts from molecules or 3D structures takes them the same
way, and LUCI writes each program's own format:

| Input | GUI | CLI | What LUCI hands the program |
|---|---|---|---|
| Molecule CSV | *Molecules (CSV)* | `--molecules m.csv` | the program's CSV layout (`InputMode.columns`): AQME `SMILES,code_name`, ThermoMLIP `id,smiles`... in `<output>/.luci/inputs/` |
| One SMILES | *One SMILES* + code_name | `--molecule S --code-name N` | `--smi S --name N` (`name_flag`), or a one-row CSV when the program only reads files |
| Folder of 3D structures | *Folder of 3D structures* | `--structures DIR` | SDF files: the folder itself when it holds only SDF, else `<output>/input_sdf/` (converted by Open Babel in the program's environment, cached) |

The molecule CSV needs the columns `smiles` and `code_name`; other columns
(`charge`, `mult`...) are kept. `code_name` names each molecule's output files
in every program. Tables (ROBERT, EDBO+, ScopeBO) are CSV only.

`luci.chem` does the checking in plain Python (LUCI has no chemistry library):

- `table.read_table` reads a CSV (UTF-8, UTF-16 or Windows-1252; `,`, `;` or
  tab; Excel's `sep=` line), refuses Excel workbooks named .csv and unclosed
  quotes, and writes clean comma-separated UTF-8 copies.
- `molecules.read_molecules` checks the columns, empty cells and the names
  (spaces become `_`; characters Windows forbids, reserved names and repeated
  names are errors). The SMILES are passed on as written.
- `structures.plan_folder` decides, without converting, what happens to each
  file: SDF files are used as they are; Gaussian .gjf/.com and Gaussian/ORCA
  .log/.out are read by LUCI (last geometry, with the charge and spin of that
  job) and handed to Open Babel as XYZ; XYZ, MOL, MOL2 and PDB go to Open Babel
  directly. When two files share a name the SDF wins, then the finished
  calculation over its input. 2D drawings (a "2D" MOL header with all z = 0)
  are refused.
- `structures.prepare_folder` runs the conversion through
  `runners/to_sdf.py` inside the program's own environment (Open Babel is in
  the AQME, Auto-QChem, MolSimplify, DBSTEP and TS-tools environments). SDF
  records get AQME's `Real charge` and `Mult` properties when the file states
  them. Conversions are cached in `input_sdf/` with a manifest (size,
  modification time, start of the content, converter version); LUCI only ever
  overwrites or deletes files listed in that manifest, and never converts into
  the user's own folder.
- `structures.new_outputs` finds the XYZ structures a run wrote
  (`Launch.structure_outputs`: MolSimplify, TS-tools); LUCI adds an SDF copy
  next to each, never replacing an SDF that existed before the run.

Errors stop the run with the list of problems; `--skip-invalid` (the GUI's
*Leave out the N with errors*) runs the rest. After the run,
`Launch.per_input_output` lists the molecules that produced nothing. The GUI
shows the same check under the input (`gui/inputs.py`): a verdict and the
problem list. `luci check` runs it from the command line.

## Environments

One manifest per environment (`envs/manifests/<key>/pixi.toml`) rather than one
shared file, because pixi solves every environment of a manifest together: a
broken upstream pin in one program would otherwise block all the others.
Every program has its own environment (the three AQME modules are one program), so
one program's pins can never break another.

Each manifest ships with a `pixi.lock` (both platforms, solved with the real
conda <-> PyPI mapping by `tools/lock_check.sh`). Installs run `pixi install
--frozen`: the user's machine downloads exactly those versions and never solves,
so an upstream release cannot break a new install and every group member gets
the same versions.

Install steps (`EnvManager.install`):

1. Remove the "installed" marker (written again only at the end), then copy the
   manifest and its `pixi.lock` to `<home>/envs/<key>/`. Leftovers of an
   unfinished install are deleted first.
2. For programs installed from a repository, clone it into `src/` there (git,
   or a zip download when git is missing).
3. `pixi install --frozen` (Git must be installed for environments with GitHub
   dependencies: AQME 2.1 and ROBERT master).
4. Run the manifest's `postinstall` task when there is one (editable install of
   the source, unpacking a checkpoint...).
5. Write `.luci-installed.json` with the manifest hash. A different hash later
   means *Update available*.

pixi itself: the `pixi_path` setting, then `LUCI_PIXI`, then `pixi` on PATH,
then `<home>/bin/pixi`, which LUCI downloads (pinned version) when needed.

## Variants

A program can have several variants, each with its own environment and launch
(TS-tools: xTB, g-xTB, MLIP). The GUI shows a *Method* selector, unless the
program's input modes pick the variant (ThermoMLIP: a CSV runs the batch
script, one SMILES the single-molecule one). Options can depend on the variant
with `visible_if=("@variant", "xtb,gxtb")`.

## Testing

`python -m pytest` covers the registry and manifests, command building, the CLI
(including LUCI 0.1 syntax), execution planning, every runner (against fake
programs, under Python 3.8 grammar) and the GUI offscreen (every page, filters,
variants, workflows, and no horizontal overflow at 1920×1080 down to 760×520).
`tools/gui_screenshots.py` renders every screen for visual review.
