# LUCI program request: racerTS (racerts)

Provides a configurable command-line workflow for generating conformer ensembles of ground-state molecules, transition states, and structures with constrained cores. The tasks share the same embedding, refinement, energy-pruning, and RMSD-pruning workflow, with different fixed atoms.

**Docs:** https://digital-chemistry-laboratory.github.io/racerts/cli/

## Installation

```bash
pip install racerts
```

RDKit >= 2023.9.6 is installed automatically as a dependency.

Optional extras:

```bash
pip install "racerts[yaml]"
```

enables YAML pipeline configuration files.

```bash
pip install "racerts[ase]"
```

enables optional ASE-based refinement. Custom ASE calculators such as xTB or MLIP calculators are configured through the Python API only.

## Flags

| Flag | What it does | Default | Example / options |
|---|---|---|---|
| `TASK` (subcommand) | Selects the conformer-generation task | none | `gs / ts / constrained` |
| `INPUT` (positional) | Molecule or starting structure | none | `CCCOC / molecule.xyz / ts.xyz / complex.xyz` |
| `-r`, `--reacting-atoms` | 0-based atoms whose connectivity changes; required for `ts` unless an explicit frozen set is supplied | none | `2 3 4` |
| `--frozen-atoms` | For `ts`, explicitly sets atoms held fixed instead of inferring them from reacting atoms | none | `0 1 2 3` |
| `--hard` | 0-based atoms held at their reference positions; required for `constrained` | none | `0 1 2 3` |
| `-s`, `--smiles` | Defines molecular topology when the input is a structure file | none | `"CCCCCC=C"` |
| `--graph` | Selects how the molecular graph is obtained from a structure file | automatic | `smiles / bonds / connect` |
| `-c`, `--charge` | Total molecular charge | `0`; for `gs` from SMILES, charge can be read from the SMILES | `-1 / 0 / 1` |
| `--multiplicity` | Spin multiplicity | lowest allowed for the electron count | `1 / 2 / 3` |
| `--config` | JSON or YAML file containing pipeline settings; CLI options override it | none | `settings.json / settings.yaml` |
| `-n`, `--n-conformers` | Number of conformers to embed; `-1` lets racerTS determine the number from molecular flexibility | `-1` | `100` |
| `--conf-factor` | Multiplier used when automatically determining the number of conformers | `80` | `120` |
| `--embed` | Distance-geometry embedding mode | task-dependent | `cmap / bounds` |
| `--etkdg`, `--no-etkdg` | Enables or disables ETKDGv3 embedding; normally enabled for ground-state searches | task-dependent | `--etkdg / --no-etkdg` |
| `--refine` | Classical force-field refinement method | `mmff` | `mmff / uff` |
| `--no-fallback` | Disables automatic graph and MMFF-to-UFF fallback behaviour | fallback enabled | `--no-fallback` |
| `--num-threads` | Number of threads used by supported workflow steps | `1` | `4` |
| `--energy-threshold` | Relative-energy cutoff used for pruning, in kcal/mol | `20.0` | `10.0` |
| `--rmsd-threshold` | Heavy-atom RMSD threshold used for duplicate pruning, in Å | `0.125` | `0.25` |
| `-o`, `--output` | Output conformer-ensemble filename | `conformer_ensemble.xyz` | `ensemble.xyz` |
| `-v`, `-vv` | Increases CLI logging verbosity | warnings only | `-v / -vv` |

## Input

racerTS exposes three explicit CLI tasks.

### Ground-state conformer generation

```bash
racerts gs "CCCOC"
```

or

```bash
racerts gs molecule.xyz
```

`gs` performs ordinary conformer generation without freezing atoms. Ground-state searches use ETKDG-based embedding by default.

The preferred input is a SMILES string or a structure format that contains reliable bond information. When an XYZ file is used, molecular connectivity and bond orders may need to be reconstructed. A SMILES can therefore be supplied with `--smiles` to define the intended molecular topology explicitly.

### Transition-state conformer generation

```bash
racerts ts ts.xyz --reacting-atoms 2 3 4 --charge 0
```

`ts` starts from a reference transition-state geometry. Reacting atoms are the atoms whose connectivity changes in the reaction.

By default racerTS preserves the reacting region during conformer generation. An explicit set of frozen atoms can instead be supplied with `--frozen-atoms`.

A SMILES can optionally be supplied with `--smiles` to define the intended molecular topology.

### Constrained conformer generation

```bash
racerts constrained complex.xyz --hard 0 1 2 3
```

`constrained` samples conformations while keeping a user-defined set of atoms fixed at their reference positions. This is suitable for molecules containing a core, binding motif, coordination environment, or other geometry that should remain unchanged.

All atom indices used by racerTS are **0-based**: the first atom is atom 0.

## Output

All three CLI tasks produce a pruned conformer ensemble.

By default the result is written to:

```text
conformer_ensemble.xyz
```

The output is a multi-structure XYZ conformer ensemble. The output filename can be changed with `--output`.

## Notes

Treat racerTS as one command-line conformer-generation program with three explicit tasks:

- `gs` — general ground-state conformer generation
- `ts` — transition-state conformer generation with a preserved reacting region
- `constrained` — conformer generation around an explicitly fixed core or motif

The normal workflow is:

```text
Embed -> Refine -> Prune by energy -> Prune by RMSD
```

Typical CLI commands are:

Ground state:

```bash
racerts gs "CCCOC" -o gs_ensemble.xyz
```

Transition state:

```bash
racerts ts ts.xyz --reacting-atoms 2 3 4 --charge 0 -o ts_ensemble.xyz
```

Constrained core:

```bash
racerts constrained complex.xyz --hard 0 1 2 3 -o constrained_ensemble.xyz
```

For general-purpose ground-state conformer generation, molecular topology should be supplied as explicitly as possible. SMILES or bond-containing SDF/MOL input is preferable to relying only on connectivity inferred from bare XYZ coordinates.

### Optional ASE calculators

racerTS can additionally use ASE calculators for higher-level refinement, for example xTB or machine-learned interatomic potentials. This requires the optional installation:

```bash
pip install "racerts[ase]"
```

Because an ASE calculator is a Python object that must be instantiated and passed to the refinement workflow, this advanced functionality belongs to the racerTS **Python API**.
