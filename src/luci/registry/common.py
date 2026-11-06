"""Building blocks shared by several program descriptions."""

from __future__ import annotations

from .model import InputMode, OptionSpec


def opt(key, label, kind="text", **kwargs) -> OptionSpec:
    """Short constructor so program files read like a table."""
    return OptionSpec(key, label, kind, **kwargs)


def switch(key, label, tooltip, *, group="Options", native_flag="", visible_if=None) -> OptionSpec:
    """An on/off flag emitted bare (``--sterimol``) when ticked."""
    return OptionSpec(key, label, "bool", tooltip=tooltip, group=group, default=False,
                      flag_only=True, native_flag=native_flag, visible_if=visible_if)


def regroup(options, group: str) -> tuple[OptionSpec, ...]:
    return tuple(OptionSpec(**{**o.__dict__, "group": group}) for o in options)


CHARGE_MULT = (
    opt("charge", "Charge", "number", placeholder="Auto", group="Core options",
        row_label="Charge / multiplicity",
        tooltip="Total charge of the molecule and its spin multiplicity (2S+1)."),
    opt("mult", "Multiplicity", "number", placeholder="Auto", group="Core options", same_row=True),
)


def constraints(*, group="Constraints", atoms=True, complex_type=True, visible_if=None):
    """The AQME constraint block, which several AQME modules accept verbatim."""
    built: list[OptionSpec] = []
    if atoms:
        built.append(opt("constraints_atoms", "Constraint atoms", placeholder="[1,2]", group=group,
                         visible_if=visible_if,
                         tooltip="Atoms restrained near their starting position during the search, as [1,2]."))
    built += [
        opt("constraints_dist", "Distance constraints", placeholder="[[1,2,1.8]]", group=group,
            visible_if=visible_if,
            tooltip="Interatomic distances restrained towards a target value, as [[atom1,atom2,distance]] in Angstrom."),
        opt("constraints_angle", "Angle constraints", placeholder="[[1,2,3,180]]", group=group,
            visible_if=visible_if,
            tooltip="Bond angles restrained towards a target value, as [[atom1,atom2,atom3,degrees]]."),
        opt("constraints_dihedral", "Dihedral constraints", placeholder="[[1,2,3,4,180]]", group=group,
            visible_if=visible_if,
            tooltip="Dihedrals restrained towards a target value, as [[atom1,atom2,atom3,atom4,degrees]]."),
    ]
    if complex_type:
        built.append(opt("complex_type", "Complex type", "choice", group=group, visible_if=visible_if,
                         choices=(("Not set", ""), "squareplanar", "squarepyramidal", "linear", "trigonalplanar"),
                         tooltip="Coordination geometry used to build a metal complex."))
    return tuple(built)


CSV_FILTER = "CSV files (*.csv);;All files (*)"
# Tables are CSV only: LUCI checks them and Excel workbooks break several programs.
TABLE_FILTER = CSV_FILTER
QM_FILTER = "QM outputs (*.log *.out *.extxyz);;All files (*)"
REACTION_FILTER = "Reaction lists (*.txt);;All files (*)"

# The column layout AQME reads (it also accepts lowercase smiles).
AQME_COLUMNS = (("smiles", "SMILES"), ("code_name", "code_name"))
MOLECULES_HELP = ("CSV with a header and the columns smiles and code_name, one molecule per row. "
                  "Other columns (charge, mult...) are kept. LUCI checks the columns and the names "
                  "before the run; the SMILES are passed on as written.")
SMILES_HELP = "One SMILES, passed on as written. The code_name names the output files."
STRUCTURES_HELP = ("A folder of 3D structures: SDF, XYZ, MOL, MOL2, PDB, Gaussian .gjf/.com and "
                   "Gaussian or ORCA outputs (last geometry). LUCI hands them over as SDF files.")


def molecules_input(flag: str, *, columns=None, keep_extra=True, variant="", help=MOLECULES_HELP,
                    key="molecules") -> InputMode:
    """LUCI's molecule CSV (smiles, code_name), rewritten in the program's layout."""
    from .model import STANDARD_COLUMNS
    return InputMode(key, "Molecules (CSV)", flag, CSV_FILTER, dialog="file", help=help,
                     variant=variant, kind="molecules", columns=columns or STANDARD_COLUMNS,
                     keep_extra=keep_extra)


def smiles_input(flag: str = "", *, name_flag="", variant="", key="smiles") -> InputMode:
    """One typed SMILES. Without ``flag`` LUCI passes it as a one-row molecule CSV."""
    return InputMode(key, "One SMILES", flag, "", dialog="text", help=SMILES_HELP,
                     variant=variant, kind="smiles", name_flag=name_flag)


def structures_input(flag: str, *, key="structures", help=STRUCTURES_HELP) -> InputMode:
    """A folder of 3D structures, handed over as SDF files."""
    return InputMode(key, "Folder of 3D structures", flag, "", dialog="directory", pattern="*.sdf",
                     help=help, kind="structures")
