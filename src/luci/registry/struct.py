"""LUCI-STRUCT: 3D structures (conformer ensembles, optimized geometries, complexes)."""

from __future__ import annotations

from .common import (
    AQME_COLUMNS, CHARGE_MULT, constraints, molecules_input, opt, smiles_input, structures_input, switch,
)
from .model import Launch, ProgramSpec, Tags, Variant

AQME_CSEARCH = ProgramSpec(
    key="aqme_csearch", name="AQME CSEARCH", layer="struct",
    description="Conformer generation with RDKit or CREST.",
    tags=Tags(inputs=("smiles", "structures")),
    variants=(Variant("default", "AQME", env="aqme",
                      launch=Launch("cli", ("python", "{runners}/aqme_cli.py", "--csearch"),
                                    output_flag="--destination", run_from_input=True,
                                    output_subdir="CSEARCH",
                                    per_input_output="{name}_*.sdf")),),
    docs_url="https://aqme.readthedocs.io/en/latest/API/aqme.csearch.html",
    input_help="Molecules: a CSV with smiles and code_name (charge, mult and complex_type columns "
               "are used too), or one SMILES. 3D structures: a folder of files to start from.",
    input_modes=(
        molecules_input("--input", columns=AQME_COLUMNS),
        smiles_input("--smi", name_flag="--name"),
        structures_input("--input", help="A folder of existing 3D structures to start from "
                                         "(RacerTS workflow); each is converted to SDF."),
    ),
    options=(
        opt("program", "Method", "choice", choices=(("RDKit", "rdkit"), ("CREST (Linux)", "crest")),
            group="Method",
            tooltip="Conformer engine. RDKit does fast distance-geometry sampling; CREST runs xTB "
                    "metadynamics, which is slower but explores harder cases. CREST is only "
                    "packaged for Linux."),
        *CHARGE_MULT,
        opt("sample", "Number of conformers", "number", placeholder="25", group="Core options",
            tooltip="Conformers kept in the final ensemble, at maximum."),
        *constraints(visible_if=("@input", "molecules,smiles")),
        opt("freeze", "Freeze atoms", placeholder="[1,2]", group="3D structures",
            visible_if=("@input", "structures"),
            tooltip="Atoms kept fixed in the RacerTS workflow: atom-map numbers when the SDF has "
                    "them, else file order (1 = first atom). Not compatible with CREST."),
        opt("crest_keywords", "CREST keywords", placeholder="--nci --alpb h2o", group="CREST extras",
            visible_if=("program", "crest"),
            tooltip="Extra flags passed straight to CREST, for example --nci --alpb h2o."),
        opt("xtb_keywords", "xTB keywords", placeholder="--alpb h2o", group="CREST extras",
            visible_if=("program", "crest"),
            tooltip="Extra flags passed straight to xTB during the CREST run, for example --alpb h2o."),
        opt("cregen_keywords", "CREGEN keywords", group="CREST extras", visible_if=("program", "crest"),
            tooltip="Extra flags passed straight to CREGEN when the duplicate filter runs."),
        opt("crest_runs", "CREST runs", "number", placeholder="1", group="CREST extras",
            visible_if=("program", "crest"),
            tooltip="How many independent CREST searches to launch; more runs cover conformational space better."),
        opt("crest_force", "CREST force", "number", placeholder="0.5", group="CREST extras",
            visible_if=("program", "crest"),
            tooltip="Force constant applied to the constraints during the CREST search."),
    ),
    legacy_keys=("aqme_csearch", "aqme", "csearch", "conf"),
)

AQME_CMIN = ProgramSpec(
    key="aqme_cmin", name="AQME CMIN", layer="struct",
    description="Geometry optimization of conformers with xTB or machine-learned potentials "
                "(FAMEX), minima or transition states, optional frequencies.",
    tags=Tags(inputs=("structures",), cost=("cpu", "gpu")),
    variants=(Variant("default", "AQME", env="aqme",
                      launch=Launch("cli", ("python", "{runners}/aqme_cli.py", "--cmin"),
                                    output_flag="--destination", run_from_input=True,
                                    output_subdir="CMIN", per_input_output="{name}_*.sdf")),),
    docs_url="https://aqme.readthedocs.io/en/latest/API/aqme.cmin.html",
    input_modes=(
        structures_input("--files", help="A folder of conformers to optimize, for example a "
                                         "CSEARCH output folder. Non-SDF files are converted."),
    ),
    options=(
        opt("program", "Backend", "choice", group="Method",
            choices=(("xTB (tblite)", "xtb"), ("UMA (needs famex[uma])", "uma"),
                     ("MACE (needs mace-torch)", "mace"), ("AIMNet2 (needs aimnet)", "aimnet2"),
                     ("ORB (needs famex[orb])", "orb"), ("SO3LR (needs so3lr)", "so3lr")),
            tooltip="FAMEX engine used to optimize each conformer: GFN2-xTB through tblite, or a "
                    "machine-learned potential. The MLIP backends need their FAMEX extra in the "
                    "AQME environment (e.g. famex[uma], famex[orb])."),
        *CHARGE_MULT,
        opt("target", "Target", "choice", choices=(("Minimum", "minima"), ("Transition state", "ts")),
            default="minima", group="Core options",
            tooltip="What to optimize towards: a minimum on the energy surface, or a transition state."),
        opt("freq", "Frequencies", "bool", default=False, flag_only=True, group="Core options",
            tooltip="Compute vibrational frequencies for the conformers that survive the filters."),
        *constraints(atoms=False, complex_type=False),
    ),
    legacy_keys=("aqme_cmin", "cmin", "gopt"),
)

