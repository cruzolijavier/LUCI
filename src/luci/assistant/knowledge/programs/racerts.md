# racerTS: upstream documentation

Source: https://github.com/digital-chemistry-laboratory/racerts (docs: https://digital-chemistry-laboratory.github.io/racerts/)

## How LUCI runs racerTS

- Layer LUCI-STRUCT, program key `racerts`, its own environment (Python 3.12, Open Babel, racerTS from GitHub at a pinned commit because the gs/ts/constrained command line is not on PyPI yet; Git is needed to install it).
- Inputs: molecules (CSV with smiles and code_name, or one SMILES) for the ground-state task; a folder of 3D structures for any task (LUCI hands them over as SDF; a file with several structures starts from the first one).
- LUCI calls `racerts <task> <molecule> -o <code_name>_racerts.xyz` once per molecule or file and adds an SDF copy of every ensemble. LUCI lists the molecules that gave no ensemble.
- Options in the window: Task (gs / ts / constrained), Reacting atoms and Frozen atoms (ts), Fixed atoms (--hard, constrained), Topology SMILES and Molecular graph (structure files), Charge / multiplicity (empty = from the SMILES, the CSV charge/mult columns or the charge stored in the SDF), Conformers to embed, Conformer factor, Energy window, RMSD threshold, Force field, Embedding, ETKDGv3, Threads, Random seed, No fallbacks, CREST-style energies, Pipeline settings file, Detailed log.
- Atom indices are 0-based (racerTS' own convention), unlike DBSTEP and Morfeus (1-based).
- CLI example: luci struct --backend racerts --structures ts_guesses/ -- --task ts --reacting_atoms "2 3 4"
- AQME CSEARCH also uses racerTS internally for its --freeze workflow; the racerTS program gives direct access to all of its options.


## racerts/README.md

<p align="center">
  <img src="https://raw.githubusercontent.com/digital-chemistry-laboratory/racerts/main/docs/img/logo.png" alt="racerTS logo" width="450">
</p>

<p align="center"><b>Ra</b>pid <b>C</b>onformer <b>E</b>nsembles with <b>R</b>DKit for <b>T</b>ransition <b>S</b>tates</p>

<p align="center">
  <a href="https://doi.org/10.1021/acs.jcim.5c02794"><img src="https://img.shields.io/badge/paper-JCIM%202026-blue" alt="Paper"></a>
  <a href="https://pypi.org/project/racerts/"><img src="https://img.shields.io/pypi/v/racerts.svg" alt="PyPI"></a>
  <a href="https://anaconda.org/conda-forge/racerts"><img src="https://img.shields.io/conda/vn/conda-forge/racerts.svg" alt="conda-forge"></a>
  <a href="https://github.com/digital-chemistry-laboratory/racerts/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/digital-chemistry-laboratory/racerts/test.yml?label=tests" alt="Tests"></a>
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license">
</p>

<p align="center">Transition-state conformer ensembles via constrained distance geometry</p>

# Installation

```shell
$ pip install racerts
```

# Usage

racerTS can be imported as a Python module that is easily integrated into
workflows for transition state conformer ensemble generation.
For further information, see the separate [documentation](https://digital-chemistry-laboratory.github.io/racerts/).

```shell
>>> import racerts
>>> ensemble = racerts.generate_ts("example.xyz", reacting_atoms=[2, 3, 4], charge=0)
>>> ensemble.write_xyz("ensemble.xyz")
```

The legacy racerts API (`ConformerGenerator`) keeps working and gives the same ensembles.
It can also be accessed via a command line interface.

```console
$ racerts ts example.xyz --reacting-atoms 2 3 4 --charge 0
$ racerts example.xyz --charge 0 --reacting_atoms 2 3 4   # legacy form
```

# Cite this work
If you use racerTS, please cite [our paper in *J. Chem. Inf. Model.*](https://doi.org/10.1021/acs.jcim.5c02794):

```
@article{schmid_rapid_2026,
	author = {Schmid, Stefan P. and Seng, Henrik and Kläy, Thibault and Jorner, Kjell},
	title = {Rapid Generation of Transition-State Conformer Ensembles via Constrained Distance Geometry},
	journal = {Journal of Chemical Information and Modeling},
	volume = {66},
	number = {5},
	pages = {2777-2790},
	year = {2026},
	doi = {10.1021/acs.jcim.5c02794},
}
```

# Data availability

All data to reproduce the study can be found on [Zenodo](https://doi.org/10.5281/zenodo.17610186).

# License
MIT License

Copyright &copy; 2025 ETH Zürich


## racerts/docs/getting-started.md

# Getting started

## What is racer<sup>TS</sup>?

racer<sup>TS</sup> generates conformer ensembles for transition states (TS) using RDKit functions.

This documentation covers how to install and use racer<sup>TS</sup>, the command-line interface, and how to configure the individual components.

- [Command-line interface](cli.md)
- [Modules overview](modules/README.md)


<img src="../img/TOC.png" alt="TOC" width="400">

## Installation

- Python 3.10+
- RDKit >= 2023.9.6 (installed automatically via pip dependency)

```bash
pip install racerts
pip install "racerts[ase]"   # optional: refinement with ASE calculators (xTB, MLIPs, ...)
pip install "racerts[yaml]"  # optional: pipeline settings as YAML files
```

## Input format

- Input geometry must be an .xyz file of a TS structure (or .sdf/.mol with bonds)
- Reacting atoms are the atoms whose connectivity changes in the reaction
- Overall molecular charge
- Optionally, a SMILES for either product or starting material can be provided to define the topology around the TS


## Quickstart (Python)

```python
import racerts

# example.xyz is a single-geometry TS structure; reacting atoms are 0-based indices
ensemble = racerts.generate_ts("example.xyz", reacting_atoms=[2, 3, 4], charge=0)
ensemble.write_xyz("ensemble.xyz")
print(ensemble.summary())
```

`generate_ts` returns a [`ConformerEnsemble`](pipeline.md#conformer-ensembles): the RDKit
molecule with its conformers (`ensemble.mol`), their energies and provenance. Settings
are passed as a [`PipelineConfig`](pipeline.md#settings); tasks other than transition
states (ground states, constrained cores) are described in [Pipelines and
tasks](pipeline.md).

The legacy racerts API still works and gives the same ensembles:

```python
from racerts import ConformerGenerator

cg = ConformerGenerator()
mol = cg.generate_conformers(file_name="example.xyz", charge=0, reacting_atoms=[2,3,4])
cg.write_xyz("ensemble.xyz")
```

## Quickstart (CLI)

```bash
racerts ts example.xyz --reacting-atoms 2 3 4 --charge 0
racerts example.xyz --charge 0 --reacting_atoms 2 3 4   # legacy racerts form, same result
```

This will generate a pruned ensemble and write `conformer_ensemble.xyz` in the current directory by default.

Messages go through Python's `logging` (logger `racerts`): warnings are shown by
default; `verbose=True` (or `-v`, `-vv` on the command line) also shows progress.


## racerts/docs/cli.md

# Command-line interface

The `racerts` CLI mirrors the core functionality of the Python API. It has three
subcommands, `racerts ts`, `racerts gs` and `racerts constrained`, and keeps the legacy racerts form
`racerts filename.xyz [options]` (also `racerts run filename.xyz [options]`), which is
described in the rest of this page. With the same settings, `racerts ts` and the legacy form
write the same ensemble.

## racerts ts / racerts gs / racerts constrained

```bash
$ racerts ts ts.xyz --reacting-atoms 3 4 5 --smiles "CCCCCC=C" [options]
$ racerts gs "OC(=O)[C@@H]1CCCN1C(C)=C" [options]
$ racerts gs molecule.xyz [options]
$ racerts constrained complex.xyz --hard 0 1 2 3 [options]
```

`racerts constrained` samples a structure around atoms that stay where they are in the
file, e.g. a binding motif or a core (the task `Constrained` of the
[Python API](pipeline.md#tasks)).

`racerts gs` takes the molecule as a SMILES or as a structure file. From a file it keeps
the configuration of the geometry (stereocentres and double bonds). The graph of an xyz
file comes from the SMILES (`-s`) if given, then from the perceived bonds, and from the
connectivity alone only with `--graph connect`: without bond orders the search would run
on a different molecule.

| Option | Explanation |
| --- | --- |
| `-r`, `--reacting-atoms` (ts) | 0-based indices of the atoms whose bonds form or break |
| `--frozen-atoms` (ts) | frozen atoms instead of the reacting atoms and their neighbours |
| `--hard` (constrained) | 0-based indices of the atoms held at the geometry of the file |
| `-s`, `--smiles` (ts, constrained, gs with a file) | SMILES of the TS topology or of the molecule, one per fragment |
| `--graph` (ts, constrained, gs with a file) | first method for the graph: `smiles`, `bonds` or `connect` |
| `-c`, `--charge` | total charge (default 0; gs with a SMILES: from the SMILES) |
| `--multiplicity` | spin multiplicity (default: the lowest for the electrons) |
| `--config` | [PipelineConfig](pipeline.md#settings) as JSON or YAML; the options below override it |
| `-n`, `--n-conformers`, `--conf-factor` | conformers to embed |
| `--embed` | `cmap` or `bounds` |
| `--etkdg`, `--no-etkdg` | ETKDGv3 instead of plain distance geometry (default: only for gs) |
| `--refine` | `mmff` or `uff` |
| `--no-fallback` | no fallback for the graph (bonds, connectivity) or MMFF (UFF) |
| `--seed`, `--num-threads` | |
| `--energy-threshold`, `--rmsd-threshold` | pruning |
| `-o`, `--output` | output file (default `conformer_ensemble.xyz`) |
| `--crest-energies` | only the energy (Hartree) on each comment line, as CREST does |
| `-v`, `-vv` | progress (INFO) or details (DEBUG) on stderr |

## racerts filename.xyz (legacy)

The command is:
```bash
$ racerts filename.xyz [options]
```
where the `filename.xyz` is the path to an .xyz file containing a single TS conformer.

### General inputs

| Command | Options | Explanation |
| --- | --- | --- |
| `-c`<br>`--charge` | &lt;INT&gt; [0] | Overall molecular charge |
| `-mult`<br>`--multiplicity` | &lt;INT&gt; | Spin multiplicity; the lowest for the number of electrons (1 or 2) if omitted |
| `-smiles`<br>`--input_smiles` | &lt;STR...&gt; | One (or multiple) SMILES for either product<br>or starting material to define topology |
| `-atoms`<br>`--reacting_atoms` | &lt;INT...&gt; | List of (0-based) indices of reacting atoms |
| `-frozen`<br>`--frozen_atoms` | &lt;INT...&gt; | Optional: overwrite of atoms to freeze;<br>if omitted, neighbors of reacting atoms are inferred |

### Ensemble size

| Command | Options | Explanation |
| --- | --- | --- |
| `-cf`<br>`--conf_factor` | &lt;INT&gt; [80] | Number of initially generated conformers: <br>NumRotatableBonds × `conf_factor` + 30  |
| `-n`<br>`--number_of_conformers` | &lt;INT&gt; [-1] | Specify number of initially generated conformers <br>(and overwrite `conf_factor`) |


### Conformer Generation Configuration

| Command | Options | Explanation |
| --- | --- | --- |
| `-m`<br>`--mol` | &lt;smiles\|bonds\|connect&gt; | Method to infer molecular graph from .xyz:<br>`smiles` use [`MolGetterSMILES`](./modules/conformer_generator.md#get_mol);<br>`bonds` use [`MolGetterBonds`](./modules/conformer_generator.md#get_mol);<br>`connect` use [`MolGetterConnectivity`](./modules/conformer_generator.md#get_mol) |
| `-e`<br>`--embed` | &lt;dm\|cmap&gt; [cmap] | Embedding method:<br>`dm` = bounds-matrix; uses [`BoundsMatrixEmbedder`](./modules/conformer_generator.md#embed_TS);<br>`cmap` = coordinate map; uses [`CmapEmbedder`](./modules/conformer_generator.md#embed_TS) |
| `-ff`<br>`--ff` | &lt;mmff\|uff&gt; [mmff] | Force-field refinement: ;<br>`mmff` uses [`MMFFOptimizer`](./modules/ff_optimizer.md#mmff_optimizer);<br>`uff` uses [`UFFOptimizer`](./modules/ff_optimizer.md#uff_optimizer) |


### Output

| Command | Options | Explanation |
| --- | --- | --- |
| `-o`<br>`--output` | &lt;STR&gt; [conformer_ensemble.xyz] | Output .xyz filename; the comment lines are in extended XYZ format<br>(energy in eV, charge, spin; readable with `ase.io.read`) |
| `--out_energies` | - | Instead, write only the energy in E<sub>h</sub> on each comment line (as in CREST ensembles);<br>conformer property remains in kcal/mol |
| `-v`<br>`--verbose` | - | Progress on stderr (`-vv`: details) |

### Performance and reproducibility

| Command | Options | Explanation |
| --- | --- | --- |
| `--num_threads` | &lt;INT&gt; [1] | Threads for embedding/optimization |
| `--seed` | &lt;INT&gt; [12] | Random seed |
| `--no_fallback` | - | Disable automatic fallback (see below) |

!!! note "Fallback"
    In the default setup, an automatic fallback substitutes modules upon failure:
    
    **MolGetter:**<br>
    1. [`MolGetterSMILES`](./modules/conformer_generator.md#get_mol)<br>
    2. [`MolGetterBonds`](./modules/conformer_generator.md#get_mol)<br>
    3. [`MolGetterConnectivity`](./modules/conformer_generator.md#get_mol)<br>
    
    **Optimizer**<br>
    1. [`MMFFOptimizer`](./modules/ff_optimizer.md#mmff_optimizer)<br>
    2. [`UFFOptimizer`](./modules/ff_optimizer.md#uff_optimizer)<br>

    The next module in the chain is used only if the previous one fails.

### molgetter options

| Command  | Explanation |
| ---  | --- |
| `--no_assignbonds` | For `bonds` getter: don’t assign bonds [default: True] |
| `--disallow_charged_fragments` | For `bonds` getter: disallow charged fragments [default: True] |

### embedder options

| Command | Explanation |
| --- | --- |
| `--no_random_coords` | Disable random coordinates |

### optimizer options

| Command | Explanation |
| --- | --- |
| `--force_constant` | &lt;FLOAT&gt; [1e6] | Distance-constraint force constant used during<br>FF optimization |

### RMSDPruner options

| Command | Options | Explanation |
| --- | --- | --- |
| `-rmsd`<br>`--rmsd_thres` | &lt;FLOAT&gt; [0.125] | RMSD threshold in Å |
| `-rmsd_hs`<br>`--rmsd_include_hs` | - | Include hydrogens when computing RMSDs <br>[default: False] |
| `--no_filter_energies` | - | Disable energy-based dissimilarity prefilter <br>[default: True] |
| `--no_filter_rotations` | - | Disable rotational-profile prefilter <br>[default: True] |
| `--rmsd_energy` | &lt;FLOAT&gt; [0.1] | Energy difference threshold (kcal/mol) for the prefilter |
| `--rmsd_rot_fraction` | &lt;FLOAT&gt; [0.03] | Rotational-difference fraction threshold |
| `-rmsd_match`<br>`--rmsd_max_matches` | &lt;INT&gt; [10000] | Max substructure matches for RMSD calculation |

### EnergyPruner options

| Command | Options | Explanation |
| --- | --- | --- |
| `-energy`<br>`--energy_thres` | &lt;FLOAT&gt; [20.0] | Energy window for pruning (kcal/mol) |

### Common recipes
Basic run
```bash
$ racerts example.xyz --charge 0 --reacting_atoms 2 3 4
```

Use SMILES-defined topology and coordinate-map embedding
```bash
$ racerts example.xyz --charge 0 \
  --reacting_atoms 2 3 4 \
  --input_smiles "C1=CC=CC=C1" "O" \
  --mol smiles --embed cmap --ff mmff --out_energies
```

Increase diversity by allowing more initial conformers
```bash
$ racerts example.xyz --charge 0 --reacting_atoms 2 3 4 --conf_factor 120
```
Faster refinement on many conformers with threads (if using multithreaded optimizers)
```bash
$ racerts example.xyz --charge 0 --reacting_atoms 2 3 4 --num_threads 4
```


## racerts/docs/pipeline.md

# Pipelines and tasks

racerts splits a conformer search into a **task** (what stays fixed), a **pipeline**
of stages (what is done), and a **context** that carries the molecule, the task and the
settings through the stages. The defaults reproduce legacy racerts exactly.

```python
import racerts

ensemble = racerts.generate_ts("ts.xyz", [3, 4, 5], smiles="CCCCCC=C")
```

is the same as

```python
from racerts.system import build_mol

mol = build_mol("ts.xyz", charge=0, reacting_atoms=[3, 4, 5], input_smiles=["CCCCCC=C"])
ensemble = racerts.generate(mol, racerts.TransitionState([3, 4, 5]))
```

## Tasks

| Task | Frozen atoms | Needs a reference geometry |
| --- | --- | --- |
| `TransitionState(reacting_atoms, frozen_atoms=None)` | reacting atoms and their neighbours (or `frozen_atoms`) | yes |
| `GroundState()` | none | no |
| `Constrained(hard)` | the `hard` atoms | yes |

A task returns a `FrozenSet`: `hard` atoms are placed at the reference positions during
embedding and held there during refinement. In the bounds-matrix embedder
(`embed.mode = "bounds"`), the distances between the `core` atoms (for a TS the reacting
atoms) and all hard atoms are fixed.

```python
# Ground states (ETKDGv3 embedding, nothing frozen, stereocentres kept)
ensemble = racerts.generate_gs("OC(=O)[C@@H]1CCCN1C(C)=C")

# Keep a motif of a structure fixed, sample the rest
mol = build_mol("complex.xyz", charge=0, reacting_atoms=[])
ensemble = racerts.generate(mol, racerts.Constrained(hard=[0, 1, 2, 3]))
```

## Settings

`PipelineConfig` holds the settings of the default pipeline as plain data; it can be
written to and read from JSON or YAML files. Values are checked when the config is made
and when a setting is changed: unknown keys, values of the wrong type and values out of
range raise `ValueError`. In YAML files, numbers such
as `1e6` are read as numbers (as in YAML 1.2).

```python
config = racerts.PipelineConfig.from_dict(
    {"seed": 7, "embed": {"mode": "bounds", "n_conformers": 200}, "refine": {"backend": "uff"}}
)
config.to_file("settings.yaml")
ensemble = racerts.generate_ts("ts.xyz", [3, 4, 5], config=config)
```

| Section | Setting | Default | Meaning |
| --- | --- | --- | --- |
| | `seed` | 12 | RDKit embedding seed |
| | `num_threads` | 1 | threads for embedding, force fields and RMSDs |
| `embed` | `mode` | `cmap` | `cmap` (coordinate map) or `bounds` (bounds matrix) |
| | `n_conformers` | -1 | conformers to embed; -1: rotatable bonds × `conf_factor` + 30 |
| | `conf_factor` | 80 | |
| | `etkdg` | None | ETKDGv3 instead of plain distance geometry; None: only without frozen atoms |
| | `use_random_coords` | true | |
| `refine` | `backend` | `mmff` | `mmff` or `uff` |
| | `fallback` | true | UFF if MMFF has no parameters |
| | `force_constant` | 1e6 | kcal/mol/Å² on the frozen atoms |
| `prune` | `energy_threshold` | 20.0 | kcal/mol above the lowest conformer |
| | `eht_energies` | false | rank by extended Hückel energies |
| | `rmsd_threshold` | 0.125 | Å, heavy atoms |
| | `include_hs`, `filter_energies`, `filter_rotations`, `rmsd_energy_threshold`, `rot_fraction_threshold`, `max_matches` | | see [pruner](modules/pruner.md) |

## Pipelines and stages

The default pipeline is `Embed → Refine → PruneEnergy → PruneRMSD`. Each stage takes the
context and the ensemble so far and returns an ensemble; stages built without arguments
use the legacy racerts defaults. A pipeline can be put together by hand, e.g. to refine
with an ASE calculator:

```python
from ase.calculators.lj import LennardJones
from racerts.refine import ASEOptimizer

pipeline = racerts.Pipeline([
    racerts.Embed(n_conformers=50),
    racerts.Refine(ASEOptimizer(calculator=LennardJones(), fmax=0.1)),
    racerts.PruneEnergy(),
    racerts.PruneRMSD(),
])
ensemble = racerts.generate_ts("ts.xyz", [3, 4, 5], pipeline=pipeline)
```

Any object with a `name` and a `run(ctx, ensemble)` method is a stage:

```python
class KeepLowest:
    name = "keep_lowest"

    def __init__(self, n):
        self.n = n

    def run(self, ctx, ensemble):
        order = sorted(ensemble.conf_ids, key=ensemble.energy)
        return ensemble.filter(order[: self.n])
```

Components are the objects that stages call. A new embedder subclasses
`racerts.embed.BaseEmbedder` and implements `embed(mol, reference, frozen, n)`; a new
optimizer subclasses `racerts.refine.BaseOptimizer` and implements
`_refine(mol, reference, anchors)`, which `refine` calls after checking its arguments.
Components written for legacy racerts (`embed_TS`, `tune_ts_conformers`) run in the stages
too: their base classes in `racerts.compat` route `embed` and `refine` to the legacy
methods.

`Pipeline.run(ctx, ensemble)` continues an ensemble (e.g. to refine it with another
method) and leaves the ensemble passed in unchanged; stages may change the ensemble they
get in place. `Embed` starts an ensemble: to combine two embedding runs (with different
seeds), merge their ensembles. Components passed to a stage (an embedder with its seed,
an optimizer) keep their own settings; stages create default ones for the task, e.g.
`Embed()` uses ETKDGv3 for ground states.

The pipeline logs every stage with its number of conformers and run time (logger
`racerts.pipeline.runner`, level INFO); `generate`, `generate_ts` and `generate_gs` take
`verbose=True` to show these messages.

## Conformer ensembles

A `ConformerEnsemble` wraps the RDKit molecule with its conformers (`ensemble.mol`).
Everything known about the conformers is stored in RDKit properties, so RDKit code and
the legacy classes see the same data:

| Property | Of | Content |
| --- | --- | --- |
| `energy` | each conformer | energy in kcal/mol |
| `provenance` | each conformer | JSON, e.g. `{"embedder": "CmapEmbedder", "seed": 12, "etkdg": false}` |
| `energy_method` | the molecule | the optimizer that gave the energies |
| `charge`, `multiplicity` | the molecule | total charge and spin multiplicity |

Conformer ids are those of the embedding; pruning leaves gaps, so use `conf_ids`:

```python
ensemble.conf_ids              # e.g. [0, 3, 4, 9]
ensemble.energies()            # numpy array in the order of conf_ids, NaN where missing
best = ensemble.best()         # id of the lowest conformer
ensemble.record(best)          # ConformerRecord(conf_id, energy, energy_method, provenance)
ensemble.filter(ensemble.conf_ids[:5])  # a copy with these conformers
ensemble.merge(other)          # conformers of both (same graph and energy method)
ensemble.to_ase(best)          # ASE Atoms with charge and multiplicity
ensemble.write_xyz("out.xyz")  # extended XYZ; use_energy=True for CREST-style energies
```

Ensembles can be pickled (e.g. to return them from worker processes) with all their
data; plain RDKit pickling of `ensemble.mol` drops the properties.


## racerts/docs/migration.md

# Migrating from legacy racerts

racerts gives the same ensembles as legacy racerts (0.1.7 and its fixes) with the same inputs:
`ConformerGenerator().generate_conformers(...)`, `racerts.generate_ts(...)`,
`racerts file.xyz ...` and `racerts ts file.xyz ...` write identical files.

## What stays

The legacy API keeps working; all of it lives in `racerts.compat`:

- Every module path and name of racerts 0.1.7: `from racerts import ConformerGenerator,
  embedders, mol_getters, optimizers, pruners`, `racerts.embedder`, `racerts.optimizer`,
  `racerts.pruner`, `racerts.mol_getter`, `racerts.conformer_generator`,
  `racerts.embedder.utils`, `racerts.optimizer.ase`, `racerts.utils.get_frozen_atoms`,
  `racerts.visualizer`, and so on (`tests/test_compat.py` checks them against the 0.1.7
  release).
- Custom subclasses of the legacy base classes. The legacy embedders and optimizers are
  subclasses of the current ones in `racerts.embed` and `racerts.refine` that add the
  legacy methods `embed_TS` and `tune_ts_conformers`; the current classes do not have
  them. Pruners and mol getters are the same classes in both.
- The command line `racerts file.xyz [options]` with all its options (also as
  `racerts run ...`), in `racerts.compat.cli`.

## Behaviour changes since 0.1.7

- Output files: the comment lines are extended XYZ (energy in eV, charge, spin,
  `energy_method`) instead of charge and multiplicity (`0 1`); `write_xyz(path,
  comment="0 1")` writes such a line as given. CREST-style energies (`use_energy=True`, `--out_energies`) leave out conformers
  without an energy and use the CODATA 2022 Hartree (627.5094740629 kcal/mol instead of
  627.509), so the sixth decimal can differ.
- Messages go through Python `logging` (logger `racerts`) instead of stdout: warnings to
  stderr, progress with `verbose=True` or `-v`/`-vv`.
- `generate_conformers` uses `conf_factor=80` by default, as the command line always did
  (it was 30 in the Python API).
- Stricter input: invalid SMILES, SMILES whose formal charges disagree with `charge`, and an
  embedding without conformers raise errors; errors of optimizers other than MMFF are raised
  instead of being retried silently with UFF.
- The default multiplicity is the lowest one for the number of electrons (not the radical
  count of the TS graph), which reaches ASE calculators as their spin.
- The chirality fallback of the embedders (for TS geometries that contradict a chiral tag)
  now logs a warning.

## For new code

| legacy racerts | now |
| --- | --- |
| `ConformerGenerator().generate_conformers(file, charge, reacting_atoms, input_smiles=...)` returns a `Mol` | `racerts.generate_ts(file, reacting_atoms, charge=..., smiles=...)` returns a `ConformerEnsemble` (`.mol` is the `Mol`) |
| components set on the generator | stages of a `Pipeline`, or settings of a `PipelineConfig` |
| `cg.embedder = BoundsMatrixEmbedder()` | `PipelineConfig(embed=EmbedConfig(mode="bounds"))` |
| `cg.optimizer = UFFOptimizer()` | `PipelineConfig(refine=RefineConfig(backend="uff"))` |
| `cg.optimizer = ASEOptimizer(calculator=...)` | `Refine(ASEOptimizer(calculator=...))` in a pipeline |
| `cg.write_xyz(path)` | `ensemble.write_xyz(path)` |
| TS only | also `generate_gs(smiles)` and `Constrained(hard=[...])` |

Where the legacy code lives now:

| legacy racerts | now |
| --- | --- |
| `racerts.conformer_generator` | `racerts.compat` (`DEFAULT_CONF_FACTOR` also in `racerts.embed`; `KCAL_TO_HARTREE` keeps 627.509, `racerts.utils.units.HARTREE_TO_KCAL_MOL` is the CODATA value) |
| `racerts.embedder.embedder` | `racerts.embed` (`CmapEmbedder`, `BoundsMatrixEmbedder`, without `embed_TS`) |
| `racerts.embedder.utils` | `racerts.embed.bounds`: `get_bounds_matrix(mol_ts, new_mol, frozen_atoms, reacting_atoms)` is `bounds_matrix(new_mol, mol_ts, fixed_distance_pairs(FrozenSet(tuple(frozen_atoms), tuple(reacting_atoms))))`; `tol_function`; `print_bounds_matrix_errors` is `log_inconsistent_bounds` |
| `racerts.optimizer.ff_optimizer`, `racerts.optimizer.ase` | `racerts.refine` (without `tune_ts_conformers`), `racerts.io.ase` (`rdkit_conformer_to_ase_atoms`, `write_ase_positions_to_rdkit`) |
| `racerts.optimizer.parallel` | `racerts.refine.parallel` |
| `racerts.pruner.pruner` | `racerts.prune` (also `drop_conformers_without_energy`) |
| `racerts.mol_getter.mol_getter` | `racerts.system` (the mol getters, and `build_mol`, the legacy `get_mol` logic); the atom matching of the SMILES getter: `racerts.system.match` |
| `racerts.utils` | `get_frozen_atoms`: `racerts.task.transition_state` (or `TransitionState(...).frozen_atoms(mol)`); `infer_charge_and_multiplicity`, `count_electrons`: `racerts.system`; `EV_TO_KCAL_MOL`: `racerts.utils.units`; `suppress_std`: `racerts.system.build`. `racerts.utils` itself is now the package of helpers (logging, optional imports, units). |
| `racerts.visualizer` | `racerts.io.viz` |

To replace how conformers are converted to ASE Atoms (e.g. for other charge or spin
conventions), override `ASEOptimizer._to_atoms`, or patch
`racerts.io.ase.rdkit_conformer_to_ase_atoms`. The legacy `ASEOptimizer` also honours a
patched `racerts.optimizer.ase.rdkit_conformer_to_ase_atoms`.
