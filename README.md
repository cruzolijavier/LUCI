# LUCI

LUCI (Layered Unified Computational Interfaces) brings many cheminformatics
programs together behind one command line and one desktop interface.

LUCI is organised in **layers named after what you get back**, not after the
internal steps a program takes:

| Layer | You get | Programs |
|---|---|---|
| **LUCI-STRUCT** | 3D structures | AQME CSEARCH, racerTS, MolSimplify, AQME CMIN |
| **LUCI-THERMO** | Energies and thermochemistry | GoodVibes, ThermoMLIP, universal_thermoGNN |
| **LUCI-REACT** | Transition states and reaction profiles | TS-tools (GFN2-xTB, g-xTB, MLIP) |
| **LUCI-FEAT** | Descriptors | AQME QDESCP, DBSTEP, Morfeus, Auto-QChem |
| **LUCI-PRED** | Models and predictions | ROBERT |
| **LUCI-DESIGN** | Next experiments | EDBO+, ScopeBO, BoReact |

A program that runs a whole pipeline (ThermoMLIP: SMILES → conformers → MLIP →
G) lives in the layer of its result. Every program also carries **tags**: the
inputs it accepts (SMILES, 3D structures, QM outputs, reactions, tables), its
cost (CPU, GPU, HPC, licensed software), whether it is a single run or a loop
with the lab, and the systems it runs on. The GUI's *What do you have?* filter
uses them to show only what you can run with the files you have.

The full, generated list is in [docs/programs.md](docs/programs.md).

## Installation

LUCI itself is light: pure Python plus the PySide6 interface.

```bash
python -m pip install ".[gui]"
luci-gui
```