MOLSIMPLIFY = ProgramSpec(
    key="molsimplify", name="MolSimplify", layer="struct",
    description="3D structures of transition-metal complexes from a metal and its ligands.",
    tags=Tags(inputs=()),
    variants=(Variant("default", "MolSimplify", env="molsimplify",
                      launch=Launch("runner", runner="molsimplify_runner",
                                    structure_outputs=("LUCI-MolSimplify/**/*.xyz",))),),
    docs_url="https://molsimplify.readthedocs.io/en/latest/",
    input_modes=(),
    options=(
        opt("metal", "Metal", placeholder="fe", group="Structure generation", required=True,
            tooltip="Chemical symbol of the central metal atom of the complex, for example fe or pd."),
        opt("ligands", "Ligands", placeholder="water, cl", group="Structure generation", required=True,
            tooltip="Ligands placed around the metal: names from MolSimplify's dictionary, SMILES "
                    "or file paths, separated by commas."),
        opt("counts", "Ligand counts", placeholder="4, 2", group="Structure generation",
            tooltip="How many copies of each ligand to attach, in the same order as the ligand list."),
        opt("oxstate", "Oxidation state", "number", placeholder="2", group="Structure generation",
            tooltip="Formal oxidation state of the metal centre, used to assign the total charge."),
        opt("coord", "Coordination number", "number", placeholder="6", group="Structure generation",
            tooltip="Coordination number, that is how many donor atoms bind the metal."),
        opt("geometry", "Geometry", placeholder="oct", group="Structure generation",
            tooltip="Coordination geometry code, for example oct, thd or sqp. Leave empty to let "
                    "MolSimplify choose from the coordination number."),
        opt("spin", "Spin multiplicity", "number", placeholder="1", group="Electronic structure",
            tooltip="Spin multiplicity (2S+1) of the complex: 1 for a closed shell, 2 for one unpaired electron."),
        opt("jobname", "Job name", placeholder="complex", group="Output",
            tooltip="Name of the folder MolSimplify writes inside the output directory."),
    ),
    legacy_keys=("molsimplify", "molsimp"),
)

