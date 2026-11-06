"""LUCI-FEAT: molecular descriptors (electronic, steric, DFT) ready for modeling."""

from __future__ import annotations

from .common import (
    AQME_COLUMNS, CHARGE_MULT, QM_FILTER, constraints, molecules_input, opt, regroup, smiles_input,
    structures_input, switch,
)
from .model import FLAG_ONLY, INPUT_GROUP, InputMode, Launch, ProgramSpec, Tags, Variant

AQME_QDESCP = ProgramSpec(
    key="aqme_qdescp", name="AQME QDESCP", layer="feat",
    description="xTB electronic and steric descriptors, Boltzmann-averaged over conformers.",
    tags=Tags(inputs=("smiles", "structures")),
    variants=(Variant("default", "AQME", env="aqme",
                      launch=Launch("cli", ("python", "{runners}/aqme_cli.py", "--qdescp"),
                                    output_flag="--destination", run_from_input=True,
                                    output_subdir="QDESCP")),),
    docs_url="https://aqme.readthedocs.io/en/latest/API/aqme.qdescp.html",
    input_help="Molecules (a CSV with smiles and code_name, or one SMILES): AQME builds the "
               "conformers first. 3D structures: a folder, for example a CSEARCH or CMIN output.",
    input_modes=(
        molecules_input("--input", columns=AQME_COLUMNS),
        smiles_input(),
        structures_input("--files", help="A folder of 3D structures, for example a CSEARCH or "
                                         "CMIN output folder. Non-SDF files are converted."),
    ),
    options=(
        opt("program", "Descriptor program", "choice", choices=(("xTB", "xtb"),),
            group="Method",
            tooltip="xTB electronic and steric descriptors (GFN2-xTB), Boltzmann-averaged over "
                    "conformers."),
        *regroup(CHARGE_MULT, "Method"),
        opt("qdescp_atoms", "Atomic/SMARTS targets", placeholder="[P,C=O]", group="Method",
            tooltip="Atoms described on their own, on top of the whole-molecule descriptors. Use atoms "
                    "mapped in the SMILES or in the SDF, or a SMARTS pattern such as [P,C=O]."),
        *constraints(),
    ),
    legacy_keys=("aqme_qdescp", "qdescp", "feat"),
)

