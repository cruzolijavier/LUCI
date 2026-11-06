# LUCI program request: morfeus

Calculates molecular features and steric/electronic descriptors from 3D molecular structures, including buried volume, cone angle, Sterimol, SASA, dispersion descriptors, conformer tools and xTB-derived properties.

**Docs:** https://digital-chemistry-laboratory.github.io/morfeus/cli.html

## Installation

```
pip install morfeus-ml
```

Some descriptors need optional software or Python packages; for example, the `xtb` interface requires the xTB executable. Most basic steric descriptors work with the core installation.

## Flags

| Flag | What it does | Default | Example / options |
|---|---|---|---|
| `COMMAND` (positional) | Selects the descriptor/calculation | none | `buried_volume / cone_angle / conformer / dispersion / local_force / pyramidalization / sasa / sterimol / visible_volume / xtb` |
| `FILE` (positional) | Geometry file read by the selected subcommand | none | `molecule.xyz` |
| descriptor arguments (positional) | Required command-specific arguments, commonly atom indices | none | Sterimol: `1 2` |
| `--radii_type` | Selects atomic radii where supported | command-dependent | `crc / bondi / alvarez / truhlar` |
| `--excluded_atoms` | Excludes selected atoms where supported | none | `[3,4,5]` |
| `--charge` | Molecular charge for the `xtb` interface | `0` | `-1 / 0 / 1` |
| `--method` | xTB method for the `xtb` interface | `2` | `1 / 2 / ptb` |
| final `COMMAND` or `VALUE` | Selects the method to run or property to print from the instantiated descriptor object | none | `print_report / B_1_value / L_value` |

## Input

The main CLI input is a molecular geometry file supplied after the selected subcommand, for example:

`morfeus sterimol tBu.xyz`

`read_geometry` supports `.xyz`, `.gjf` and `.com` geometry files. Coordinates are Cartesian coordinates in Å.

Most descriptor calculations also require command-specific positional arguments after the first `-`, often atom indices. Morfeus uses **1-based atom indices**: the first atom is atom 1.

Example for Sterimol:

`morfeus sterimol tBu.xyz - 1 2 --radii_type=bondi - print_report`

Some specialized workflows take additional files through chained methods, for example a cube file for a dispersion calculation.

## Output

There is no single standard output file for the Morfeus CLI. Descriptor values and formatted reports are normally written to **stdout**.

For example, Sterimol `print_report` prints the `L`, `B_1` and `B_5` values, while requesting a value such as `B_1_value` prints a single number.

## Notes

Morfeus uses Python Fire, so it does not have one fixed set of flags for every calculation. The general pattern is:

`morfeus <subcommand> <geometry> - <subcommand arguments/options> - <method or value>`

A single `-` tells Python Fire to evaluate the current object, and additional methods can be chained with further `-` separators.

Typical example:

`morfeus sterimol tBu.xyz - 1 2 --radii_type=bondi - print_report`

The cleanest implementation is to expose the Morfeus subcommand first and then show command-specific parameters.