Each program runs in **its own isolated environment**, created the first time
you use it (an *Install* button in the window, or `luci env install <program>`).
Environments are built with [pixi](https://pixi.sh). You do not need to install
pixi: if it is not on your PATH, LUCI downloads a pinned copy into its own
folder the first time. Every program has its own environment, so EDBO+ (torch
1.10, Python 3.9) and thermoGNN (torch 2, Python 3.11) live side by side, and
AQME and ROBERT never constrain each other. Each environment ships with a lock
file: everyone in the group installs exactly the same versions.

AQME 2.1 and ROBERT are installed from GitHub, so they need
[Git](https://git-scm.com/download/win) (default options) on Windows.

Environments, program sources and settings live in the LUCI folder:
`%LOCALAPPDATA%\LUCI` on Windows, `~/.local/share/luci` on Linux (change it with
the `LUCI_HOME` variable).

Developers who already use pixi get the same behaviour: LUCI uses the `pixi`
on the PATH and the same manifests.

## Command line

```bash
luci programs                         # every program, with its tags
luci programs --have smiles,table     # only what can start from these inputs
luci env list                         # environments and their state
luci env install dbstep               # create the environment a program needs
luci env uninstall dbstep             # delete it again (your files and results are kept)

luci <layer> --backend <program> [input] [--variant V] [--output-dir DIR] -- <program flags>
luci check molecules.csv              # check the CSV and the names without running anything
```

### Inputs

Every program that starts from molecules or structures takes them the same way:

- `--molecules mols.csv`: a CSV with the columns `smiles` and `code_name`, one
  molecule per row (other columns such as `charge` and `mult` are kept). The
  `code_name` becomes the name of each molecule's output files.
- `--molecule "CCO" --code-name ethanol`: one SMILES.
- `--structures folder/`: a folder of 3D structures (SDF, XYZ, MOL, MOL2, PDB,
  Gaussian .gjf/.com, Gaussian or ORCA outputs). LUCI always hands programs SDF
  files, converting the rest; structures programs write as XYZ also get an SDF copy.

Before the run LUCI checks the CSV (its columns, empty cells), the names (empty,
repeated, or with characters that break file names) and the structure files,
and says what is wrong and how to fix it. The SMILES themselves are passed on
as written: the programs check them. Files that are not SDF are converted with
Open Babel inside the program's environment. Errors stop the run;
`--skip-invalid` runs the rest. Without `--output-dir`, results go next to the
input. Tables (ROBERT, EDBO+, ScopeBO) are CSV files.

Everything after `--` is passed to the program unchanged, with its own flag
names, so each program's documentation applies as is:

```bash
luci struct --backend aqme_csearch --molecules mols.csv -- --program rdkit --sample 25
luci struct --backend aqme_csearch --molecule "CCO" --code-name ethanol --output-dir results
luci feat   --backend dbstep --structures ligands/ -- --sterimol --vbur --atom1 1 --atom2 2
luci struct --backend racerts --structures ts_guesses/ -- --task ts --reacting_atoms "2 3 4"
luci feat   --backend morfeus --structures conformers/ -- --descriptors "[sterimol,sasa]" --atom_1 1 --atom_2 2
luci thermo --backend goodvibes -- "outputs/*.log" -q --temp 353.15 --json thermo.json
luci react  --backend ts_tools --variant xtb -- --input-file reactions.txt --solvent water
luci design --backend edboplus -- --filename scope.csv --objectives "['yield']" --objective_mode "['max']"
```

`--dry-run` prints the exact command without running it.

### LUCI 0.1 commands

The commands of the first version keep working:

```bash
python -m luci --conf --aqme --input molecules.csv --program rdkit --sample 25   # -> struct / aqme_csearch
python -m luci --gopt --aqme --files "CSEARCH/*.sdf" --program xtb          # -> struct / aqme_cmin
python -m luci --feat --aqme --files "CMIN/*.sdf" --program xtb             # -> feat / aqme_qdescp
python -m luci --pred --robert --csv_name train.csv --y target --names code_name   # -> pred / robert --predict
luci conf --molsimplify --metal fe --ligands "['nh3']" --counts "[6]"     # -> struct / molsimplify
```

Saved workflows from LUCI 0.1 (`"module": "conf"`, `"backend": ...`) load in the
new interface.

## Graphical interface

- **Sidebar:** the six layers, each with what it delivers. With the input filter
  on, each layer shows how many of its programs match.
- **What do you have?** toggles above every layer page filter the program cards.
- **Program cards:** description, input tags (blue, like the filter), installation state and
  an Install button. A program that cannot run on this system has a red pill (*Linux / WSL only*).
- **Inputs:** a molecule CSV, one SMILES or a folder of structures. The CSV
  and the folder are checked as soon as they are chosen: a verdict and the
  list of problems with how to fix them.
- **Program pages:** a form built from the registry (only changed options are
  sent), a version selector for programs with several methods, a live command
  preview, run / stop, and a console. Banners say when an environment is
  missing, which external software is needed, or when a program cannot run on
  this system.
- **Uninstall:** every installed program has an *Uninstall* button on its card and on
  its page; it asks for confirmation, deletes only that program's environment
  and keeps your files and results.
- **Tools → Environments** lists every environment with install / update / uninstall.
- **Tools → Settings** holds what LUCI cannot install: Gaussian and ORCA folders,
  a g-xTB binary, a Hugging Face token for UMA weights, the default results
  folder, and a *restricted network* switch for firewalls.

## Assistant

The robot at the bottom right of the window opens **LUCI Assistant** (OpenAI,
model Luna). It knows LUCI, every program in it (generated from the registry,
so always current) and their upstream documentation (bundled from each
program's GitHub and the installed versions), and it sees the screen: it pays
special attention to the program you have open and tells you when something
does not fit. It can read your input files and logs, search the web (globe
button) and take dictation (microphone). With the small switch under the robot
on (*Control*), it fills the forms for you: input, options, method, advanced
flags, output folder; it only runs or installs when you ask.

Paste the OpenAI key in **Tools → Settings → OpenAI API key**, or save it in a
file `openai_key.txt` in the LUCI folder (next to this README) so everyone using
that folder shares it. `openai_key.txt` is ignored by git: a key pushed to a
public GitHub repository is revoked automatically by OpenAI.

## Windows executable

Double-click `packaging\build_exe.bat` (Python 3.11+ needed only on the computer that builds it). It makes
`dist\LUCI\` (`LUCI.exe`, the window; `luci-cli.exe`, the command line the window runs; `_internal\`)
and `dist\LUCI_windows.zip` to share. Whoever receives it unzips it anywhere and opens `LUCI.exe`:
no Python needed. The program environments are not inside; LUCI installs them with pixi on first
use (internet needed, as in a normal install).

The OpenAI key LUCI uses on the building computer (Tools > Settings or `openai_key.txt`) is packed
into the executable, so the assistant works for everyone who gets it, and their use is charged to
that key. Anyone can extract it from the executable. A user's own key in Tools > Settings takes
precedence. Rebuild after changing LUCI or the key.

## Platform notes

LUCI targets Windows laptops and Linux machines. Some programs are Linux only
(TS-tools, ThermoMLIP, CREST inside AQME); on Windows they are marked
*Linux / WSL only* and cannot be installed. TS-tools g-xTB, TS-tools MLIP and
BoReact are registered but marked *Coming soon* until their code is public.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
QT_QPA_PLATFORM=offscreen python tools/gui_screenshots.py screenshots   # every screen at 4 sizes
python tools/gen_programs_doc.py                                        # refresh docs/programs.md
```

See [docs/architecture.md](docs/architecture.md) and
[docs/adding_a_program.md](docs/adding_a_program.md).