_PDB = ("@input", "pdb")
DBSTEP = ProgramSpec(
    key="dbstep", name="DBSTEP", layer="feat",
    description="Steric descriptors from 3D structures: Sterimol L/Bmin/Bmax, percent buried "
                "volume, scans and Tolman cone angles.",
    tags=Tags(inputs=("structures",)),
    variants=(Variant("default", "DBSTEP", env="dbstep", launch=Launch("cli", ("dbstep",))),),
    docs_url="https://github.com/patonlab/DBSTEP",
    citation="Luchini, G.; Paton, R. S. DBSTEP: DFT-based steric parameters (patonlab/DBSTEP).",
    input_help="3D structures: a folder of files (SDF, XYZ, MOL, PDB, Gaussian/ORCA files), "
               "handed over as SDF. Proteins and density cubes are read directly. Atom indices are "
               "1-based, in file order.",
    input_modes=(
        structures_input(""),
        InputMode("pdb", "Protein (.pdb)", "", "PDB files (*.pdb *.ent);;All files (*)",
                  help="A protein structure; enables the residue options."),
        InputMode("cube", "Electron density (.cube)", "", "Cube files (*.cube);;All files (*)",
                  help="A density cube: sterics from the electron density surface instead of "
                       "atomic radii."),
    ),
    options=(
        switch("sterimol", "Sterimol (L, Bmin, Bmax)", "Compute Sterimol parameters along the "
               "atom1 -> atom2 axis.", group="Measurements"),
        switch("vbur", "Buried volume (%Vbur)", "Compute the percent buried volume of a sphere "
               "centred on atom1.", group="Measurements"),
        switch("cone", "Tolman cone angle", "Cone angle, metal-centroid distance and ligand "
               "Sterimol values for a metal complex.", group="Measurements"),
        opt("atom1", "Reference atom", "number", placeholder="1", group="Measurements",
            row_label="Atoms 1 / 2 / 3",
            tooltip="atom1: origin of the Sterimol axis, centre of the sphere or the metal. "
                    "atom2: atom(s) defining the axis (several separated by commas). atom3: "
                    "optional atom aligned to +x."),
        opt("atom2", "Axis atom(s)", placeholder="2", group="Measurements", same_row=True),
        opt("atom3", "Orientation atom", "number", placeholder="none", group="Measurements",
            same_row=True),
        opt("r", "Sphere radius (Angstrom)", "number", placeholder="3.5", group="Measurements",
            native_flag="-r", tooltip="Radius of the buried-volume sphere."),
        opt("scan", "Radius scan", placeholder="2.0:4.0:0.5", group="Measurements",
            tooltip="Repeat the measurement over radii written as rmin:rmax:interval."),
        opt("measure", "Sterimol method", "choice", choices=("classic", "grid"), default="classic",
            group="Measurements", tooltip="Classic (Verloop) or grid-based Sterimol."),
        switch("pos", "Positive direction only", "Grid Sterimol only in the direction from atom1 "
               "towards atom2.", group="Measurements", visible_if=("measure", "grid")),
        opt("radii", "van der Waals radii", "choice", choices=("bondi", "charry-tkatchenko", "cpk"),
            default="bondi", group="Atoms and radii", tooltip="Set of van der Waals radii."),
        opt("scalevdw", "Radii scaling", "number", placeholder="1.0", group="Atoms and radii",
            tooltip="Scaling factor applied to the van der Waals radii."),
        switch("sambvca", "SambVca 2.1 settings", "Bondi radii scaled by 1.17, hydrogens excluded.",
               group="Atoms and radii"),
        switch("noH", "Exclude hydrogens", "Leave hydrogen atoms out of the measurement.",
               group="Atoms and radii"),
        switch("nometals", "Exclude metals", "Leave metal atoms out of the measurement.",
               group="Atoms and radii"),
        opt("exclude", "Excluded atoms", placeholder="1,2,3", group="Atoms and radii",
            tooltip="Atom indices to ignore, comma separated with no spaces."),
        opt("cutoff", "Distance cut-off", placeholder="auto or 8.0", group="Atoms and radii",
            tooltip="Ignore atoms farther than this from atom1 (Angstrom); auto keeps exactly those "
                    "that can reach the sphere."),
        opt("grid", "Grid spacing (Angstrom)", "number", placeholder="0.05", group="Grid and surface",
            tooltip="Grid point spacing."),
        opt("surface", "Surface", "choice", choices=("vdw", "density"), default="vdw",
            group="Grid and surface",
            tooltip="Molecular surface from van der Waals radii or from a density cube file."),
        opt("isoval", "Density isovalue", "number", placeholder="0.0016", group="Grid and surface",
            visible_if=("surface", "density"),
            tooltip="Density value that counts as occupied."),
        switch("norot", "Do not rotate", "Structures are already aligned along z.",
               group="Grid and surface"),
        opt("boltzmann", "Boltzmann average", "choice", group="Conformer ensembles",
            choices=(("Off", ""), ("Auto-detect energies", FLAG_ONLY), ("Field: Energy", "Energy"),
                     ("Free energy G (QM outputs)", "G"), ("Electronic energy E (QM outputs)", "E")),
            tooltip="Boltzmann-average over a conformer ensemble, reading energies from the SDF "
                    "data field or the QM outputs."),
        opt("energy_window", "Energy window (kcal/mol)", "number", placeholder="none",
            group="Conformer ensembles", native_flag="energy-window",
            tooltip="Leave out conformers more than this above the lowest."),
        opt("temperature", "Temperature (K)", "number", placeholder="298.15",
            group="Conformer ensembles", tooltip="Temperature for the Boltzmann weights."),
        opt("energy_units", "Energy units", "choice", choices=("kcal", "kj", "hartree", "ev"),
            default="kcal", group="Conformer ensembles", native_flag="energy-units",
            tooltip="Units of the energies stored in SDF or XYZ files."),
        opt("frames", "Frames", placeholder="0:1000:10", group="Conformer ensembles",
            tooltip="Structures of a multi-structure file to run, as start:stop:stride (0-based)."),
        opt("residue", "Residue(s)", placeholder="A:186 or all", group="Proteins", visible_if=_PDB,
            tooltip="Residue to measure as chain:number, several separated by commas, or all."),
        opt("atom", "Residue atom", placeholder="CA", group="Proteins", visible_if=_PDB,
            tooltip="Name of atom1 within the residue."),
        opt("chain", "Chain", placeholder="A", group="Proteins", visible_if=_PDB,
            tooltip="Keep only this chain."),
        switch("nowater", "Remove water", "Leave out water molecules.", group="Proteins",
               visible_if=_PDB),
        switch("nohet", "Remove ligands and ions", "Leave out HETATM records.", group="Proteins",
               visible_if=_PDB),
        switch("exclude_self", "Pocket only", "The selected residue occupies no volume, so only its "
               "pocket is measured.", group="Proteins", native_flag="exclude-self", visible_if=_PDB),
        switch("decompose", "Per-residue decomposition", "Split the buried volume between the "
               "residues that fill the sphere.", group="Proteins", visible_if=_PDB),
        opt("csv", "CSV results", placeholder="dbstep_results.csv", group="Output",
            tooltip="Write every result row to this CSV file (best for chaining into LUCI-PRED)."),
        opt("dp", "Decimal places", "number", placeholder="2", group="Output",
            tooltip="Decimal places in the printed table."),
        switch("pymol", "PyMOL script", "Write a PyMOL script and aligned xyz to visualize the "
               "result.", group="Output"),
    ),
)

