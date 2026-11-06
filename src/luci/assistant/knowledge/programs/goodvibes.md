# GoodVibes: upstream documentation

Source: https://github.com/patonlab/GoodVibes

## GoodVibes/README.md

===

[](https://github.com/patonlab/GoodVibes/actions/workflows/tests.yml)
[](https://badge.fury.io/py/goodvibes)
[](https://anaconda.org/conda-forge/goodvibes)
[](https://goodvibespy.readthedocs.io/en/stable/?badge=stable)
[](https://zenodo.org/badge/latestdoi/54848929)
[](https://anaconda.org/conda-forge/goodvibes)

GoodVibes computes quasi-harmonic thermochemical corrections from electronic structure calculations (Gaussian, ORCA, NWChem, QChem, xTB, ASE). It corrects the poor description of low-frequency vibrations by the rigid-rotor harmonic oscillator (RRHO) treatment using the approaches of [Grimme](http://dx.doi.org/10.1002/chem.201200497) and [Truhlar](http://dx.doi.org/10.1021/jp205508z).

#### Features

- Grimme quasi-RRHO (mRRHO) and Truhlar quasi-harmonic entropy corrections
- Head-Gordon quasi-harmonic enthalpy correction
- Variable temperature and concentration thermochemistry
- Automated vibrational frequency scaling factor lookup (~200 levels of theory)
- Single-point energy corrections (link jobs or separate files)
- Boltzmann-weighted populations and N-way stereoselectivity (`--label`)
- Potential energy surface analysis with YAML-defined pathways, stoichiometric sums (`2*A + B`), and Gconf corrections
- Structured JSON output (`--json`) for downstream pipelines
- Reaction-profile documents (`reaction-profile/1.0`, a published JSON Schema): write them with `--profile`, then plot, tabulate and convert them with `goodvibes-profile` without the output files (re-evaluating them, e.g. at another temperature, also needs `--with-conformers`); CSV tables of literature values plot the same way
- Symmetry-corrected entropy via pymsym point-group detection
- Solvent standard-state concentration and free-space corrections
- Skip re-parsing across runs with `--export` / `--import` (v1.0 unified JSON; legacy `--cache-save` / `--cache-read` retained as deprecated aliases)
- Duplicate structure detection (`--dedup`) and energy-sorted output (`--sort`)
- Supports Gaussian, ORCA, NWChem, QChem, xTB, and ASE output files

#### Installation

Requires Python >= 3.10.

```bash
pip install goodvibes
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install goodvibes
```

Or from conda-forge:

```bash
conda install -c conda-forge goodvibes
```

For development (editable install):

```bash
pip install -e .
```

#### Quick Start

```bash
goodvibes <output_file(s)> -q
```

The `-q` flag applies quasi-harmonic corrections (Grimme entropy + Head-Gordon enthalpy). Use `-h` for the full list of options.

#### Supported Programs

GoodVibes reads output files from:

- **Gaussian** (09, 16) `.log` / `.out` -- optimization, frequency, single-point, link jobs, ONIOM, VPT2 anharmonic
- **ORCA** (5, 6) `.out` -- optimization, frequency, single-point, DLPNO-CCSD(T)
- **NWChem** `.out` -- optimization, frequency, single-point
- **QChem** (6) `.out` / `.qcin` -- optimization, frequency, single-point, linked jobs
- **xTB** `.out` -- frequency calculations (ORCA/xTB integration compatible)
- **ASE** (Atomic Simulation Environment) `.extxyz` -- extended XYZ format with energy & frequency data

The program is auto-detected from the output file contents. Additional file extensions can be registered with `--custom_ext`.

#### Documentation

Full documentation is available on [Read the Docs](https://goodvibespy.readthedocs.io/en/latest/).

#### Examples

##### Example 1: Grimme-type quasi-harmonic correction with a cut-off of 150 cm<sup>-1</sup>
```bash
goodvibes examples/methylaniline.out -f 150

   Structure                    E        ZPE             H        T.S     T.qh-S          G(T)       qh-G(T)
   *********************************************************************************************************
o  methylaniline      -326.664901   0.142118   -326.514489   0.039668   0.039465   -326.554157   -326.553954
   *********************************************************************************************************

```

The output shows both standard harmonic and quasi-harmonic corrected thermochemical data (in Hartree). The corrected enthalpy and entropy values are always less than or equal to the harmonic value.

##### Example 2: Quasi-harmonic thermochemistry with a larger basis set single point energy correction link job
```bash
goodvibes examples/ethane_spc.out --spc link

   Structure                E_SPC             E        ZPE         H_SPC        T.S     T.qh-S      G(T)_SPC   qh-G(T)_SPC
   ***********************************************************************************************************************
o  ethane_spc          -79.858399    -79.830421   0.073508    -79.779414   0.027540   0.027542    -79.806954    -79.806956
   ***********************************************************************************************************************
```

This calculation contains a multi-step job: an optimization and frequency calculation with a small basis set followed by (--Link1--) a larger basis set single point energy. Note the use of the `--spc link` option. The standard harmonic and quasi-harmonic corrected thermochemical data are obtained from the small basis set partition function combined with the larger basis set single point electronic energy. In this example, GoodVibes automatically recognizes the level of theory used in the frequency calculation, B3LYP/6-31G(d), and applies the [Truhlar group scaling factors](https://t1.chem.umn.edu/freqscale/index.html) of 0.991 (harmonic, used for H<sub>vib</sub> and S<sub>vib</sub>) and 0.977 (ZPE). Use `-v 1.0` to suppress all scaling, or `--zpe-vscal Y` to override only the ZPE factor.

Alternatively, if a single point energy calculation has been performed separately, provided both file names share a common root e.g. `ethane.out` and `ethane_TZ.out` then use of the `--spc TZ` option is appropriate. This will give identical results as above.

```bash
goodvibes examples/ethane.out --spc TZ

   Structure                E_SPC             E        ZPE         H_SPC        T.S     T.qh-S      G(T)_SPC   qh-G(T)_SPC
   ***********************************************************************************************************************
o  ethane              -79.858399    -79.830421   0.073508    -79.779414   0.027540   0.027542    -79.806954    -79.806956
   ***********************************************************************************************************************
```

##### Example 3: Changing the temperature (from standard 298.15 K to 1000 K) and concentration (from standard state in gas phase, 1 atm, to standard state in solution, 1 mol/l)
```bash
goodvibes examples/methylaniline.out --temp 1000 --conc 1.0

   Structure                    E        ZPE             H        T.S     T.qh-S          G(T)       qh-G(T)
   *********************************************************************************************************
o  methylaniline      -326.664901   0.142118   -326.452307   0.218212   0.216559   -326.670519   -326.668866
   *********************************************************************************************************
```

This correction from 1 atm to 1 mol/l is responsible for the addition 1.89 kcal/mol to the Gibbs energy of each species (at 298K). It affects the translational entropy, which is the only component of the molecular partition function to show concentration dependence. In the example above the correction is larger due to the increase in temperature.

##### Example 4: Analyzing the Gibbs energy across an interval of temperatures 300-1000 K with a stepsize of 100 K, applying a (Truhlar type) cut-off of 100 cm<sup>-1</sup>
```bash
goodvibes examples/methylaniline.out --ti '300,1000,100' --qs truhlar -f 120

   Structure               Temp/K                        H        T.S     T.qh-S          G(T)       qh-G(T)
   ******************************************************************************************************
o  methylaniline            300.0              -326.514399   0.040005   0.039842   -326.554404   -326.554241
o  methylaniline            400.0              -326.508735   0.059816   0.059596   -326.568551   -326.568331
o  methylaniline            500.0              -326.501670   0.082625   0.082349   -326.584296   -326.584020
o  methylaniline            600.0              -326.493429   0.108148   0.107816   -326.601577   -326.601245
o  methylaniline            700.0              -326.484222   0.136095   0.135707   -326.620317   -326.619930
o  methylaniline            800.0              -326.474218   0.166216   0.165772   -326.640434   -326.639990
o  methylaniline            900.0              -326.463545   0.198300   0.197800   -326.661845   -326.661346
o  methylaniline           1000.0              -326.452307   0.232169   0.231614   -326.684476   -326.683921
   ******************************************************************************************************
```

Note that the energy and ZPE are not printed in this instance since they are temperature-independent. The Truhlar-type quasi-harmonic correction sets all frequencies below 120 cm<sup>-1</sup> to a value of 100. Constant pressure is assumed, so that the concentration is recomputed at each temperature.

##### Example 5: Analyzing the Gibbs Energy using scaled vibrational frequencies
```bash
goodvibes examples/methylaniline.out -v 0.95

   Structure                    E        ZPE             H        T.S     T.qh-S          G(T)       qh-G(T)
   *********************************************************************************************************
o  methylaniline      -326.664901   0.135012   -326.521265   0.040238   0.040091   -326.561503   -326.561356
   *********************************************************************************************************
```

The frequencies are scaled by a factor of 0.95 before they are used in the computation of the vibrational energies (including ZPE) and entropies.

##### Example 6: Writing Cartesian coordinates
```bash
goodvibes examples/HCN*.out --xyz
```

Optimized cartesian-coordinates found in files HCN_singlet.out and HCN_triplet.out are written to GoodVibes_output.xyz

##### Example 7: Analyzing multiple files at once
```bash
goodvibes examples/*.out --cpu

   Structure                    E        ZPE             H        T.S     T.qh-S          G(T)       qh-G(T)
   *********************************************************************************************************
o  Al_298K            -242.328708   0.000000   -242.326347   0.017670   0.017670   -242.344018   -242.344018
o  Al_400K            -242.328708   0.000000   -242.326347   0.017670   0.017670   -242.344018   -242.344018
o  H2O                 -76.368128   0.020772    -76.343577   0.021458   0.021458    -76.365035    -76.365035
o  HCN_singlet         -93.358851   0.015978    -93.339373   0.022896   0.022896    -93.362269    -93.362269
o  HCN_triplet         -93.153787   0.012567    -93.137780   0.024070   0.024070    -93.161850    -93.161850
o  allene             -116.569605   0.053913   -116.510916   0.027618   0.027621   -116.538534   -116.538537
o  benzene            -232.227201   0.101377   -232.120521   0.032742   0.032745   -232.153263   -232.153265
o  ethane              -79.830421   0.075238    -79.750770   0.027523   0.027525    -79.778293    -79.778295
o  isobutane          -158.458811   0.132380   -158.319804   0.034241   0.034252   -158.354046   -158.354056
o  methylaniline      -326.664901   0.142118   -326.514489   0.039668   0.039535   -326.554157   -326.554024
o  neopentane         -197.772980   0.160311   -197.604824   0.036952   0.036966   -197.641776   -197.641791
   *********************************************************************************************************
TOTAL CPU      0 days  2 hrs 29 mins 28 secs

```
Wildcard characters (`*`) can be used to specify all output files in a directory.

##### Example 8: Entropic Symmetry Correction
```bash
goodvibes examples/allene.out examples/benzene.out examples/ethane.out examples/isobutane.out examples/neopentane.out --symm

   Structure                    E        ZPE             H        T.S     T.qh-S          G(T)       qh-G(T)  Point Group
   **********************************************************************************************************************
o  allene             -116.569605   0.053913   -116.510916   0.026309   0.026312   -116.537225   -116.537228          D2d
o  benzene            -232.227201   0.101377   -232.120521   0.030396   0.030399   -232.150917   -232.150919          D6h
o  ethane              -79.830421   0.075238    -79.750770   0.025831   0.025833    -79.776601    -79.776603          D3d
o  isobutane          -158.458811   0.132380   -158.319804   0.033204   0.033214   -158.353008   -158.353019          C3v
o  neopentane         -197.772980   0.160311   -197.604824   0.034606   0.034620   -197.639430   -197.639444           Td
   *********************************************************************************************************************************************
```

##### Example 9: Potential Energy Surface (PES) Comparison with Accessible Conformer Correction

The profile is a [reaction-profile document](docs/source/reaction_profile.md),
`examples/gconf_ee_boltz/gconf_aminox_cat_profile.yaml`: the points and pathway, and under
`goodvibes:` which output files make up each species and how its conformers are rolled up (gconf).

```yaml
schema: reaction-profile/1.0
title: Aminoxylation (catalyst + substrate to TS)
units: kcal/mol
species:
  cat: {}
  subs: {}
  TS: {}
points:
  cat+subs: {species: cat + subs, role: reactant}
  TS: {species: TS, role: ts, display: "TS‡"}
pathways:
  Reaction: [cat+subs, TS]
style: {decimals: 2}
goodvibes:
  sources:
    default:
      cat: {files: "aminox_cat_*"}
      subs: {files: "aminox_subs_*"}
      TS: {files: "Aminoxylation_TS1_R"}
  rollup: {mode: gconf}
```

```bash
goodvibes examples/gconf_ee_boltz/*.log --pes examples/gconf_ee_boltz/gconf_aminox_cat_profile.yaml

      Structure                        E        ZPE             H        T.S     T.qh-S          G(T)       qh-G(T)
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────
o     aminox_cat_conf65_S    -517.877161   0.200789   -517.661584   0.049563   0.048445   -517.711147   -517.710028
o     aminox_cat_conf212_S   -517.875165   0.200338   -517.659623   0.051586   0.049603   -517.711210   -517.709226
o     aminox_cat_conf280_R   -517.877308   0.200869   -517.661594   0.049769   0.048566   -517.711362   -517.710160
o     aminox_subs_conf713    -361.535757   0.095336   -361.431955   0.037712   0.037587   -361.469668   -361.469543
o     Aminoxylation_TS1_R    -879.405138   0.295352   -879.087613   0.063356   0.061120   -879.150968   -879.148733
o     Aminoxylation_TS2_S    -879.404445   0.295301   -879.086800   0.063974   0.061531   -879.150774   -879.148331
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────

   Gconf correction applied to relative values

           RXN: Reaction  (kcal/mol)  at T = 298.15 K, p = 1 atm

     Species      ΔE    ΔZPE     ΔH     T·ΔS   T·Δqh-S   ΔG(T)   Δqh-G(T)
 ─────────────────────────────────────────────────────────────────────────
     cat+subs   0.00    0.00   0.00     0.00      0.00    0.00       0.00
     TS         4.72   -0.46   3.52   -15.89    -16.39   19.40      19.91
──────────────────────────────────────────────────────────────────────────
```

The same profile evaluated into a document, then drawn and tabulated later without the output files:

```bash
goodvibes examples/gconf_ee_boltz/*.log --pes examples/gconf_ee_boltz/gconf_aminox_cat_profile.yaml --profile aminox.json
goodvibes-profile plot aminox.json -o aminox.svg --label-points
goodvibes-profile table aminox.json -o aminox_si.md
```

See [the reaction-profile format](docs/source/reaction_profile.md) for the document, the CSV tables `goodvibes-profile` reads, and `--with-conformers`.

##### Example 10: Stereoselectivity and Boltzmann populations

```bash
goodvibes examples/gconf_ee_boltz/Aminoxylation_TS1_R.log examples/gconf_ee_boltz/Aminoxylation_TS2_S.log \
          --boltz --label R='*_R*' --label S='*_S*'

   Structure                       E        ZPE             H        T.S     T.qh-S          G(T)       qh-G(T)  Boltz
   *******************************************************************************************************************
o  Aminoxylation_TS1_R   -879.405138   0.295352   -879.091374   0.063746   0.061481   -879.155120   -879.152855  0.605
o  Aminoxylation_TS2_S   -879.404445   0.295301   -879.090562   0.064366   0.061891   -879.154928   -879.152453  0.395
   *******************************************************************************************************************

   Selectivity, Boltzmann-averaged (gibbs, T = 298.15 K)
       Species   Files   Population (%)   ΔΔG (kcal/mol)
   ★   R             1            60.50            0.000
       S             1            39.50            0.249

   Ratio R:S = 60:40   Major: R   excess = 20.98%   ΔΔG = 0.25 kcal/mol
```

`--label NAME=PATTERN` is repeatable and supports any number of buckets (N=2 reports `excess` + `ΔΔG`; N>2 reports the ratio only). The legacy `--ee "*_R*:*_S*"` flag still works with a deprecation notice and will be removed in v6.0.

#### CLI Reference

Run `goodvibes -h` for the full list of options. Key flags:

| Flag | Description | Default |
|------|-------------|---------|
| `-q` | Apply quasi-harmonic corrections (Grimme entropy + Head-Gordon enthalpy) | off |
| `-f FREQ` | Frequency cut-off for entropy and enthalpy (cm-1) | 100 |
| `--fs FREQ` | Frequency cut-off for entropy only (cm-1) | 100 |
| `--fh FREQ` | Frequency cut-off for enthalpy only (cm-1) | 100 |
| `--qs {grimme,truhlar}` | Quasi-harmonic entropy method | grimme |
| `--qh` | Apply Head-Gordon enthalpy correction only | off |
| `--temp TEMP` | Temperature in Kelvin | 298.15 |
| `--ti START,END,STEP` | Temperature interval scan | -- |
| `--conc CONC` | Concentration in mol/L (solution-phase entropy) | gas phase |
| `-v SCALE` | Vibrational frequency scaling factor (partition-function H/S) | auto |
| `--zpe-vscal SCALE` | Separate scaling factor for ZPE (Truhlar `zpe_fac`) | auto |
| `--spc SUFFIX` | Single-point energy correction (suffix or `link`) | -- |
| `--strict-spc` | With `--spc`, stop with an error when a single-point energy is missing or unparseable (default: warn and use the frequency-level energy) | off |
| `--jobs N` | Parse and compute in parallel across N worker processes (`0` = all cores) | 1 |
| `--symm` | Apply symmetry correction to entropy (pymsym) | off |
| `--pg` | Display detected point group (no entropy correction applied) | off |
| `--boltz` | Print Boltzmann-weighted populations | off |
| `--label NAME=PATTERN` | N-way selectivity bucket (repeatable, fnmatch on basenames) | -- |
| `--selectivity FILE.yaml` | Selectivity spec via YAML (alternative to `--label`) | -- |
| `--ee PATTERNS` | (deprecated) Two-species selectivity, e.g. `"*_R*:*_S*"` — use `--label` | -- |
| `--pes FILE` | YAML-defined reaction pathway analysis (legacy + true YAML auto-detected) | -- |
| `--lowest-only` | PES tables: use only each species' lowest qh-G conformer | off |
| `--json PATH` | Write structured results (schema v1.0: qcdata + thermo + selectivity + pes blocks) | -- |
| `--export PATH` | Synonym for `--json`; same v1.0 payload, intended for `--import` re-use | -- |
| `--import PATH` | Read pre-parsed data from a v1.0 JSON file (or legacy cache envelope) instead of re-parsing | -- |
| `--csv PATH` | Write per-file thermochemistry to a CSV file (requires pandas; `goodvibes[full]`) | -- |
| `--parquet PATH` | Write per-file thermochemistry to a Parquet file (requires pyarrow; `goodvibes[full]`) | -- |
| `--si PATH` | Write a per-structure Supporting Information table (`.md`, `.tex`, `.csv`, `.tsv` or `.xyz`) with a Cartesian-coordinates appendix | -- |
| `--si-units UNITS` | Energy units of the `--si` table (`hartree`, `kcal/mol`, `kJ/mol`, `eV`) | hartree |
| `--strip-plot PATH` | Save a per-species ΔG strip plot (requires `--label`/`--selectivity`; `goodvibes[plot]`) | -- |
| `--pes-plot PATH` | Save a reaction-profile plot (requires `--pes`; `goodvibes[plot]`). With `--ti` the scan temperatures are overlaid on one axes | -- |
| `--profile PATH` | With `--pes`: write the evaluated reaction-profile document (`.json`/`.yaml`); plot, tabulate or convert it later with `goodvibes-profile`, no output files needed | -- |
| `--with-conformers` | With `--profile`: embed every structure's parsed data so the document can be re-evaluated (e.g. at another temperature) without the output files | off |
| `--pes-plot-quantity Q` | Quantity drawn by `--pes-plot`: `qh_gibbs`, `gibbs`, `enthalpy`, `qh_enthalpy`, `electronic` (E), `e_zpe`, `zpe`, `entropy`, `qh_entropy` or `spc` (`--gtype` is the historical spelling) | qh_gibbs |
| `--media SOLVENT` | Solvent standard-state concentration correction | -- |
| `--freespace SOLVENT` | Free-space correction for solvent cavity | -- |
| `--invert [THRESH]` | Invert small imaginary frequencies to positive values | off |
| `--bav {global,conf}` | Moment of inertia for free-rotor entropy | global |
| `--sort [energy\|gibbs]` | Sort output by energy | -- |
| `--dedup` | Remove duplicate structures (compared within each `--label` species) | off |
| `--dedup-global` | With `--dedup` and labels, also compare structures across species | off |
| `--dp N` | Decimal places for energy output | 6 |
| `--cache-save FILE` | (deprecated) alias for `--export`; still accepted, prefer `--export` | -- |
| `--cache-read FILE` | (deprecated) alias for `--import`; still accepted, prefer `--import` | -- |
| `--custom_ext EXTS` | Additional file extensions (comma-separated) | -- |
| `--exclude PATTERN` | Glob pattern to exclude files | -- |
| `--check` | Verify consistency across input files | off |
| `--cpu` | Print total CPU time | off |
| `--xyz` | Write Cartesian coordinates to .xyz file | off |
| `--imag` | Print imaginary frequencies | off |
| `--output NAME` | Output file base name | output |
| `--nogconf` | Disable Gconf correction in PES analysis | off |
| `--graph FILE` | Graph a reaction profile from free energies | -- |

#### Dependencies

- **Python** >= 3.10
- **numpy** -- numerical computations
- **pymsym** -- point group detection and symmetry numbers
- **rich** >= 13 -- console table rendering

Optional:

- **ase** >= 3.22 (`goodvibes[ase]`) -- only needed to *write* `.extxyz` inputs with `goodvibes.ase_helper` or to drive `QCData.from_atoms` / `from_vibrations` from your own ASE workflow; parsing `.extxyz` files needs no ase
- **pyyaml** -- reaction-profile documents, PES YAML and `--selectivity FILE.yaml` (a core dependency from 4.6)
- **jsonschema** (optional) -- `goodvibes-profile validate` also checks documents against the published JSON Schema when it is installed

Build requires setuptools >= 64. See `pyproject.toml` for details.

#### Contributing

Install for development:

```bash
pip install -e .
```

Run the test suite:

```bash
pytest -v
```

Test data is organized by program:
- `tests/g16/` -- Gaussian 16 output files
- `tests/orca6/` -- ORCA 6 output files (full coverage)
- `tests/orca5/` -- ORCA 5 output files (lightweight regression layer)
- `tests/qchem6/` -- QChem 6 output files
- `tests/xtb/` -- xTB output files
- `tests/ase/` -- ASE (extended XYZ) test files

Test helpers in `tests/conftest.py` provide path resolvers (`g16path()`, `orca_path()`, `orca5_path()`, `qchem_path()`, `xtb_path()`, `ase_path()`) and categorized file lists (`G16_FREQ_FILES`, `ORCA_FREQ_FILES`, `QCHEM_FREQ_FILES`, `XTB_FREQ_FILES`, `ASE_FREQ_FILES`, etc.) used by parametrized tests.

#### Citing GoodVibes
Luchini, G.; Alegre-Requena, J. V.; Funes-Ardoiz, I.; Paton, R. S. GoodVibes: Automated Thermochemistry for Heterogeneous Computational Chemistry Data. *F1000Research*, **2020**, *9*, 291 [**DOI:** 10.12688/f1000research.22758.1](https://doi.org/10.12688/f1000research.22758.1)

#### References
1. Ribeiro, R. F.; Marenich, A. V.; Cramer, C. J.; Truhlar, D. G. *J. Phys. Chem. B* **2011**, *115*, 14556-14562 [**DOI:** 10.1021/jp205508z](http://dx.doi.org/10.1021/jp205508z)
2. Grimme, S. *Chem. Eur. J.* **2012**, *18*, 9955-9964 [**DOI:** 10.1002/chem.201200497](http://dx.doi.org/10.1002/chem.201200497)
3. Li, Y.; Gomes, J.; Sharada, S. M.; Bell, A. T.; Head-Gordon, M. *J. Phys. Chem. C* **2015**, *119*, 1840-1850 [**DOI:** 10.1021/jp509921r](http://dx.doi.org/10.1021/jp509921r)
4. Alecu, I. M.; Zheng, J.; Zhao, Y.; Truhlar, D. G.; *J. Chem. Theory Comput.* **2010**, *6*, 2872-2887 [**DOI:** 10.1021/ct100326h](http://dx.doi.org/10.1021/ct100326h)
5. Mammen, M.; Shakhnovich, E. I.; Deutch, J. M.; Whitesides, G. M. *J. Org. Chem.* **1998**, *63*, 3821-3830 [**DOI:** 10.1021/jo970944f](http://dx.doi.org/10.1021/jo970944f)
6. Pracht, P.; Grimme, S. *Chem. Sci.* **2021**, *12*, 6551-6568 [**DOI:** 10.1039/D1SC00621E](https://doi.org/10.1039/D1SC00621E)

---
#### License

GoodVibes is freely available under an [MIT](https://opensource.org/licenses/MIT) License

## GoodVibes/docs/source/cookbook.md

# Cookbook

Task-oriented recipes for the workflows that landed in v4.x. Each
section is self-contained — copy, paste, modify the inputs, run.

For background on the underlying CLI flags and Python API, see the
[programmatic API guide](api_guide.md) and the
[main README](README.md).

---

## 0. A table of numbers → a publication figure

No output files are needed. Type the relative energies into a CSV, one
column per pathway (an empty cell means the point is not on that
pathway; `role: ts` puts the value label above the bar):

```text
point,role,display,main
R,reactant,R,0.0
TS1,ts,TS1‡,18.4
Int,minimum,Int,3.2
TS2,ts,TS2‡,12.9
P,product,P,-12.1
```

```bash
goodvibes-profile plot levels.csv -o fig.svg -o fig.pdf --label-points --preset single-column
goodvibes-profile table fig.svg          # the SVG carries its numbers
```

- `--preset` sizes the figure, fonts and line widths for one journal
  column (about 85 mm), a full page width (`double-column`, about
  178 mm) or a `slide`.
- The SVG keeps its text as text, gives every bar, connector and label
  an `id` for editing in Inkscape or Illustrator, and embeds the
  reaction-profile document of what was drawn.
- The values are taken as ΔG at 298.15 K in kcal/mol unless you pass
  `--quantity`, `--temperature` and `--units`.

For error bars use the long layout, with one row per point and an
`uncertainty` column:

```text
pathway,point,role,display,value,uncertainty
main,R,reactant,R,0.0,
main,TS1,ts,TS1‡,18.4,1.5
main,Int,minimum,Int,3.2,0.8
main,TS2,ts,TS2‡,12.9,1.2
main,P,product,P,-12.1,1.0
```

From Python:

```python
from goodvibes import load_profile

prof = load_profile("levels.csv", quantity="gibbs", temperature=298.15)
fig = prof.plot(preset="single-column", label_points=True)
fig.save("fig.svg", "fig.pdf")
```

`goodvibes-profile convert levels.csv -o levels.yaml` writes the same
data as a [reaction-profile document](reaction_profile.md). Edit it to
add methods, barrier annotations or a second series. The
[gallery](gallery.md) shows what else a document can draw.

---

## 1. One file → one structured result

The lowest-friction path for notebooks and scripts. Replaces the older
15-positional-arg `calc_bbe()` constructor.

```python
from goodvibes import compute_thermo

r = compute_thermo(
    "ethane.log",
    QS="grimme",            # default — Grimme quasi-RRHO entropy
    s_freq_cutoff=50,       # cm⁻¹ — soften modes below this
    spc="TZ",
    temperature=313.15,
)

print(f"qh-G(T) = {r.qh_gibbs_free_energy:.6f} Hartree")
print(f"point group: {r.point_group}, σ = {r.symmno}")
print(f"level of theory (auto-detected): {r.level_of_theory}")
print(f"frequency scale factor: {r.freq_scale_factor} ({r.scale_factor_source})")
```

`compute_thermo` returns a frozen `ThermoResult` dataclass with every
attribute `calc_bbe` produces, plus `r.bbe` and `r.qcdata` for advanced
reads. Defaults match the CLI: gas-phase concentration (`P/RT`),
auto-lookup of the frequency scaling factor from the level of theory
via the Truhlar database. A level that is not in the database is used
unscaled with a `ScaleFactorWarning` (`r.scale_factor_source ==
"none-found"`); pass `freq_scale_factor=` to set one.

---

## 2. Batch a directory with parallel parsing → DataFrame

The most common notebook workflow: parse hundreds of conformers,
filter, sort, export.

```python
import glob
from goodvibes import compute_batch, to_dataframe
from goodvibes.constants import KCAL_TO_AU

paths = sorted(glob.glob("conformers/*.log"))
results = compute_batch(paths, jobs=8)        # 8 worker processes

df = to_dataframe(results)
df = df.sort_values("qh_gibbs_free_energy")
df["ΔG_kcal"] = (df.qh_gibbs_free_energy - df.qh_gibbs_free_energy.min()) * KCAL_TO_AU

# Drop conformers more than 3 kcal/mol above the lowest
keep = df[df["ΔG_kcal"] < 3.0]
print(f"{len(keep)} of {len(df)} conformers within 3 kcal/mol of the lowest")
keep[["name", "qh_gibbs_free_energy", "ΔG_kcal"]].to_csv("survivors.csv", index=False)
```

`jobs=0` uses all CPU cores. Output preserves input order. Pandas is
optional — install with `pip install goodvibes[full]`.

The same thing from the shell, no Python:

```bash
goodvibes conformers/*.log --jobs 8 --csv all_thermo.csv
```

---

## 3. N-way selectivity (replaces `--ee`)

The v4.1 redesign generalizes `--ee a:b` (2-bucket only) to N-way
selectivity. Each bucket is named explicitly with `--label NAME=PATTERN`
(repeatable). The patterns are `fnmatch` globs against the input
filenames — no filesystem walks.

The example fixture in `goodvibes/examples/selectivity/` is a
Diels–Alder TS set: 8 transition states across two regiochemistries
(1,2- vs 1,4-) and two diastereomers (exo / endo).

**2-way (exo vs endo)**

```bash
cd goodvibes/examples/selectivity
goodvibes DA_*.out --label exo='*_exo_*' --label endo='*_endo_*'
```

```text
Selectivity, Boltzmann-averaged (gibbs, T = 298.15 K)
       Species   Files   Population (%)   ΔΔG (kcal/mol)
       exo           4             2.56            2.156
★      endo          4            97.44            0.000

Ratio exo:endo = 3:97   Major: endo   excess = 94.88%   ΔΔG = 2.16 kcal/mol

Selectivity, Lowest conformer only (gibbs, T = 298.15 K)
       Species   Files   Population (%)   ΔΔG (kcal/mol)
       exo           1             1.84            2.355
★      endo          1            98.16            0.000

Ratio exo:endo = 2:98   Major: endo   excess = 96.31%   ΔΔG = 2.36 kcal/mol
```

The two tables answer different questions: the Boltzmann row shows the
selectivity once you average over conformers; the lowest-conformer row
shows what the selectivity would be if only the most stable TS in each
species mattered. The gap between them tells you how much of the
selectivity is driven by conformer mixing.

**4-way (regio × stereo)**

```bash
goodvibes DA_*.out \
  --label exo_12='*_exo_12*'   --label endo_12='*_endo_12*' \
  --label exo_14='*_exo_14*'   --label endo_14='*_endo_14*'
```

For N > 2 the summary line drops `excess` and `ΔΔG` (those are 2-bucket
concepts) and just reports the ratio — `Ratio exo_12:endo_12:exo_14:endo_14 = 2:97:0:0`.

**Per-species subdirectories**

If your conformers are organized into one directory per species,
`--label` patterns are matched against the immediate parent
directory's basename in addition to the file's basename. So a
layout like

```text
selectivity_separated/
  exo/
    DA_exo_12_i.out
    DA_exo_12_ii.out
    ...
  endo/
    DA_endo_12_i.out
    ...
```

works with the directory names as labels:

```bash
cd selectivity_separated
goodvibes */*out --label exo='exo*' --label endo='endo*'
```

The shell expands `*/*out` to relative paths like `exo/DA_exo_12_i.out`,
and the `'exo*'` pattern matches the parent dir `exo`. The same
patterns also keep working on flat layouts (where the species is
encoded in the filename), so you don't need to know in advance
which layout your data uses.

**JSON output**

Add `--json results.json` and the file gets two top-level blocks,
`selectivity` and `selectivity_lowest`, each with the per-species
populations, ΔΔG, ee (when N=2), and the source files for every
species. Each result also records `major`, the signed `ee_signed`, `ratio`
(major over runner-up) and each species' `ensemble_energies`
(−RT ln Σ exp(−G/RT), in Hartree).

**Strip plot**

To visualize where the selectivity comes from — lowest-TS gap vs
conformer mixing — write a per-species ΔG strip plot:

```bash
goodvibes DA_*.out \
  --label exo='*_exo_*' --label endo='*_endo_*' \
  --strip-plot selectivity.png
```

The image shows one column per species with scattered conformer
ΔG values (relative to the global lowest). A tight cluster near the
bottom of a column means that species is dominated by its lowest
conformer; a wide spread means conformer mixing is contributing.

In Python:

```python
import matplotlib.pyplot as plt
from goodvibes import compute_batch
from goodvibes.selectivity import (
    compute_selectivity, parse_label_args, assign_files_to_labels,
)
from goodvibes.plot import plot_selectivity_strip

results = compute_batch(glob.glob("DA_*.out"))
thermo = {r.file: r.bbe for r in results}          # compute_selectivity reads calc_bbe objects
labels = parse_label_args(["exo=*_exo_*", "endo=*_endo_*"])
files_per_label = assign_files_to_labels(list(thermo), labels)
sel = compute_selectivity(thermo, files_per_label, 298.15)

ax = plot_selectivity_strip(sel, {r.file: r.qh_gibbs_free_energy for r in results})
plt.savefig("selectivity.png", dpi=200, bbox_inches="tight")
```

matplotlib is in the optional `[plot]` extras (or `[full]`) — install
with `pip install goodvibes[plot]`.

**Migration from `--ee`**

```bash
# v3.x
goodvibes *.log --ee 'P_R_*:P_S_*'

# v4.x equivalent
goodvibes *.log --label R='P_R_*' --label S='P_S_*'
```

`--ee` still works with a deprecation notice; it will be removed in v6.0.

---

## 3b. Selectivity sweeps, populations and temperature scans

**How robust is the prediction?** `compute_selectivity_batch` evaluates
many selectivity jobs at once, over temperatures, quasi-harmonic entropy
cutoffs and conformer energy windows. Each file is parsed once and then
re-evaluated for every condition:

```python
from goodvibes import compute_selectivity_batch, summarize_selectivity

jobs = {"DA": {"endo": "DA_endo_*.out", "exo": "DA_exo_*.out"}}   # globs, paths, results or ConformerSets
df = compute_selectivity_batch(jobs, [298.15, 353.15],
                               s_freq_cutoffs=[50, 150],           # cm⁻¹; the nominal 100 is always included
                               conformer_windows=[0, 1.0, 3.0])    # kcal/mol above each label's lowest
for s in summarize_selectivity(df):
    print(s["temperature"], s["text"])
```

```text
298.15 ee +95 % (94 to 96 % over s_freq_cutoff 50–150 cm⁻¹, conformer window 0–3 kcal/mol)
353.15 ee +90 % (88 to 93 % over s_freq_cutoff 50–150 cm⁻¹, conformer window 0–3 kcal/mol)
```

The DataFrame has one row per job and condition, with these columns:
- `job`, `temperature`, `s_freq_cutoff`, `conformer_window`;
- `nominal`: the nominal cutoff with all conformers;
- `major` and `ee`;
- `ddG` in kcal/mol, and `ratio`;
- per label, `population[<label>]` and `n[<label>]`.

`records=True` returns plain dicts, and `quantity="electronic"` weights
energy-only ensembles (`read_xyz_frames`).

The signs follow the `SelectivityResult` conventions:
- `major` is the most populated label; on a tie, the first listed.
- `ee = (p₁ − p₂) × 100`, with the labels in the order given, so it is
  positive when the first label is the major one.
- `ddG` and `ratio` compare the major with the runner-up.

**Where does the selectivity come from?** `plot_boltzmann_histogram`
draws the conformer populations. Given a mapping, it pools the groups into
one distribution, and its legend gives each group's total:

```python
import glob
from goodvibes import ConformerSet, compute_batch
from goodvibes.plot import plot_boltzmann_histogram, plot_temperature_scan

endo = compute_batch(sorted(glob.glob("DA_endo_*.out")))
exo = compute_batch(sorted(glob.glob("DA_exo_*.out")))
ax = plot_boltzmann_histogram({"endo": endo, "exo": exo}, temperature=298.15)   # legend: endo (97.4 %), exo (2.6 %)
ax.figure.savefig("populations.png", dpi=200, bbox_inches="tight")

ax = plot_temperature_scan(ConformerSet.from_results("endo", endo), [273.15, 298.15, 323.15, 353.15])
```

`plot_temperature_scan` draws a conformer ensemble's Δqh-G, Δqh-H and
T·Δqh-S against temperature. For a reaction-profile document, it draws each
point's level across the document's series temperatures instead.

**Selectivity in a reaction-profile document.** A `selectivity` block (see
[the format](reaction_profile.md)) names the competing branch points and
the point they share. GoodVibes predicts the selectivity from each branch
barrier, for computed and declared series alike, and checks the
Curtin–Hammett preconditions:

```python
from goodvibes import load_profile

prof = load_profile("tests/profile_conformance/valid/05_selectivity.yaml")
for r in prof.evaluate_selectivity():
    print(r.name, r.major, f"{r.ee_signed:+.1f} %", r.curtin_hammett)   # er TS_R +76.7 % satisfied
```

```bash
goodvibes-profile selectivity profile.json               # summary line and branch table per block
goodvibes-profile diff before.json after.json --tolerance 0.05
```

---

## 4. PES with the new YAML format

The legacy line-based PES file (`--- # PES` markers) is auto-detected
and still works, but it isn't real YAML and has no stoichiometry
support. v4.2 adds a proper YAML schema with `pathways:` / `species:`
/ `format:` top-level keys and a `coeff*name` syntax for stoichiometric
sums.

```yaml
# azabor_PES_v2.yaml
pathways:
  Ph:
    - "R1-An + Aza-Phos"
    - "R1-Comp + THF"
    - "AmTS + THF"
    - "Azir-Comp + THF"
    - "OpenTS + THF"
    - "Syn-P + THF"

species:
  R1-An:      {files: "r1-li-3thf-c1*"}
  Aza-Phos:   {files: "azaoxy-phosphine-full*"}
  THF:        {files: "thf*"}
  R1-Comp:    {files: "r1-phosphine-2thf-full*"}
  Azir-Comp:  {files: "aziridinium-phos-full*"}
  Syn-P:      {files: "syn-product-phos-full*"}
  OpenTS:     {files: "openTS-phos-full*"}
  AmTS:       {files: "aminationTS-full-unfrz-c1*"}

format:
  units: kcal/mol
  decimals: 1
```

Stoichiometric example: a bimolecular reaction would write a point
as `"2*A + B"`. Each species' `files:` is a glob (single string) or
explicit list (`[a.log, b.log]`).

**Assigning species by directory.** When each species lives in its
own subdirectory, use `dir:` (single) or `dirs:` (list) instead of
file globs:

```yaml
species:
  R1-An:      {dir: "R1-An"}
  Aza-Phos:   {dir: "Aza-Phos"}
  AmTS:      {dir: "AmTS"}
  # combine if a species has both subdir conformers and a separate
  # explicit file:
  THF:        {files: "thf_extra.log", dir: "THF"}
```

`dir:` matches files whose immediate parent directory's basename
equals the value (or matches it as an fnmatch glob — `dir: "TS_*"`
catches every `TS_R/`, `TS_S/`, ...). Trailing `/`, `/*` or `/**`
on the dir name is ignored.

Run it from the directory above the per-species subdirectories (the
shipped `goodvibes/examples/pes` set is flat; this layout is one you
arrange yourself, e.g. one directory per species):

```bash
cd my_pes_project        # contains R1-An/, Aza-Phos/, THF/, ... subdirectories
goodvibes */*log --spc sp_tzpop --pes azabor_PES.yaml
```

The shell `*/*log` glob hands GoodVibes relative paths like
`R1-An/r1-li-3thf-c1.log` — the `dir: "R1-An"` rule sees `R1-An`
as the parent dir basename and assigns the file there.

Run it:

```bash
cd goodvibes/examples/pes
goodvibes *.log --pes azabor_PES_v2.yaml --spc sp_tzpop
```

By default each species' contribution is **gconf-corrected**: lowest
qh-G conformer + Boltzmann adjustment + the −R Σ pᵢ ln pᵢ mixing
entropy. Two flags change that:

| Mode | Flag | What it does |
| --- | --- | --- |
| gconf (default) | — | lowest + adjustment + mixing entropy |
| pure Boltzmann | `--nogconf` | Boltzmann-weighted average, no mixing entropy |
| lowest only | `--lowest-only` | use each species' single lowest qh-G conformer |

The mode tag appears in the table title:

```text
RXN: Ph  (kcal/mol)  at T = 298.15 K, p = 1 atm — lowest conformer per species
```

**Reaction-profile diagram**

```bash
goodvibes *.log --pes azabor_PES_v2.yaml --spc sp_tzpop \
                --pes-plot pes.png
```

Saves a step-plot of the pathway's qh-G profile (one column per
point, horizontal bar at each level, smooth bezier connectors).
matplotlib via `pip install goodvibes[plot]`. `--pes-plot-quantity E`
(or `H`, `G`, `E+ZPE`, ...) draws another quantity; with `--ti` the
scan temperatures are overlaid on one axes, one linestyle each.

If your PES YAML defines multiple pathways (e.g. an R-side and an
S-side TS sharing reactants and products), `--pes-plot` overlays
them on the same axes by default — different colors from the
matplotlib cycle, with a legend. The x axis is the merge of the
pathways' point sequences, so pathways of different lengths, or
branches that share a reactant, line up by point label.

For full control drop down to `plot_profile`, which returns a
`ProfileAxes` holding the figure, the axes and the drawn levels (the
same evaluation the tables use):

```python
from goodvibes import load_pes, plot_profile, Series

pes = load_pes("R_vs_S.yaml", thermo_data)        # 2-pathway YAML

# Two temperatures on one axes (linestyle per temperature; the species
# are re-evaluated at each T from their parsed inputs).
fig = plot_profile(pes, temperatures=[298.15, 373.15],
                   colors={"R": "#26a6a4", "S": "#e76f51"},
                   label_points=True)
fig.annotate_barrier("R", "A", "TS_R")          # ΔΔ between two points
fig.save("R_vs_S.svg", "R_vs_S.pdf")
print(fig.levels["qh_gibbs@298.15K"]["R"])     # {point label: kcal/mol}

# ΔE and Δqh-G on one axes; declared (literature) values as a third
# series, drawn with hollow markers and converted to the figure's units.
lit = Series.declared_from("lit", "lit. B3LYP (298 K)",
                           {"R": {"A": 0.0, "TS_R": 18.4, "B": -12.1}},
                           quantity="gibbs", temperature=298.15, units="kcal/mol")
plot_profile(pes, series=[pes.default_series("E")[0],
                          pes.default_series("qh_gibbs")[0], lit],
             layout="panels", show_conformers=True).save("compare.png")
```

Points carry a `role` (`reactant`, `minimum`, `ts`, `product`) and a
`display` label; edges between points are `step` (default),
`barrierless` (dotted connector) or `none`:

```python
path = pes.pathway("R")
path.point("TS_R").role, path.point("TS_R").display = "ts", "TS_R‡"
pes.pathways[0] = path.with_edges([("A", "TS_R"), ("TS_R", "B", "barrierless")])
```

The older `plot_pes(pes, ...)` keeps working as a thin wrapper that
returns the matplotlib Axes.

The legacy `--graph FILE.yaml` flag is still supported and reads
styling (dpi, color, title, legend, gridlines, ylim, ...) from a
YAML's `--- # FORMAT` block. It will be removed in v6.0 once
`--pes-plot` covers the remaining gaps.

**Building a profile without a PES file**

`ConformerSet`, `Point`, `Pathway` and `PESResult` can be assembled
directly from `compute_thermo` results, for example from an MLIP
workflow that never writes an output file (next recipe):

```python
from goodvibes import ConformerSet, PESResult, PESOptions, Pathway, Point, plot_profile

species = {name: ConformerSet.from_results(name, results)
           for name, results in {"R": r_confs, "TS_R": ts_r_confs, "TS_S": ts_s_confs}.items()}
pathways = [Pathway("R-path", [Point.from_label("R", species), Point.from_label("TS_R", species, role="ts")]),
            Pathway("S-path", [Point.from_label("R", species), Point.from_label("TS_S", species, role="ts")])]
pes = PESResult(pathways, PESOptions(units="kcal/mol"), temperatures=[298.15, 373.15])
plot_profile(pes).save("profile.svg")

# Ensemble properties of one species
cs = species["TS_R"]
cs.populations(298.15), cs.s_conf(298.15), cs.ensemble_free_energy(373.15)
cs.dedup()                                    # same gates as --dedup
```

The Rich tables the CLI prints are available without its logging
set-up: `goodvibes.output.pes_tables(pes)` returns one
`rich.table.Table` per pathway.

---

## 4b. MLIP / ASE workflows without output files

`QCData.from_atoms` and `QCData.from_vibrations` build the parsed
record GoodVibes needs from an ASE `Atoms`, an energy and the
vibrational analysis, so a MACE / ANI / xTB-in-ASE pipeline never has
to write an `.extxyz` first:

```python
from ase.io import read
from ase.vibrations import Vibrations
from mace.calculators import mace_off
from goodvibes import QCData, compute_thermo, ConformerSet

calc = mace_off(model="medium")
results = {}
for label, pattern in {"R": "R_c*.xyz", "TS_R": "TS_R_c*.xyz", "TS_S": "TS_S_c*.xyz"}.items():
    results[label] = []
    for i, atoms in enumerate(read(pattern, index=":")):
        atoms.calc = calc
        vib = Vibrations(atoms, delta=0.01, name=f"vib_{label}_{i}"); vib.run()
        qc = QCData.from_vibrations(atoms, vib.get_vibrations(), atoms.get_potential_energy(),
                                    name=f"{label}_c{i}", method="MACE-OFF23",
                                    job_type="TS" if label.startswith("TS") else "Freq")
        results[label].append(compute_thermo(qcdata=qc, QS="grimme", temperature=298.15))

species = {label: ConformerSet.from_results(label, rs) for label, rs in results.items()}
```

What the constructors do:

- energies default to eV (`energy_units="hartree"`, `"kcal/mol"`,
  `"kJ/mol"` otherwise), frequencies to cm⁻¹ (`"eV"`, `"meV"`); a
  negative or complex frequency is an imaginary mode;
- `from_vibrations` drops the 6 (5 for a linear molecule)
  translational/rotational modes of a 3N finite-difference Hessian,
  takes an imaginary mode smaller than 15 cm⁻¹ (`imag_threshold_cm1`)
  as numerical noise (real at |ν|, with a `RuntimeWarning`) and warns
  when a `job_type="TS"` structure does not have exactly one imaginary
  mode or a minimum has any;
- masses are the most-abundant-isotope values QC programs use
  (`masses="atoms"` takes ASE's standard weights); the point group and
  symmetry number come from pymsym when it is installed (`symm="auto"`),
  or pass `symm=<int>`;
- `method=` is recorded as `level_of_theory`; when it matches an entry
  of the scaling-factor database the usual scale factors apply. An MLIP
  (a `method` naming no basis set, such as `MACE-OFF23`) is used unscaled
  by design (`scale_factor_source == "mlip-unscaled"`); a QM level the
  database lacks is used unscaled with a `ScaleFactorWarning`.

`compute_batch` accepts `QCData` objects alongside paths, and
`ThermoResult.name` / `program` are the `name=` given and `"ase"`.

**DFT//MLIP composites.** `QCData.with_single_point` attaches a
higher-level single-point energy to a structure, in place of a `--spc`
output file: enthalpies and free energies use it, the frequencies (and their
scale factor) stay those of the MLIP.

```python
composite = qc.with_single_point(-232.3301, "hartree", "wB97X-D/def2-TZVP")
r = compute_thermo(qcdata=composite)      # r.spc_applied is True
```

The units are required. The attached energy survives re-evaluation at
other temperatures, `--export` caches and embedded conformers.

**Ensembles in one file.** `read_xyz_frames` reads every frame of a
multi-frame `.xyz` / `.extxyz` (a CREST `crest_conformers.xyz`, an xtb
trajectory, or MLIP energies written with `ase.io.write`) as an energy-only
`QCData`. Weighted by the electronic energy, an ensemble gives Boltzmann
populations and its ensemble energy:

```python
from goodvibes import ConformerSet, compute_batch, read_xyz_frames

frames = read_xyz_frames("crest_conformers.xyz", method="GFN2-xTB")
ens = ConformerSet.from_results("crest", compute_batch(frames), weight_by="electronic")
print(ens.populations(298.15)[:5], ens.lowest_index())
```

A plain `.xyz` comment line gives the energy as a bare number (CREST) or
`energy: <value>` (xtb), in hartree. An extxyz one gives it as `energy=`,
`free_energy=` or `total_energy=` (eV, the ASE convention), or as
`scf_energy=` (hartree). `energy_key=` and `energy_units=` override the
key and the units. Free energies need frequencies, so the thermochemical
quantities of these frames are None.

---

## 4c. Reaction-profile documents and the file-free `goodvibes-profile`

`--profile PATH` writes the evaluated profile as a
[reaction-profile document](reaction_profile.md): points, pathways, one
series of the plotted quantity per temperature, and provenance. With
`--with-conformers` it also carries every structure's parsed data, so it
can be re-evaluated at another temperature without the outputs.

```bash
cd goodvibes/examples/pes
goodvibes *.log --spc sp_tzpop --pes azabor_PES_v2.yaml --profile azabor.json --with-conformers
goodvibes-profile plot azabor.json -o azabor.svg --label-points
goodvibes-profile evaluate azabor.json -o hot.json --temperatures 298.15,373.15
goodvibes-profile table hot.json -o azabor_si.md
```

A CSV of literature values is a profile too, and a document can mix
computed and declared series (hollow markers) with barrier annotations:

```bash
goodvibes-profile plot levels.csv -o lit.svg --quantity gibbs --temperature 298.15
goodvibes-profile convert levels.csv -o lit.yaml     # then add series, methods, annotations by hand
```

A document with a DFT and an MLIP method can give each its own
thermochemistry options. `goodvibes.thermo.by_method` re-evaluates the
method's structures with them:

```yaml
goodvibes:
  sources:
    dft:  {R: {files: "R_dft*"}, TS: {files: "TS_dft*"}}
    mace: {R: {files: "R_mace*"}, TS: {files: "TS_mace*"}}
  thermo:
    by_method:
      mace: {freq_scale_factor: 1.0, QS: truhlar, s_freq_cutoff: 50}
```

---

## 4d. Rates, the energy span and an SI table

`goodvibes-profile kinetics` turns a profile into Eyring rates. Each
transition state is one step, from the last intermediate before it to the
first one after it; `--span` adds the energy span model (Kozuch and Shaik)
with the turnover-determining states and the TOF:

```yaml
# cycle.yaml
schema: reaction-profile/1.0
units: kcal/mol
points:
  I0: {role: reactant}
  TS1: {role: ts}
  I1: {role: minimum}
  TS2: {role: ts}
  P: {role: product}
pathways:
  cycle: [I0, TS1, I1, TS2, P]
series:
  - id: G
    quantity: gibbs
    temperature: 298.15
    source: declared
    levels:
      cycle: {I0: 0.0, TS1: 15.0, I1: -10.0, TS2: 8.0, P: -5.0}
```

```text
$ goodvibes-profile kinetics cycle.yaml --span
pathway cycle, series G, T = 298.15 K (kcal/mol)
  I0 -> TS1 -> I1: barrier 15.00 (from the lowest point before it 15.00), k = 62.8 s-1, half-life 0.011 s
  I1 -> TS2 -> P: barrier 18.00 (from the lowest point before it 18.00), k = 0.397 s-1, half-life 1.74 s
energy span 20.00 kcal/mol (TDTS TS1, TDI I1, TDTS before TDI: + ΔG_r), ΔG_r -5.00 kcal/mol, TOF 0.0131 s⁻¹ at 298.15 K
```

The last point closes the cycle (ΔG_r = last − first). Here the span is
not the largest step barrier (18.0): TS1 comes before the deep I1, so the
next turnover crosses it at 15.0 − 5.0 = 10.0 above I1, 20.0 in all.
`-o steps.csv` (or `.md`) writes the step table and `--json` prints
everything. `--mikimo reaction_data.csv` writes the input of
[mikimo](https://github.com/digital-chemistry-laboratory/mikimo) for
microkinetic modelling, one row per pathway (`--pathway a,b`), with the
points renamed to its `INT0, TS1, INT1, …, Prod` convention.

The same from Python:

```python
from goodvibes import eyring_rate, rate_ratio
from goodvibes.profile import load_profile

prof = load_profile("cycle.yaml")
es = prof.energy_span()             # EnergySpan: tdts, tdi, span, tof, control, ...
es.control                          # degree of TOF control of each state
prof.step_table()                   # one dict per step: barrier, k, half-life, ...
prof.write_mikimo("reaction_data.csv")
eyring_rate(20.0)                   # s⁻¹ at 298.15 K, kcal/mol
rate_ratio(15.0, 16.0)              # k(15.0) / k(16.0) = 5.41
```

`--si` writes the per-structure table a Supporting Information needs: E
(and the single point when `--spc` applied one), ZPE, H, T·S, T·qh-S, G,
qh-G, the imaginary modes, the three lowest real modes, the scale factors
and their source, the point group and symmetry number and their source,
the level of theory and the temperature, then the Cartesian coordinates.

```bash
goodvibes *.log --spc sp_tzpop --si si.md --si-units kcal/mol
```

The format follows the extension: `.md` and `.tex` (booktabs) hold the
table and a coordinates appendix, leaving out columns empty for every
structure; `.csv`/`.tsv` hold every column and write the coordinates next to
them as `<name>_coordinates.xyz`; `.xyz` holds only the coordinates. From
Python, `goodvibes.write_si(results, "si.tex", units="kcal/mol",
decimals=2)` or `si_rows(results)` for the rows.

---

## 5. PES + JSON for downstream analysis

```bash
goodvibes *.log --pes azabor_PES_v2.yaml --spc sp_tzpop --json pes.json
```

The JSON gets a `pes` block (schema v1.0):

```python
import json

with open("pes.json") as f:
    payload = json.load(f)

for path in payload["pes"]["pathways"]:
    print(f"\n=== {path['name']} ({path['units']}) ===")
    for pt in path["points"]:
        print(f"  {pt['label']:25s}  ΔqhG = {pt['relative']['qh_g']:+7.2f}")
```

Each point carries `label`, `species` (name + coefficient + resolved
files), and `relative` (Δ-values for E, ZPE, H, qh-H, T·S, T·qh-S, G,
qh-G, plus SPC variants when `--spc` was set). Plug straight into
plotting libraries or downstream pipelines.

---

## 6. Parse once, re-analyze many times

QC outputs are slow to parse, especially for large conformer ensembles
or composite-method SPCs. The unified v1.0 JSON payload (`--export`)
captures every parsed field once; subsequent runs read it back via
`--import` and skip the QC files entirely. Useful for re-running at a
different temperature, concentration, frequency cutoff, or quasi-RRHO
scheme without touching the original `.log`/`.out` files.

```bash
# First pass — parse + apply SPC + export the structured payload.
goodvibes conformers/*.log --spc TZ --export thermo.json

# Re-run at 350 K with the same files but no QC parsing. Re-pass --spc
# to keep the cached SPC numbers driving G(T)_SPC; drop it for plain G.
goodvibes --import thermo.json --spc TZ -t 350

# Re-run with the Truhlar frequency-raising entropy scheme and a
# stricter low-frequency cutoff. Still no parsing.
goodvibes --import thermo.json --spc TZ --qs truhlar -f 150

# Combine cached --spc with selectivity at a new temperature.
goodvibes --import thermo.json --spc TZ -t 313.15 \
          --label R='cat_R*' --label S='cat_S*'
```

`--export` writes the same payload as `--json`, so a single file covers
both downstream pipelines and re-import. Once exported, the original
`.log`/`.out` files can be archived, moved, or deleted — `--import`
works with just the JSON. The `--spc` energies are cached on the QCData
record, so re-passing `--spc <suffix>` reuses them without ever
re-reading the SPC files.

---

## See also

- The full CLI flag table in the [main README](README.md).
- The [programmatic API reference](api_guide.md) for `compute_thermo`,
  `compute_batch`, `ThermoResult`, and `to_dataframe`.
- The full module reference covers `goodvibes.pes_loader`,
  `goodvibes.pes_model`, `goodvibes.selectivity`, etc., for users
  embedding GoodVibes in larger pipelines.

## GoodVibes/docs/source/reaction_profile.md

# The reaction-profile format

`reaction-profile/1.x` is a small, tool-independent document format for
reaction energy profiles: the species and points of a mechanism, the
pathways through them, and one or more *series* of relative energies
(computed by GoodVibes from quantum-chemistry or MLIP data, or typed in from
a paper). One document is the data behind a figure, its table and its
provenance. Version 1.1 adds `selectivity`: competing branches and the
selectivity their barriers predict.

- **Status.** 1.x is a draft until a second, independent tool reads and
  writes it; minor versions only ever add optional keys.
- **Licence.** The JSON Schema and this specification text are CC0-1.0
  (public domain); GoodVibes itself is MIT.
- **Schema.** [`reaction-profile-1.1.schema.json`](https://goodvibespy.readthedocs.io/en/latest/reaction-profile-1.1.schema.json)
  (JSON Schema draft 2020-12), installed with GoodVibes; it validates 1.0
  and 1.1 documents. The 1.0 schema,
  [`reaction-profile-1.0.schema.json`](https://goodvibespy.readthedocs.io/en/latest/reaction-profile-1.0.schema.json),
  stays published unchanged.
- **Reference implementation.** `goodvibes.profile` (Python) and the
  `goodvibes-profile` command.
- **Conformance kit.** `tests/profile_conformance/` in the repository:
  documents a reader must accept (`valid/`), reject for structural reasons
  (`invalid-structural/`, also rejected by the JSON Schema) and reject for
  referential reasons (`invalid-semantic/`, which a JSON Schema cannot
  express).

## A minimal profile

Typed-in values, no QC data, 20 lines:

```yaml
schema: reaction-profile/1.0
title: Minimal profile
units: kcal/mol
points:
  R:   {role: reactant}
  TS1: {role: ts, display: "TS1‡"}
  Int: {role: minimum}
  TS2: {role: ts, display: "TS2‡"}
  P:   {role: product}
pathways:
  main: [R, TS1, Int, TS2, P]
series:
  - id: G
    label: "ΔG (298 K)"
    quantity: gibbs
    temperature: 298.15
    source: declared
    levels:
      main: {R: 0.0, TS1: 18.4, Int: 3.2, TS2: 12.9, P: -12.1}
```

```bash
goodvibes-profile plot minimal.yaml -o minimal.svg
```

## Document structure

A document is a YAML or JSON mapping. Only `schema` and `pathways` are
required.

| Key | Type | Meaning |
| --- | --- | --- |
| `schema` | string | `reaction-profile/1.<minor>` |
| `title`, `description` | string | free text |
| `units` | `kcal/mol` \| `kJ/mol` \| `eV` \| `hartree` | units of every level in the document (default `kcal/mol`) |
| `ensemble` | `ideal-gas` | the statistical ensemble; the only one defined in 1.0 |
| `default_temperature` | number > 0 | K; used by computed series without a temperature (default 298.15; the `goodvibes` command evaluates them at its run temperature instead) |
| `species` | mapping | identity of each species (no files, no values) |
| `points` | mapping | the nodes of the profile |
| `pathways` | mapping | ordered points, a zero and edges |
| `order` | list | optional x order of point ids across all pathways |
| `methods` | mapping | provenance of the series (program, level of theory, ...) |
| `series` | list | the energies: one line set on the axes, one column set in a table |
| `annotations` | list | barriers and spans to mark on the figure |
| `selectivity` | list | (1.1) competing branches sharing a reference point |
| `style` | mapping | presentation hints |
| `provenance` | mapping | who made the document, from what |
| `goodvibes` | mapping | GoodVibes' recipe namespace; other readers ignore it |
| `x-…` | any | extension keys; preserved, never validated |

### species

`name: {smiles, inchi, formula, name, charge, multiplicity}`, every key
optional (`{}` or `null` is fine). Species carry identity only; where their
structures come from belongs to a tool's namespace.

### points

`id: {species, role, display}`.

- `species` is a stoichiometric sum, as a string (`"A + 2*B"`) or a mapping
  (`{A: 1, B: 2}`, required when a species name contains `+`). Omit it for a
  point that only appears in declared series.
- `role` is `reactant`, `minimum` (default), `ts` or `product`. A figure
  labels transition states above their bar and other points below.
- `display` is the label a figure prints (default: the id), e.g. `"TS1‡"`.

A pathway may name a point by its species sum without listing it under
`points` (`pathways: {p: ["A + B", "TS"]}` with species `A`, `B`, `TS`
declared); the point is created with that id.

### pathways

`name: {points: [ids], zero: id, edges: [...]}`, or just the list of ids.

- `zero` (default: the first point) is the reference every level of the
  pathway is relative to. It may be any defined point.
- Edges default to one `step` between each pair of consecutive points. A
  listed edge `{from, to, kind}` replaces the default edge between the same
  two points or adds a new one; `kind` is `step`, `barrierless` (drawn
  dotted) or `none` (no connector).
- Pathways may have different lengths and share points; a figure aligns
  them on one x axis by point id (`order` overrides the merged order).

### methods

`id: {program, model, level_of_theory, solvent, standard_state,
frequency_scaling, quasi_harmonic, hessian, reference, description}`, all
optional and free-form, e.g.
`standard_state: {concentration_M: 1.0}` or `{pressure_atm: 1}`,
`reference: {doi, note}`.

### series

`{id, label, method, quantity, temperature, source, levels, uncertainty,
style, standard_state}`; `id` and `quantity` are required, ids are unique.

- `source: declared` — typed-in values; `levels` is required and the series
  is never re-evaluated. `source: computed` (default) — evaluated by a tool
  from structures; its `levels` are absent until it is evaluated.
- `levels` is `{pathway: {point: value}}`: values in the document `units`,
  relative to that pathway's zero. A point missing from a pathway's levels
  is not drawn; `null` means the point is on the pathway but its value is
  unknown.
- `uncertainty` has the same shape, values ≥ 0.
- `temperature` in K (`null` for a temperature-independent value).
- `style` holds drawing hints such as `{linestyle: dashed}`.

`quantity` is one of:

| id | label | meaning |
| --- | --- | --- |
| `spc` | ΔE_SPC | single-point electronic energy |
| `electronic` | ΔE | electronic energy at the frequency level |
| `zpe` | ΔZPE | zero-point vibrational energy |
| `e_zpe` | ΔE+ZPE | electronic energy (single point when applied) plus ZPE |
| `enthalpy` | ΔH | enthalpy |
| `qh_enthalpy` | Δqh-H | quasi-harmonic enthalpy (Head-Gordon) |
| `entropy` | T·ΔS | T times the RRHO entropy |
| `qh_entropy` | T·Δqh-S | T times the quasi-harmonic entropy |
| `gibbs` | ΔG(T) | Gibbs energy |
| `qh_gibbs` | Δqh-G(T) | quasi-harmonic Gibbs energy |

GoodVibes also accepts aliases on input (`G`, `E`, `H`, `qh-G`, ...) and
writes the canonical id.

### annotations

`{type: barrier | span, pathway, from, to, series, label}` marks the
difference `to − from` on one pathway (in `series`, default the first
drawn one).

### selectivity (1.1)

Each entry names points that compete from one shared point: enantiomeric or
diastereomeric transition states, regioisomeric pathways, a chemoselective
choice.

```yaml
schema: reaction-profile/1.1
selectivity:
  - id: er                     # unique
    label: R vs S              # optional
    kind: enantio              # enantio | diastereo | regio | chemo | other (default)
    reference: Int             # the point the branches leave from
    branches: [TS_R, TS_S]     # at least two points, in the order that sets the ee sign
    series: G                  # optional: the series to use (default: every series with the levels)
    interconversion: TS_swap   # optional: the barrier between the states feeding the branches
```

**What it predicts.** For a series, each branch's barrier is
`ΔG‡ᵢ = level(branchᵢ) − level(reference)`, both read on one pathway that
holds the two points (so pathways with different zeros are fine). The
branch populations are the Curtin–Hammett distribution
`pᵢ = exp(−ΔG‡ᵢ/RT) / Σⱼ exp(−ΔG‡ⱼ/RT)` at the series' temperature
(`default_temperature` when it has none). A computed series rolled up over
conformers gives each branch's ensemble free energy, so the conformers of
every branch count. Declared series work too, so literature values predict
a selectivity the same way.

**Conventions.**
- The *major* branch has the largest population; on an exact tie, the
  first listed.
- With two branches, `ee = (p₁ − p₂) × 100` with the branches in the
  order listed: positive when the first branch is the major one. The
  excess without a sign is `|ee|`, and `ΔΔG‡ = RT ln(p_major/p_minor) ≥ 0`.
- With more branches, `ratio = p_major / p_runner-up`.

**Curtin–Hammett.** The distribution assumes the states feeding the
branches interconvert faster than they react, from the reference as their
common ground state. A reader reports the assumption as:
- *violated* when a branch lies at or below the reference, when a point
  between the reference and a branch on its pathway lies below the
  reference (a deeper resting state, so the energy span, not the barrier
  from the reference, applies), or when the `interconversion` barrier (its
  level minus the reference's) is not lower than the lowest branch
  barrier;
- *satisfied* when a lower `interconversion` barrier is given;
- *assumed* otherwise.

A branch that is not a transition state gets a note: its population is an
equilibrium ratio, not a kinetic selectivity.

### style

`{preset, layout: overlay | panels, connector: bezier | linear | step,
label_points: bool, decimals: 0-6, figsize: [w, h]}`, all hints a reader
may ignore. `preset` names a target for the figure:

| preset | figure | text |
| --- | --- | --- |
| `none` (default) | sized to the profile | the plotting library's defaults |
| `single-column` | about 85 mm wide (3.35 × 2.6 in) | 7 pt; value labels 6 pt |
| `double-column` | about 178 mm wide (7.0 × 3.2 in) | 8 pt; value labels 7 pt |
| `slide` | 16:9 (10 × 5.6 in) | 16 pt; value labels 14 pt |

An explicit `figsize` overrides the preset's.

### provenance

Free-form. GoodVibes writes `{tool, goodvibes_version, generated_at,
invocation, inputs: [{file, species, method, sha1}], warnings}`.

## Rules a reader enforces

The JSON Schema checks structure. A conforming reader additionally rejects:

1. a pathway point, zero, `order` entry or edge end that is not a defined
   point (or, for pathway points, a sum of declared species);
2. an edge whose ends are not both on the pathway, or an `order` that omits
   a pathway point;
3. a point that uses an undeclared species;
4. a series whose `levels` / `uncertainty` name an unknown pathway, or a
   point that is neither on that pathway nor its zero;
5. duplicate series ids, and a `method` that is defined nowhere;
6. an annotation naming an unknown pathway, point or series;
7. (1.1) a selectivity entry with a duplicate id, a reference, branch or
   `interconversion` point that is not defined, a branch that is the
   reference or listed twice, a branch or `interconversion` point on no
   pathway with the reference, or an unknown `series`.

Unknown keys that do not start with `x-` produce a warning (an error in
strict mode).

## Versioning

`reaction-profile/MAJOR.MINOR`. A minor adds optional keys only; a reader
of 1.0 reads any 1.x document, warning that keys it does not know are
ignored. A major version changes meaning and is refused by readers of the
previous major.

A document using a 1.1 key must declare `reaction-profile/1.1`: a
`selectivity` block in a 1.0 document is an error. A writer should declare
the oldest version that can express the document: GoodVibes writes 1.0
unless the document has a `selectivity` block, so a 1.0 reader reads
everything else it writes without a warning.

## The GoodVibes namespace

Everything GoodVibes needs to *compute* a series lives under `goodvibes:`.

```yaml
goodvibes:
  sources:                   # method -> species -> which output files
    default:
      R1-An:  {files: "r1-li-3thf-*"}         # glob on the file stem
      AmTS:   {dir: "AmTS"}                     # every file in that directory
      THF:    {files: [thf.log], dirs: ["THF_*"]}
  rollup: {mode: gconf, weight_by: qh_gibbs}   # gconf | boltzmann | lowest
  thermo: {QS: grimme, QH: false, s_freq_cutoff: 100.0, spc: sp_tzpop}
  dedup: {e_cutoff: 0.05, ro_cutoff: 0.01}
  conformers: {...}          # written by --with-conformers; see below
```

`goodvibes.thermo` records the options the structures were computed with.
Its `by_method` key maps a method id to the options that method sets for
itself: `QS`, `QH`, `s_freq_cutoff`, `h_freq_cutoff`, `concentration`,
`freq_scale_factor`, `zpe_scale_factor`, `solv`, `invert`, `symm` and
`inertia`.

```yaml
  thermo:
    QS: grimme
    by_method:
      mace: {freq_scale_factor: 1.0, QS: truhlar, s_freq_cutoff: 50}
```

When a document is evaluated, that method's structures are re-evaluated with
these options in place of the ones they were computed with, so a DFT and an
MLIP method can differ in scaling and qRRHO settings within one evaluation.
Setting either scale factor resolves both again: a `freq_scale_factor`
alone sets both, and a factor that is left out or null is looked up for
the level of theory. A method id that is not defined, an unknown option and
`spc` / `strict_spc` (the single point is read with the output files) are
errors. The re-evaluation needs the parsed structures: thermo data from
`compute_thermo` / `calc_bbe.from_options`, the `goodvibes` command, or
embedded conformers.

`goodvibes.conformers` (written with `--with-conformers` or
`Profile.evaluate(..., with_conformers=True)`) stores every structure's
parsed data and thermochemistry options. A document that carries them can be
re-evaluated at any temperature, redrawn and retabulated with no output
files: the azabor example (about 100 Gaussian outputs) becomes a 380 KB JSON
file (`goodvibes/examples/profiles/azabor_profile.json`).

## Making and using documents

**From output files** (the `goodvibes` command):

```bash
goodvibes *.log --spc sp_tzpop --pes azabor_PES_v2.yaml --profile azabor.json
goodvibes *.log --pes profile.yaml --profile evaluated.json --with-conformers
goodvibes *.log --pes profile.yaml --json out.json      # payload 1.1: the `profile` block
```

`--pes` accepts a reaction-profile document, the v2 PES YAML or the legacy
`--- # PES` text; the two older formats are upgraded (point ids are their
point labels). A v2 / legacy file gets one computed series of
`--pes-plot-quantity` per temperature (`--ti` gives several). A
reaction-profile document keeps its own series, and `--pes-plot` draws them
with its declared values and annotations. `--nogconf` and `--lowest-only`
override the document's `goodvibes.rollup`; without them the document's
rollup is used.

**Without output files** (`goodvibes-profile`):

```bash
goodvibes-profile validate profile.yaml [--strict]
goodvibes-profile plot azabor.json -o azabor.svg -o azabor.pdf [--series ID,...] [--layout panels] [--preset single-column]
goodvibes-profile table azabor.json [-o table.csv | table.md] [--long]
goodvibes-profile convert levels.csv -o profile.yaml --quantity gibbs --temperature 298.15
goodvibes-profile convert old_pes.yaml -o profile.yaml          # v2 / legacy -> explicit form
goodvibes-profile evaluate azabor.json -o hot.json --temperatures 298.15,373.15
goodvibes-profile plot azabor.json --temperatures 273,373 -o scan.png
goodvibes-profile selectivity profile.json [--id er] [--temperatures 273,298] [-o sel.csv | --json]
goodvibes-profile diff old.json new.json [--tolerance 0.05] [--series G] [--json]
```

`selectivity` prints each block's major branch, signed ee, ΔΔG‡,
Curtin–Hammett status and branch table. `diff` lists what changed between
two documents (points, pathways, series metadata, every level beyond
`--tolerance` after converting to one set of units, selectivity blocks and
annotations) and exits 1 when they differ. The `goodvibes` command prints a
document's selectivities after its PES tables, and `--json` adds them as a
`profile_selectivity` list.

`evaluate` and `--temperatures` need embedded conformers. A GoodVibes
`--json` payload with a `profile` block is accepted wherever a document is,
and so is an SVG figure GoodVibes saved.

**Figures carry their data.** An SVG written by `goodvibes-profile plot`,
`Profile.plot(...).save` or `ProfileAxes.save` has:
- text kept as text;
- an `id` on every bar, connector, value label, error bar and barrier
  marker (for example `bar-G-main-TS1`);
- a `<metadata id="goodvibes-reaction-profile">` element holding, as JSON,
  the reaction-profile document of what was drawn (the drawn series with
  their levels and uncertainties, no embedded conformers) and an index from
  each `id` to the series, pathway and point it shows.

`load_profile("fig.svg")` and `goodvibes-profile table fig.svg` read the
numbers back; `--no-embed` (`save(..., embed=False)`) leaves the document
out. A series' `uncertainty` is drawn as ± error bars (`--no-uncertainty`
to omit them).

**Tables of relative energies.** A CSV (or TSV) is read as a declared-only
profile. Wide layout: a `point` column, optional `role` and `display`, then
one column per pathway (`pathway:series` for several series); an empty cell
means the point is not on that pathway, `null` an unknown value. Long
layout: `pathway, point, value` plus optional `series, label, quantity,
temperature, units, method, role, display, uncertainty`.

```text
point,role,display,Ph,Ph-lit
R,reactant,R,0.0,0.0
TS1,ts,TS1‡,20.1,18.4
P,product,P,-12.6,-12.1
```

**From Python:**

```python
import glob
from goodvibes import compute_batch, load_profile

prof = load_profile("profile.yaml")                 # .yaml/.json/.csv, v2 or legacy PES
results = compute_batch(glob.glob("*.log"), spc="sp_tzpop")
ev = prof.evaluate(results, temperatures=[298.15, 373.15], with_conformers=True)
ev.dump("profile.json")                             # .json / .yaml
fig = ev.plot(label_points=True)                    # ProfileAxes
fig.save("profile.svg")
ev.to_dataframe("long")                             # pandas, one row per pathway × point × series
ev.write_table("si_table.md")
ev.evaluate_selectivity()                           # 1.1 selectivity blocks -> [SelectivityResult]
ev.diff(load_profile("other.json"), tolerance=0.05) # ProfileDiff; empty when they agree
```

`Profile.from_table(...)`, `Profile.from_pes_result(pes)` (for a model built
in Python) and `validate_document(mapping)` complete the API; see
`goodvibes.profile`.

## GoodVibes/docs/source/api_guide.md

# Programmatic API

Starting with **v4.2**, GoodVibes exposes a clean kwargs-based Python API
in addition to the CLI. The same parser and thermochemistry engine
power both — the API just wraps `calc_bbe` in a friendlier signature
and returns a structured result.

## Quick start

```python
from goodvibes import compute_thermo

r = compute_thermo("structure.log")
print(f"qh-G(T) = {r.qh_gibbs_free_energy:.6f} Hartree")
print(f"level   = {r.level_of_theory}")
```

`compute_thermo` returns a frozen `ThermoResult` dataclass with every
attribute `calc_bbe` produces (energies in Hartree, entropies in
Hartree/K, frequencies in cm⁻¹), plus references to the underlying
`bbe` and `qcdata` for advanced use.

```python
@dataclass(frozen=True)
class ThermoResult:
    file: str                       # absolute path
    name: str                       # basename without extension
    scf_energy: float
    sp_energy: float | None         # None unless --spc was used
    zpe: float
    enthalpy: float
    qh_enthalpy: float | None       # None when QH=False
    entropy: float
    qh_entropy: float
    gibbs_free_energy: float
    qh_gibbs_free_energy: float
    frequency_wn: list[float] | None
    im_frequency_wn: list[float] | None
    inverted_freqs: list[float] | None
    point_group: str | None
    symmno: int | None
    linear_mol: bool
    multiplicity: int | None
    job_type: str | None
    level_of_theory: str | None
    program: str | None             # 'Gaussian', 'Orca', ...
    bbe: Any                        # original calc_bbe instance
    qcdata: Any                     # parsed QCData
    spc_applied: bool               # a single-point energy replaced E in H and G
    # provenance
    temperature: float              # K
    options: ThermoOptions          # every option, with the scale factors resolved
    freq_scale_factor: float
    zpe_scale_factor: float
    scale_factor_source: str | None # 'user' | 'truhlar' | 'mlip-unscaled' | 'none-found'
    symmetry_source: str            # 'output' | 'pymsym' | 'assumed' (sigma = 1)
    n_imag: int | None              # imaginary modes in the output
```

`scale_factor_source` says where the vibrational scale factors came from:
passed in (`user`), the Truhlar database for the level of theory
(`truhlar`), unscaled by design for an MLIP input (`mlip-unscaled`: from ASE,
with a level of theory that names no basis set, e.g. `MACE-OFF23`),
or not found (`none-found`: the frequencies are used unscaled, and a
`goodvibes.thermo.ScaleFactorWarning` says so instead of a silent 1.0). It is
None, like `n_imag`, for an input without frequencies. `to_dataframe` has a
column for each (not `options`).

## Common options

```python
r = compute_thermo(
    "structure.log",
    QS="grimme",            # default — Grimme quasi-RRHO entropy
    s_freq_cutoff=50,       # cm⁻¹ — soften vibrational modes below this
    spc="TZ",               # use 'structure_TZ.log' for the single point
    temperature=313.15,     # K
    concentration=1.0,      # mol/L; defaults to gas-phase 1 atm
    freq_scale_factor=None, # None → auto-lookup from level of theory
)
```

All keyword names match the CLI flags. Defaults match what the CLI
does when those flags aren't passed.

## Batch and parallel processing

```python
from goodvibes import compute_batch
import glob

paths = glob.glob("conformers/*.log")

# Sequential (default).
results = compute_batch(paths)

# Parallel: spawn 8 worker processes.
results = compute_batch(paths, jobs=8)

# Use all available CPU cores.
results = compute_batch(paths, jobs=0)
```

`compute_batch` preserves input order. With `jobs > 1`, parsing and
thermochemistry run in a `ProcessPoolExecutor`; on a typical laptop
this gives 2–3× speedup at 8 cores once the file count is large enough
to amortise process startup (~50 files).

## Pandas DataFrame export

```python
from goodvibes import compute_batch, to_dataframe

results = compute_batch(glob.glob("*.log"))
df = to_dataframe(results)
df.to_csv("thermo.csv", index=False)
df.sort_values("qh_gibbs_free_energy").head()
```

`to_dataframe` requires pandas; install with `pip install goodvibes[full]`
(includes pandas, pyarrow, matplotlib, ase and pyyaml).

The CLI flag `--csv PATH` does the same thing without leaving the shell:

```bash
goodvibes *.log --csv thermo.csv
```

## Supporting Information tables

```python
from goodvibes import compute_batch, si_rows, write_si

results = compute_batch(glob.glob("*.log"))
write_si(results, "si.md", units="kcal/mol")    # also .tex, .csv, .tsv, .xyz
rows = si_rows(results)                         # one dict per structure
```

The CLI flag `--si PATH` (with `--si-units`) does the same; see cookbook
recipe 4d.

## Rates and the energy span

```python
from goodvibes import energy_span, eyring_rate, rate_ratio, step_table

eyring_rate(20.0, 298.15)                        # s⁻¹; kcal/mol unless units= says otherwise
rate_ratio(15.0, 16.0)                           # k(15.0) / k(16.0)
levels = {"I0": 0.0, "TS1": 15.0, "I1": -10.0, "TS2": 8.0, "P": -5.0}
es = energy_span(levels, ["TS1", "TS2"])         # the last point closes the cycle
print(es.span, es.tdts, es.tdi, es.tof)
step_table(levels, ["TS1", "TS2"])               # barrier, k and half-life per step
```

A reaction-profile document has the same as `Profile.energy_span()`,
`Profile.step_table()` and `Profile.write_mikimo()`, at the series'
temperature and in the document's units.

## Skipping a re-parse

If you've already parsed an output file (e.g. via
:py:func:`goodvibes.io.parse_qcdata`), pass it in to avoid re-reading:

```python
from goodvibes.io import parse_qcdata
from goodvibes import compute_thermo

qc = parse_qcdata("structure.log")
r = compute_thermo(qcdata=qc)
```

A `QCData` can also be built without any file, from an ASE `Atoms`
and a vibrational analysis (`QCData.from_atoms`,
`QCData.from_vibrations`); see cookbook recipe 4b.

## What's new in v4.x at a glance

- **v4.1 — Selectivity redesign.** N-way `--label NAME=PATTERN` (or
  `--selectivity FILE.yaml`) replaces the 2-only `--ee a:b`. Outputs
  Boltzmann-averaged AND lowest-conformer-only tables. Structured
  `SelectivityResult` exposed on the JSON output.
- **v4.1 — `--json PATH`.** Structured output (schema v1.0) with
  per-file thermochemistry, parsed metadata, options, plus optional
  `selectivity` and `pes` blocks.
- **v4.2 — PES rewrite.** New 3-layer model
  (`ConformerSet`/`Point`/`Pathway`); true-YAML input format alongside
  the legacy line-based format (auto-detected, deprecated); stoichiometric
  sums (`2*A + B`); `--lowest-only` mode for "lowest qh-G conformer per
  species" PES tables.
- **v4.2 — Programmatic API.** This page.
- **v4.6 — Profile model.** `ConformerSet.from_results` with public
  ensemble rollups (`populations`, `ensemble_free_energy`, `s_conf`,
  `dedup`) that re-evaluate each structure at any temperature
  (`ComputedEntry`); point roles and display labels; pathway edges;
  `Series` (a quantity at a temperature, computed or declared);
  `plot_profile` with a merged x axis, temperature / quantity /
  literature overlays and `layout="panels"`; `QCData.from_atoms` /
  `from_vibrations` for file-free ASE and MLIP inputs; every class
  importable from `goodvibes`. See the cookbook, recipes 4 and 4b.
- **5.1 — Selectivity on the profile.** `SelectivityResult` v2 (`major`,
  signed `ee_signed`, `ratio`, `ensemble_energies`); the reaction-profile
  1.1 `selectivity` block with Curtin–Hammett checks
  (`Profile.evaluate_selectivity`, `goodvibes-profile selectivity`);
  `compute_selectivity_batch` / `summarize_selectivity` for sweeps over
  temperatures, entropy cutoffs and conformer windows;
  `plot_boltzmann_histogram`, `plot_temperature_scan`; `Profile.diff` and
  `goodvibes-profile diff`. See cookbook recipe 3b.
- **Reaction-profile documents.** `load_profile` / `Profile` read, validate,
  evaluate, write, tabulate and plot `reaction-profile/1.0` documents;
  `goodvibes --profile` writes one and `goodvibes-profile` works with them
  without output files. See [the reaction-profile format](reaction_profile.md).
- **v4.2 — `--jobs N` parallel parsing.** ~3× speedup at 8 cores.
- **v4.2 — `--csv PATH`.** Per-structure DataFrame export.
- **v4.2 — ORCA CPU-time scaling.** ORCA prints wall time only;
  GoodVibes now multiplies by the parsed MPI process count to give
  an effective CPU time, matching the Gaussian/NWChem/xTB convention.
  Footnoted on the `TOTAL CPU` line.

See the [project ROADMAP](https://github.com/patonlab/GoodVibes/blob/master/ROADMAP.md)
for what is planned next and `CHANGELOG.md` for what has shipped.

## goodvibes --help (installed version)

```
usage: goodvibes [-h] [--temp TEMP] [--ti TI] [-c CONC] [--media solvent]
                 [--freespace SOLVENT] [-q] [--qh] [--qs QS] [-f FREQ_CUTOFF]
                 [--fh H_FREQ_CUTOFF] [--fs S_FREQ_CUTOFF]
                 [--bav {global,conf}] [-v SCALE_FACTOR]
                 [--zpe-vscal ZPE_SCALE_FACTOR] [--vmm MM_SCALE_FACTOR]
                 [--invert [INVERT]] [--imag] [--symm] [--pg] [--sort [KEY]]
                 [--boltz [KEY]] [--dedup] [--e_cutoff KCAL]
                 [--ro_cutoff FRAC] [--rmsd_cutoff ANGS]
                 [--label NAME=PATTERN] [--selectivity FILE.yaml]
                 [--ee patterns] [--pes file] [--graph file] [--nogconf]
                 [--lowest-only] [--custom_ext exts] [--exclude PATTERN]
                 [--spc suffix] [--import PATH] [--cache-read FILE]
                 [--output name] [--dp DP] [--json PATH] [--csv PATH]
                 [--parquet PATH] [--xyz] [--strip-plot PATH]
                 [--pes-plot PATH] [--export PATH] [--cache-save FILE] [--cpu]
                 [--check] [--jobs N]

Compute quasi-harmonic thermochemical corrections from quantum chemistry
output files.

options:
  -h, --help            show this help message and exit

Temperature & state:
  --temp TEMP           Temperature in Kelvin (default: 298.15)
  --ti TI               Temperature interval as START,END,STEP in Kelvin (e.g.
                        '300,1000,100')
  -c CONC, --conc CONC  Concentration in mol/L for solution-phase entropy; gas
                        phase (1 atm) if not set
  --media solvent       Apply standard-state concentration correction for the
                        given solvent (e.g. H2O corrects to 55.34 M)
  --freespace SOLVENT   Apply free-space correction for the given solvent
                        (e.g. H2O, toluene, DMF, AcOH, chloroform)

Quasi-harmonic corrections:
  -q                    Apply both quasi-harmonic entropy (Grimme mRRHO) and
                        enthalpy (Head-Gordon) corrections
  --qh                  Apply Head-Gordon quasi-harmonic enthalpy correction
  --qs QS               Quasi-harmonic entropy method: 'grimme' for mRRHO
                        free-rotor interpolation, 'truhlar' for frequency
                        raising (default: grimme)
  -f FREQ_CUTOFF, --tau FREQ_CUTOFF
                        Frequency cut-off for both entropy and enthalpy in
                        cm-1 (default: 100)
  --fh H_FREQ_CUTOFF    Frequency cut-off for enthalpy only in cm-1; overrides
                        -f for H (default: 100)
  --fs S_FREQ_CUTOFF    Frequency cut-off for entropy only in cm-1; overrides
                        -f for S (default: 100)
  --bav {global,conf}   Moment of inertia for free-rotor entropy: 'global'
                        uses Bav = 10e-44 kg m^2 for all molecules, 'conf'
                        computes from rotational constants per file (default:
                        global)

Frequency handling:
  -v SCALE_FACTOR, --vscal SCALE_FACTOR
                        Vibrational frequency scaling factor for the
                        partition-function frequencies (H_vib, S_vib); auto-
                        detected from level of theory via Truhlar's harm_fac
                        if not set, falls back to 1.0
  --zpe-vscal ZPE_SCALE_FACTOR
                        Separate scaling factor for the zero-point energy
                        (ZPE); auto-detected from level of theory via
                        Truhlar's zpe_fac if not set. If --vscal is set but
                        --zpe-vscal is not, ZPE inherits --vscal (back-
                        compat).
  --vmm MM_SCALE_FACTOR
                        Frequency scaling factor for the MM region in ONIOM
                        calculations
  --invert [INVERT]     Invert small imaginary frequencies (> -50 cm-1) to
                        positive values; optionally provide a custom threshold
                        in cm-1
  --imag                Print imaginary frequencies for each structure

Symmetry:
  --symm                Apply external symmetry correction to entropy using
                        point-group detection (pymsym)
  --pg                  Display point group from output file (no entropy
                        correction applied)

Sorting & deduplication:
  --sort [KEY]          Sort output by energy ('energy' for SCF, 'gibbs' for
                        quasi-harmonic G; default when flag used: gibbs)
  --boltz [KEY]         Print Boltzmann-weighted populations ('energy' for
                        SCF, 'gibbs' for quasi-harmonic G; default when flag
                        used: gibbs)
  --dedup               Remove duplicate structures based on energy,
                        rotational constants, and stoichiometry
  --e_cutoff KCAL       Energy cutoff for duplicate detection in kcal/mol
                        (default: 0.05)
  --ro_cutoff FRAC      Rotational constant cutoff for duplicate detection as
                        a fraction (default: 0.01 = 1%)
  --rmsd_cutoff ANGS    RMSD cutoff for duplicate detection in Angstrom
                        (default: off; 0.125 matches CREST)

Selectivity & PES:
  --label NAME=PATTERN  Repeatable: assign files matching fnmatch PATTERN to
                        species NAME for selectivity analysis. Two or more
                        species supported (N=2: excess + ΔΔG; N>2: populations
                        only). Example: --label R='*P_R_*' --label S='*P_S_*'.
  --selectivity FILE.yaml
                        YAML spec for selectivity analysis. Top-level key
                        'labels' maps species -> fnmatch pattern, or 'files'
                        maps species -> explicit list of files. Use instead of
                        --label for many species or shareable specs.
  --ee patterns         DEPRECATED — use --label/--selectivity. Compute
                        2-species selectivity from a colon-delimited glob pair
                        (e.g. '*_R*:*_S*'). Will be removed in v5.0.
  --pes file            YAML file defining a reaction pathway for tabulating
                        relative energies
  --graph file          Graph a reaction profile from free energies; provide
                        the PES YAML file
  --nogconf             Disable the Gconf correction for multi-conformer
                        ensembles (enabled by default)
  --lowest-only         PES tables: use only each species' lowest qh-G
                        conformer (overrides --nogconf and the default Gconf
                        correction)

Input:
  --custom_ext exts     Additional file extensions to accept, comma-separated
                        (e.g. '.qfi,.gaussian'); also settable via
                        GOODVIBES_CUSTOM_EXT env var
  --exclude PATTERN     Glob pattern to exclude files from the analysis (e.g.
                        '*_TZ.out')
  --spc suffix          Single-point correction suffix: reads energy from
                        FILE_SPC.ext (e.g. --spc TZ reads from FILE_TZ.log)
  --import PATH         Read pre-parsed data from a v1.0 JSON file (or a
                        legacy --cache-save envelope) instead of re-parsing
                        the input QC outputs. Useful for fast re-analysis at a
                        different temperature/concentration without re-reading
                        large outputs.
  --cache-read FILE     (deprecated, use --import instead) Read pre-parsed
                        data from a JSON file.

Output & reports:
  --output name         Base name for the output file, written as
                        GoodVibes_OUTPUT.dat (default: output)
  --dp DP               Number of decimal places for energy values in output
                        (default: 6)
  --json PATH           Write structured results to PATH as JSON (every parsed
                        and computed field per file plus the run options).
                        Schema is preview/v0.1.
  --csv PATH            Write per-file thermochemistry to PATH as CSV (one row
                        per structure; columns mirror ThermoResult). Requires
                        pandas; install with `pip install goodvibes[full]`.
  --parquet PATH        Write per-file thermochemistry to PATH as Parquet
                        (same columns as --csv). Requires pandas + a Parquet
                        engine (pyarrow); install with `pip install
                        goodvibes[full]`.
  --xyz                 Write optimized Cartesian coordinates to a .xyz file
  --strip-plot PATH     Save a per-species ΔG strip plot to PATH (PNG/PDF/SVG
                        by extension). Requires --label or --selectivity to
                        define buckets; matplotlib via `pip install
                        goodvibes[plot]`.
  --pes-plot PATH       Save a clean reaction-profile diagram to PATH
                        (PNG/PDF/SVG by extension). Requires --pes; uses
                        goodvibes.plot.plot_pes (simpler than the legacy
                        --graph FILE.yaml, no styling YAML needed). matplotlib
                        via `pip install goodvibes[plot]`.
  --export PATH         Write the unified v1.0 JSON payload to PATH (per-file
                        QCData + thermo + run options + selectivity / pes
                        blocks). Identical to --json. The same file can be re-
                        loaded via --import to skip parsing on a follow-up
                        run.
  --cache-save FILE     (deprecated, use --export instead) Save parsed data to
                        a JSON file.
  --cpu                 Print total CPU time from output files
  --check               Verify all files use the same program, level of
                        theory, and solvation model; also flag potential
                        duplicates

Performance:
  --jobs N              Parse and compute thermochemistry in parallel across N
                        worker processes (default 1, sequential). 0 = use all
                        available CPU cores.
```
