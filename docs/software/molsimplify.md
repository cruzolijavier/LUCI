# MolSimplify backend

The MolSimplify backend belongs to LUCI-CONF and generates 3D coordination
structures from a metal, oxidation state, coordination number, and ligand
definition.
It is selected with `--molsimplify`; AQME CSEARCH remains the default CONF
backend.

The in-memory API accepts `metal`, `ligands`, `counts`, `oxstate`, `spin`, and
`coord`. The GUI and CLI expose those same core parameters. `destination`
controls the LUCI output directory; `output_xyz` optionally selects the XYZ
file path. Other MolSimplify options are intentionally not exposed because
this backend calls `structgen()` directly in memory.

Each run uses a dedicated working directory:

```text
<destination>/LUCI/LUCI-C-Molsimplify/
```

MolSimplify must be importable as a Python package. The upstream help files in
this repository remain authoritative for available core names and ligands.

Python usage:

```python
from importlib import import_module

generate_complex_in_memory = import_module(
    "luci.modules.01_conf.molsimplify"
).generate_complex_in_memory

complex_mol3d = generate_complex_in_memory(
    metal="fe", ligands=["water", "cl"], counts=[4, 2],
    oxstate="3", spin="6",
)
```
