# Programs in LUCI

Generated from `src/luci/registry` by `tools/gen_programs_doc.py`. Do not edit by hand.

## LUCI-STRUCT: 3D structures

Generate and optimize 3D structures: conformer ensembles, optimized geometries and metal complexes.

| Program | Key | Inputs | Cost | Mode | Platforms | Environment | Status |
|---|---|---|---|---|---|---|---|
| [AQME CSEARCH](https://aqme.readthedocs.io/en/latest/API/aqme.csearch.html) | `aqme_csearch` | SMILES, 3D structures | CPU | Single run | Windows, Linux | aqme | tested on Linux |
| [racerTS](https://digital-chemistry-laboratory.github.io/racerts/cli/) | `racerts` | SMILES, 3D structures | CPU | Single run | Windows, Linux | racerts | untested |
| [MolSimplify](https://molsimplify.readthedocs.io/en/latest/) | `molsimplify` | none | CPU | Single run | Windows, Linux | molsimplify | untested |
| [AQME CMIN](https://aqme.readthedocs.io/en/latest/API/aqme.cmin.html) | `aqme_cmin` | 3D structures | CPU, GPU helps | Single run | Windows, Linux | aqme | tested on Linux |

## LUCI-THERMO: Energies

Energies and thermochemistry: ZPE, enthalpy, entropy, free energies and formation energies.

| Program | Key | Inputs | Cost | Mode | Platforms | Environment | Status |
|---|---|---|---|---|---|---|---|
| [GoodVibes](https://goodvibespy.readthedocs.io/en/latest/) | `goodvibes` | QM outputs | CPU | Single run | Windows, Linux, macOS | goodvibes | tested on Linux |
| [ThermoMLIP](https://github.com/chimie-paristech-CTM/ThermoMLIP) | `thermomlip` | SMILES | CPU, GPU helps | Single run | Linux | Batch (CSV): thermomlip; Single molecule: thermomlip | Batch (CSV): untested; Single molecule: untested |
| [universal_thermoGNN](https://github.com/chimie-paristech-CTM/universal_thermoGNN) | `thermognn` | SMILES | CPU, GPU helps | Single run | Windows, Linux | thermognn | untested |

## LUCI-REACT: Transition states

Transition states, reaction paths and energy profiles from reactions.

| Program | Key | Inputs | Cost | Mode | Platforms | Environment | Status |
|---|---|---|---|---|---|---|---|
| [TS-tools](https://github.com/chimie-paristech-CTM/TS-tools) | `ts_tools` | Reactions | HPC cluster, Licensed software | Single run | Linux | GFN2-xTB: tstools; g-xTB: tstools_gxtb; MLIP (UMA, GPU): tstools_mlip | GFN2-xTB: untested; g-xTB: not public yet; MLIP (UMA, GPU): not public yet |

## LUCI-FEAT: Descriptors

Molecular descriptors (electronic, steric, DFT) ready for modeling.

| Program | Key | Inputs | Cost | Mode | Platforms | Environment | Status |
|---|---|---|---|---|---|---|---|
| [AQME QDESCP](https://aqme.readthedocs.io/en/latest/API/aqme.qdescp.html) | `aqme_qdescp` | SMILES, 3D structures | CPU | Single run | Windows, Linux | aqme | tested on Linux |
| [DBSTEP](https://github.com/patonlab/DBSTEP) | `dbstep` | 3D structures | CPU | Single run | Windows, Linux, macOS | dbstep | tested on Linux |
| [Morfeus](https://digital-chemistry-laboratory.github.io/morfeus/) | `morfeus` | 3D structures | CPU | Single run | Windows, Linux | morfeus | untested |
| [Auto-QChem](https://github.com/doyle-lab-ucla/auto-qchem) | `autoqchem` | SMILES, QM outputs | HPC cluster, Licensed software | Single run | Windows, Linux | autoqchem | untested |

## LUCI-PRED: Models and predictions

Machine-learning models trained on your data, and their predictions.

| Program | Key | Inputs | Cost | Mode | Platforms | Environment | Status |
|---|---|---|---|---|---|---|---|
| [ROBERT](https://robert.readthedocs.io/en/latest/) | `robert` | CSV / tables | CPU | Single run | Windows, Linux | robert | tested on Linux |

## LUCI-DESIGN: Next experiments

Which experiments to run next: Bayesian optimization of conditions and substrate scope selection, round after round.

| Program | Key | Inputs | Cost | Mode | Platforms | Environment | Status |
|---|---|---|---|---|---|---|---|
| [EDBO+](https://github.com/doyle-lab-ucla/edboplus) | `edboplus` | CSV / tables | CPU | Iterative loop | Windows, Linux | edboplus | untested |
| [ScopeBO](https://github.com/doyle-lab-ucla/ScopeBO) | `scopebo` | SMILES, CSV / tables | CPU | Iterative loop | Windows, Linux | scopebo | untested |
| [BoReact](https://github.com/chimie-paristech-CTM/BoReact) | `boreact` | CSV / tables | CPU | Iterative loop | Windows, Linux | boreact | not public yet |

## Environments

| Key | Title | Platforms | Source | Notes |
|---|---|---|---|---|
| `aqme` | AQME | windows, linux | package index | CREST (conformer search) is only packaged for Linux; RDKit sampling works everywhere. |
| `robert` | ROBERT | windows, linux | package index |  |
| `molsimplify` | MolSimplify | windows, linux | package index |  |
| `dbstep` | DBSTEP | windows, linux, macos | package index |  |
| `racerts` | racerTS | windows, linux | package index | Installed from GitHub (the gs / ts / constrained command line is not on PyPI yet). |
| `morfeus` | Morfeus | windows, linux | package index |  |
| `goodvibes` | GoodVibes | windows, linux, macos | package index |  |
| `thermognn` | universal_thermoGNN | windows, linux | https://github.com/chimie-paristech-CTM/universal_thermoGNN (`edl`) |  |
| `thermomlip` | ThermoMLIP | linux | https://github.com/chimie-paristech-CTM/ThermoMLIP (`main`) | Linux only: ThermoMLIP uses fcntl and Linux compilers. On Windows, run LUCI inside WSL. |
| `tstools` | TS-tools (xTB) | linux | https://github.com/chimie-paristech-CTM/TS-tools (`master`) | Linux only: Gaussian 16 drives xTB through its external= keyword. |
| `tstools_gxtb` | TS-tools (g-xTB) | linux | https://github.com/maximeferrer/ts-tools-gxtb (`main`) | The ts-tools-gxtb repository is not public yet. |
| `tstools_mlip` | TS-tools (MLIP / UMA) | linux | https://github.com/maximeferrer/ts-tools-MLIP (`main`) | Beta; the ts-tools-MLIP repository is not public yet. |
| `autoqchem` | Auto-QChem | windows, linux | package index | Upstream lists Windows as untested. |
| `edboplus` | EDBO+ | windows, linux | https://github.com/doyle-lab-ucla/edboplus (`main`) | Pinned to torch 1.10 / Python 3.9 by upstream. |
| `scopebo` | ScopeBO | windows, linux | https://github.com/doyle-lab-ucla/ScopeBO (`main`) | Pinned to torch 1.10 / Python 3.9 by upstream. |
| `boreact` | BoReact | windows, linux | https://github.com/chimie-paristech-CTM/BoReact (`main`) | The BoReact repository is not public yet. |