_TS = ("task", "ts")
_FILE = ("@input", "structures")
RACERTS = ProgramSpec(
    key="racerts", name="racerTS", layer="struct",
    description="Conformer ensembles for ground states, transition states (the reacting region "
                "stays at the TS geometry) and structures with a fixed core.",
    tags=Tags(inputs=("smiles", "structures")),
    variants=(Variant("default", "racerTS", env="racerts",
                      launch=Launch("runner", runner="racerts_runner",
                                    structure_outputs=("*_racerts.xyz",),
                                    per_input_output="{name}_racerts.xyz")),),
    docs_url="https://digital-chemistry-laboratory.github.io/racerts/cli/",
    citation="Schmid, S. P.; Seng, H.; Klay, T.; Jorner, K. racerTS: rapid conformer ensembles "
             "with RDKit for transition states (digital-chemistry-laboratory/racerts).",
    input_help="Ground state: molecules (a CSV with smiles and code_name, or one SMILES) or a folder "
               "of 3D structures. Transition state and fixed core: a folder of 3D structures (the TS "
               "or reference geometry); a file with several structures starts from the first one. "
               "Atom indices are 0-based (the first atom is 0), in file order.",
    input_modes=(
        molecules_input("--molecules"),
        smiles_input(),
        structures_input("--structures", help="A folder of 3D structures (TS guesses, complexes, "
                                              "molecules). Each one gives its own ensemble."),
    ),
    options=(
        opt("task", "Task", "choice", group="Task", default="gs",
            choices=(("Ground state (gs)", "gs"), ("Transition state (ts)", "ts"),
                     ("Fixed core (constrained)", "constrained")),
            tooltip="gs: ordinary conformer search, nothing frozen. ts: the reacting atoms and their "
                    "neighbours stay at the TS geometry. constrained: the atoms you list stay where "
                    "they are in the file (a core, a binding motif, a metal environment)."),
        opt("reacting_atoms", "Reacting atoms", placeholder="2 3 4", group="Task", visible_if=_TS,
            tooltip="0-based indices of the atoms whose bonds form or break. Required for ts unless "
                    "frozen atoms are given."),
        opt("frozen_atoms", "Frozen atoms", placeholder="optional: 0 1 2 3", group="Task",
            visible_if=_TS,
            tooltip="0-based atoms kept fixed instead of the reacting atoms and their neighbours."),
        opt("hard", "Fixed atoms", placeholder="0 1 2 3", group="Task",
            visible_if=("task", "constrained"),
            tooltip="0-based indices of the atoms held at the geometry of the file."),
        opt("topology_smiles", "Topology SMILES", placeholder="optional, e.g. CCCCCC=C", group="Task",
            visible_if=_FILE,
            tooltip="SMILES of the molecule (one per fragment, comma separated) to define bonds and "
                    "bond orders of an XYZ-like structure. Recommended for transition states."),
        opt("graph", "Molecular graph", "choice", group="Task", visible_if=_FILE,
            choices=(("Automatic", ""), ("From the SMILES", "smiles"), ("Perceived bonds", "bonds"),
                     ("Connectivity only", "connect")),
            tooltip="How racerTS builds the bonds of a structure file."),
        opt("charge", "Charge / multiplicity", "number", placeholder="auto", group="Molecule",
            row_label="Charge / multiplicity",
            tooltip="Total charge. Empty: from the SMILES, or from the charge column of the CSV / "
                    "the charge LUCI stored in the SDF."),
        opt("multiplicity", "Multiplicity", "number", placeholder="auto", group="Molecule", same_row=True,
            tooltip="Spin multiplicity 2S+1. Empty: the lowest for the electrons (or the mult column)."),
        opt("n_conformers", "Conformers to embed", "number", placeholder="auto", group="Sampling",
            tooltip="Empty or -1: rotatable bonds x conformer factor + 30."),
        opt("conf_factor", "Conformer factor", "number", placeholder="80", group="Sampling",
            tooltip="Conformers per rotatable bond when the number is automatic."),
        opt("energy_threshold", "Energy window (kcal/mol)", "number", placeholder="20",
            group="Sampling", tooltip="Conformers more than this above the lowest are discarded."),
        opt("rmsd_threshold", "RMSD threshold (Angstrom)", "number", placeholder="0.125",
            group="Sampling", tooltip="Heavy-atom RMSD below which two conformers are duplicates."),
        opt("refine", "Force field", "choice", choices=(("MMFF", "mmff"), ("UFF", "uff")),
            default="mmff", group="Sampling", tooltip="Force-field refinement of every conformer."),
        opt("embed", "Embedding", "choice", group="Advanced settings",
            choices=(("Default (cmap)", ""), ("Coordinate map (cmap)", "cmap"),
                     ("Distance bounds (bounds)", "bounds")),
            tooltip="Distance-geometry embedding mode."),
        opt("etkdg", "ETKDGv3", "choice", group="Advanced settings",
            choices=(("Task default (on for gs)", ""), ("On", "on"), ("Off", "off")),
            tooltip="ETKDGv3 embedding instead of plain distance geometry."),
        opt("num_threads", "Threads", "number", placeholder="1", group="Advanced settings",
            tooltip="Threads used by the steps that support them."),
        opt("seed", "Random seed", "number", placeholder="12", group="Advanced settings",
            tooltip="Seed for reproducible ensembles."),
        switch("no_fallback", "No fallbacks", "Fail instead of falling back (graph: bonds, then "
               "connectivity; MMFF: UFF).", group="Advanced settings"),
        switch("crest_energies", "CREST-style energies", "Write only the energy (Hartree) on each "
               "comment line of the XYZ, as CREST does.", group="Advanced settings"),
        opt("config", "Pipeline settings file", "path", group="Advanced settings",
            file_filter="Settings (*.json *.yaml *.yml);;All files (*)",
            tooltip="A racerTS PipelineConfig as JSON or YAML; the options above override it."),
        switch("verbose", "Detailed log", "Print racerTS' progress in the console.",
               group="Advanced settings"),
    ),
    notes="One ensemble per molecule, named after its code_name (name_racerts.xyz) in the output folder, with an SDF copy.",
)

PROGRAMS = (AQME_CSEARCH, RACERTS, MOLSIMPLIFY, AQME_CMIN)