AUTOQCHEM = ProgramSpec(
    key="autoqchem", name="Auto-QChem", layer="feat",
    description="DFT descriptors: parse Gaussian outputs locally, or generate conformers and run "
                "Gaussian on an HPC cluster, then export descriptor tables.",
    tags=Tags(inputs=("smiles", "qm_output"), cost=("hpc", "license")),
    variants=(Variant("default", "Auto-QChem", env="autoqchem",
                      launch=Launch("runner", runner="autoqchem_runner"),
                      requires=("Gaussian on an SGE cluster with SSH key access, for submission",)),),
    docs_url="https://github.com/doyle-lab-ucla/auto-qchem",
    citation="Zuranski, A. M. et al. React. Chem. Eng. 2022, DOI 10.1039/D2RE00030J.",
    input_help="Parse: a folder of Gaussian .log files. Submit: one SMILES or a molecule CSV "
               "(smiles, code_name). Export: no input, just the dataset tags.",
    input_modes=(
        InputMode("logs", "Gaussian outputs (parse)", "--logs", "", dialog="directory",
                  pattern="*.log", help="Folder of finished Gaussian .log files to parse locally."),
        InputMode("smiles", "One SMILES (submit)", "--smiles", "", dialog="text",
                  help="One SMILES to send to the cluster.", kind="smiles"),
        InputMode("molecules", "Molecules CSV (submit)", "--smiles_csv",
                  "CSV files (*.csv);;All files (*)", kind="molecules",
                  help="CSV with the columns smiles and code_name; every molecule is sent to the "
                       "cluster."),
        InputMode("none", "Database tags (retrieve / export)", "", "", dialog="none",
                  help="No input file: work from the tags of molecules already submitted."),
    ),
    options=(
        opt("action", "Action", "choice", group=INPUT_GROUP,
            choices=(("Export descriptors", "export"), ("Retrieve finished jobs", "retrieve")),
            default="export", visible_if=("@input", "none"),
            tooltip="Auto-QChem is asynchronous: after submitting, retrieve the finished jobs "
                    "(hours or days later), then export the descriptor tables. Parsing local "
                    "outputs and submitting are chosen by the input type."),
        opt("output_csv", "Descriptor table", placeholder="autoqchem_descriptors.csv",
            group="Output", visible_if=("@input", "logs,none"),
            tooltip="CSV written in the output directory (one sheet per preset when exporting)."),
        opt("num_conf", "Conformers", "number", placeholder="5", group="Molecules",
            visible_if=("@input", "smiles,molecules"),
            tooltip="Maximum number of conformers per molecule."),
        opt("engine", "Conformer engine", "choice", choices=("rdkit", "openbabel"), default="rdkit",
            group="Molecules", visible_if=("@input", "smiles,molecules"),
            tooltip="Conformer generation engine."),
        opt("rdkit_ff", "Force field", "choice", choices=("MMFF94", "MMFF94s", "UFF"),
            default="MMFF94", group="Molecules", visible_if=("engine", "rdkit"),
            tooltip="Force field used when the engine is RDKit."),
        switch("large_mol", "Flexible molecule", "Adjusted conformer settings for flexible "
               "molecules such as long alkyl chains.", group="Molecules",
               visible_if=("@input", "smiles,molecules")),
        opt("user", "Cluster user", placeholder="me", group="Cluster",
            visible_if=("@input", "smiles,molecules,none"), tooltip="SSH user name on the cluster."),
        opt("host", "Cluster host", placeholder="cluster.university.edu", group="Cluster",
            visible_if=("@input", "smiles,molecules,none"), tooltip="SSH host name of the cluster."),
        opt("pem_path", "SSH key", "path", group="Cluster", visible_if=("@input", "smiles,molecules,none"),
            tooltip="Private key used to log in without a password. LUCI cannot answer password "
                    "prompts, so a key is required."),
        opt("workflow_type", "Workflow", "choice", choices=("equilibrium", "transition_state"),
            default="equilibrium", group="Gaussian", visible_if=("@input", "smiles,molecules"),
            tooltip="Equilibrium: optimization, frequencies with NMR/NPA, then TD-DFT. Transition "
                    "state: TS search instead of the optimization, no TD-DFT."),
        opt("theory", "Functional", placeholder="B3LYP", group="Gaussian",
            visible_if=("@input", "smiles,molecules"), tooltip="DFT functional."),
        opt("light_basis_set", "Basis set (light atoms)", placeholder="6-31G*", group="Gaussian",
            visible_if=("@input", "smiles,molecules"), tooltip="Basis set for atoms up to Kr."),
        opt("heavy_basis_set", "Basis set (heavy atoms)", placeholder="LANL2DZ", group="Gaussian",
            visible_if=("@input", "smiles,molecules"), tooltip="Basis set / ECP for heavier atoms."),
        opt("solvent", "Solvent", placeholder="None", group="Gaussian",
            visible_if=("@input", "smiles,molecules"), tooltip="Implicit solvent, by its Gaussian SCRF name."),
        opt("wall_time", "Wall time", placeholder="23:59:00", group="Gaussian",
            visible_if=("@input", "smiles,molecules"), tooltip="Wall time requested per job."),
        opt("tags", "Dataset tags", placeholder="my_set", group="Database",
            visible_if=("@input", "smiles,molecules,none"),
            tooltip="Tags under which the molecules are stored and later exported, comma separated."),
        opt("presets", "Descriptor presets", "multi_choice", group="Database",
            choices=("global", "min_max", "substructure", "core", "transitions"),
            default=("global",), visible_if=("action", "export"),
            tooltip="Which descriptor tables to export."),
        opt("conf_option", "Conformer averaging", "choice", group="Database",
            choices=("boltzmann", "max", "min", "mean", "std", "any"), default="boltzmann",
            visible_if=("action", "export"), tooltip="How conformer-level values are combined."),
        opt("substructure", "Substructure (SMARTS)", group="Database",
            visible_if=("action", "export"),
            tooltip="SMARTS of a shared substructure whose atoms get atom-level descriptors."),
    ),
    notes="Parsing local Gaussian outputs works anywhere. Submission in the public Auto-QChem "
          "release is written for the UCLA Hoffman2 cluster (SGE paths and Gaussian module) and "
          "stores results in the Doyle lab's shared MongoDB at autoqchem.org, so your molecules "
          "are uploaded there; Slurm always asks for a password, which LUCI cannot answer. "
          "Auto-QChem+ (new version) is not public yet.",
)

_M = "descriptors"
MORFEUS = ProgramSpec(
    key="morfeus", name="Morfeus", layer="feat",
    description="Steric and electronic descriptors from 3D structures: Sterimol, buried volume, "
                "cone and solid angles, SASA, dispersion, pyramidalization and xTB properties.",
    tags=Tags(inputs=("structures",)),
    variants=(Variant("default", "Morfeus", env="morfeus",
                      launch=Launch("runner", runner="morfeus_runner")),),
    docs_url="https://digital-chemistry-laboratory.github.io/morfeus/",
    citation="Jorner, K. et al. morfeus: molecular features for machine learning "
             "(digital-chemistry-laboratory/morfeus).",
    input_help="3D structures: a folder of files, handed over as SDF. Every structure of every file "
               "(e.g. all conformers of a CSEARCH output) gets a row in the table. Atom indices are "
               "1-based (the first atom is 1), in file order.",
    input_modes=(
        structures_input("--structures", help="A folder of 3D structures, for example a CSEARCH, "
                                              "CMIN or racerTS output folder. Non-SDF files are "
                                              "converted."),
    ),
    options=(
        opt(_M, "Descriptors", "multi_choice", group="Descriptors", default=("sterimol",),
            choices=(("Sterimol", "sterimol"), ("Buried volume", "buried_volume"),
                     ("Cone angle", "cone_angle"), ("Solid angle", "solid_angle"),
                     ("SASA", "sasa"), ("Dispersion P_int", "dispersion"),
                     ("Pyramidalization", "pyramidalization"), ("Visible volume", "visible_volume"),
                     ("Bite angle", "bite_angle"), ("xTB electronic", "xtb")),
            tooltip="Every ticked descriptor becomes columns of the same table, one row per "
                    "structure. Sterimol: L, B1, B5. Buried volume: %Vbur. SASA: area and volume. "
                    "xTB: energy, HOMO, LUMO, gap, IP, EA, dipole, electrophilicity, nucleophilicity."),
        opt("atom_1", "Atom 1", "number", placeholder="1", group="Atoms", row_label="Atoms 1 / 2 / 3",
            visible_if=(_M, "sterimol,buried_volume,cone_angle,solid_angle,pyramidalization,"
                            "visible_volume,bite_angle,sasa,dispersion,xtb"),
            tooltip="Sterimol: the dummy atom (e.g. the H replaced by the substituent). Buried volume, "
                    "cone, solid and visible volume, bite angle: the metal or centre. "
                    "Pyramidalization: the atom measured. SASA, dispersion, xTB: optional atom whose "
                    "own value is added."),
        opt("atom_2", "Atom 2", "number", placeholder="2", group="Atoms", same_row=True,
            visible_if=(_M, "sterimol,bite_angle"),
            tooltip="Sterimol: the first atom of the substituent. Bite angle: the first ligand atom."),
        opt("atom_3", "Atom 3", "number", placeholder="3", group="Atoms", same_row=True,
            visible_if=(_M, "bite_angle"), tooltip="Bite angle: the second ligand atom."),
        opt("neighbors", "Neighbour atoms", placeholder="optional: 2 3 4", group="Atoms",
            visible_if=(_M, "pyramidalization"),
            tooltip="Pyramidalization: the three neighbours (found from distances when empty)."),
        opt("excluded_atoms", "Excluded atoms", placeholder="optional: 5 6 7", group="Atoms",
            visible_if=(_M, "sterimol,buried_volume,dispersion"),
            tooltip="Atoms left out of the measurement (1-based), e.g. the other ligands."),
        opt("radii_type", "Atomic radii", "choice", group="Settings",
            visible_if=(_M, "sterimol,buried_volume,cone_angle,solid_angle,sasa"),
            choices=(("Descriptor default", ""), ("CRC", "crc"), ("Bondi", "bondi"),
                     ("Alvarez", "alvarez"), ("Truhlar", "truhlar"), ("Pyykko", "pyykko")),
            tooltip="Defaults: CRC for Sterimol, cone and solid angles and SASA; Bondi for the "
                    "buried volume."),
        opt("radius", "Sphere radius (Angstrom)", "number", placeholder="3.5", group="Settings",
            visible_if=(_M, "buried_volume,visible_volume"),
            tooltip="Radius of the buried / visible volume sphere."),
        opt("radii_scale", "Radii scaling", "number", placeholder="1.17", group="Settings",
            visible_if=(_M, "buried_volume"), tooltip="Scaling of the radii for the buried volume."),
        switch("include_hs", "Include hydrogens", "Count hydrogens in the buried volume (left out by "
               "default).", group="Settings", visible_if=(_M, "buried_volume")),
        switch("buried_sterimol", "Buried Sterimol", "Cut the substituent with a sphere (5.5 A, or "
               "the sphere radius) before measuring Sterimol.", group="Settings",
               visible_if=(_M, "sterimol")),
        opt("probe_radius", "Probe radius (Angstrom)", "number", placeholder="1.4", group="Settings",
            visible_if=(_M, "sasa"), tooltip="Solvent probe radius for the SASA."),
        opt("charge", "Charge", "number", placeholder="auto", group="xTB", visible_if=(_M, "xtb"),
            tooltip="Total charge. Empty: the charge LUCI stored in the SDF, or 0."),
        opt("xtb_method", "Method", "choice", group="xTB", visible_if=(_M, "xtb"), default="2",
            choices=(("GFN2-xTB", "2"), ("GFN1-xTB", "1"), ("PTB", "ptb")),
            tooltip="xTB Hamiltonian (the xtb program is installed with Morfeus)."),
        opt("solvent", "Solvent (ALPB)", placeholder="none, e.g. water", group="xTB",
            visible_if=(_M, "xtb"), tooltip="Implicit solvent; empty for the gas phase."),
        opt("output_csv", "Table name", placeholder="morfeus_descriptors.csv", group="Output",
            tooltip="CSV written in the output folder: code_name, structure number and one column "
                    "per value (best for chaining into LUCI-PRED)."),
    ),
    notes="One table for the whole folder (morfeus_descriptors.csv); Morfeus' own command line "
          "prints one value of one file, so LUCI uses its Python API.",
)

PROGRAMS = (AQME_QDESCP, DBSTEP, MORFEUS, AUTOQCHEM)

__all__ = ["PROGRAMS", "QM_FILTER"]
