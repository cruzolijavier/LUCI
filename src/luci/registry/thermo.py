"""LUCI-THERMO: energies and thermochemistry (ZPE, H, S, G, formation energies)."""

from __future__ import annotations

from .common import CSV_FILTER, QM_FILTER, molecules_input, opt, smiles_input, switch
from .model import FLAG_ONLY, INPUT_GROUP, InputMode, Launch, ProgramSpec, Tags, Variant

GOODVIBES = ProgramSpec(
    key="goodvibes", name="GoodVibes", layer="thermo",
    description="Thermochemistry from frequency calculations, with quasi-harmonic corrections, "
                "Boltzmann populations, selectivities and reaction-profile tables.",
    tags=Tags(inputs=("qm_output",)),
    variants=(Variant("default", "GoodVibes", env="goodvibes",
                      launch=Launch("cli", ("python", "-m", "goodvibes"))),),
    docs_url="https://goodvibespy.readthedocs.io/en/latest/",
    citation="Luchini, G.; Alegre-Requena, J. V.; Funes-Ardoiz, I.; Paton, R. S. F1000Research 2020, 9, 291.",
    input_help="GoodVibes reads Gaussian, ORCA, NWChem, Q-Chem and xTB outputs that contain "
               "frequencies. Pick one file or a folder of them.",
    input_modes=(
        InputMode("file", "One output file", "", QM_FILTER, dialog="file",
                  help="One QM output file with a frequency calculation."),
        InputMode("folder_log", "Folder of .log files", "", "", dialog="directory", pattern="*.log",
                  help="Every .log file in the folder (Gaussian, xTB)."),
        InputMode("folder_out", "Folder of .out files", "", "", dialog="directory", pattern="*.out",
                  help="Every .out file in the folder (ORCA, Q-Chem, NWChem)."),
    ),
    options=(
        switch("q", "Quasi-harmonic (both)", "Apply both quasi-harmonic corrections: Grimme "
               "entropy and Head-Gordon enthalpy.", group="Corrections", native_flag="-q"),
        opt("qs", "Entropy method", "choice", choices=("grimme", "truhlar"), default="grimme",
            group="Corrections", tooltip="Quasi-harmonic entropy method."),
        switch("qh", "Head-Gordon enthalpy only", "Apply only the Head-Gordon quasi-harmonic "
               "enthalpy correction.", group="Corrections"),
        opt("f", "Frequency cut-off", "number", placeholder="100", group="Corrections",
            native_flag="-f", tooltip="Cut-off (cm-1) for both entropy and enthalpy corrections."),
        opt("fs", "Entropy cut-off", "number", placeholder="same as above", group="Corrections",
            row_label="Entropy / enthalpy cut-off",
            tooltip="Separate cut-offs (cm-1) for entropy and enthalpy; they override the one above."),
        opt("fh", "Enthalpy cut-off", "number", placeholder="same as above", group="Corrections",
            same_row=True),
        opt("v", "Frequency scaling factor", "number", placeholder="automatic", group="Corrections",
            native_flag="-v",
            tooltip="Vibrational scaling factor. By default it is chosen from the level of theory."),
        switch("symm", "Symmetry correction", "Detect the point group and apply the symmetry "
               "number correction to the entropy.", group="Corrections"),
        opt("invert", "Invert small imaginary frequencies", "choice", group="Corrections",
            choices=(("Off", ""), ("Yes, below -50 cm-1", FLAG_ONLY), ("Below -30 cm-1", "-30"),
                     ("Below -100 cm-1", "-100")),
            tooltip="Turn small imaginary frequencies into real ones before computing the "
                    "thermochemistry."),
        opt("temp", "Temperature (K)", "number", placeholder="298.15", group="Conditions",
            tooltip="Temperature used for the thermochemistry."),
        opt("ti", "Temperature scan", placeholder="300,1000,100", group="Conditions",
            tooltip="Repeat the analysis over a temperature range, written as START,END,STEP."),
        opt("c", "Concentration (mol/L)", "number", placeholder="gas phase (1 atm)",
            group="Conditions", native_flag="-c",
            tooltip="Standard-state concentration for solution-phase free energies, e.g. 1.0."),
        opt("freespace", "Free-space solvent", "choice", group="Conditions",
            choices=(("None", ""), "H2O", "toluene", "DMF", "AcOH", "chloroform"),
            tooltip="Free-volume correction to the translational entropy in this solvent."),
        opt("spc", "Single-point suffix", placeholder="TZ or link", group="Conditions",
            tooltip="Pair each output with a single-point file named <name>_<suffix>.log, or use "
                    "'link' to read the single point from a link job in the same file."),
        opt("boltz", "Boltzmann populations", "choice", group="Analysis",
            choices=(("Off", ""), ("By free energy", FLAG_ONLY), ("By SCF energy", "energy")),
            tooltip="Print the Boltzmann population of every structure."),
        opt("sort", "Sort table", "choice", group="Analysis",
            choices=(("Off", ""), ("By free energy", FLAG_ONLY), ("By SCF energy", "energy")),
            tooltip="Sort the results table by quasi-harmonic G or by SCF energy."),
        switch("dedup", "Remove duplicates", "Remove duplicate structures (same energy, "
               "rotational constants and formula).", group="Analysis"),
        opt("selectivity", "Selectivity file (YAML)", "path", group="Analysis",
            file_filter="YAML (*.yaml *.yml);;All files (*)",
            tooltip="YAML file defining which outputs belong to each product, for selectivity "
                    "analysis. Simple cases can use --label NAME=PATTERN in Advanced flags."),
        opt("pes", "Reaction pathway (YAML)", "path", group="Reaction profile",
            file_filter="YAML (*.yaml *.yml);;All files (*)",
            tooltip="YAML file describing a reaction pathway; GoodVibes prints relative energies "
                    "along it."),
        opt("pes_plot", "Profile figure", placeholder="profile.png", group="Reaction profile",
            native_flag="pes-plot",
            tooltip="Save the reaction-profile diagram to this image file (needs a pathway)."),
        switch("nogconf", "No conformer correction", "Switch off the conformational free energy "
               "(Gconf) correction in pathway tables.", group="Reaction profile"),
        switch("lowest_only", "Lowest conformer only", "Use only the lowest conformer of each "
               "species in pathway tables.", group="Reaction profile", native_flag="lowest-only"),
        switch("check", "Consistency check", "Check that all files share program, level of "
               "theory and solvation model.", group="Output"),
        switch("imag", "List imaginary frequencies", "Print the imaginary frequencies of each "
               "structure.", group="Output"),
        opt("json", "JSON results", placeholder="results.json", group="Output",
            tooltip="Write every parsed value and result to this JSON file (best for chaining "
                    "into other LUCI layers)."),
        opt("csv", "CSV results", placeholder="results.csv", group="Output",
            tooltip="Write one row per structure to this CSV file."),
        opt("output", "Output name", placeholder="output", group="Output",
            tooltip="Base name of the text report, written as GoodVibes_<name>.dat."),
        opt("jobs", "Parallel workers", "number", placeholder="1", group="Output",
            tooltip="Number of parallel worker processes; 0 uses all cores."),
    ),
)

THERMOMLIP = ProgramSpec(
    key="thermomlip", name="ThermoMLIP", layer="thermo",
    description="From SMILES to ZPE, H, S and G: conformer search, MLIP (UMA) optimization and "
                "frequencies in one run.",
    tags=Tags(inputs=("smiles",), cost=("cpu", "gpu")),
    variants=(
        Variant("batch", "Batch (CSV)", env="thermomlip",
                launch=Launch("cli", ("python", "{source}/script/run_hpc.py")),
                env_vars=(("HF_TOKEN", "{hf_token}"),),
                requires=("Hugging Face access to the UMA model weights",)),
        Variant("single", "Single molecule", env="thermomlip",
                launch=Launch("cli", ("python", "{source}/script/run_single_molecule.py"),
                              default_args=(("--task-id", "0"),)),
                env_vars=(("HF_TOKEN", "{hf_token}"),),
                requires=("Hugging Face access to the UMA model weights",)),
    ),
    docs_url="https://github.com/chimie-paristech-CTM/ThermoMLIP",
    input_help="A molecule CSV runs the batch script; one SMILES runs the single-molecule script.",
    input_modes=(
        molecules_input("--csv", columns=(("code_name", "id"), ("smiles", "smiles")),
                        keep_extra=False, variant="batch"),
        smiles_input("--smiles", name_flag="--mol-id", variant="single"),
    ),
    options=(
        opt("dataset_name", "Dataset name", placeholder="demo", group=INPUT_GROUP, required=True,
            native_flag="dataset-name",
            tooltip="Label used in the result and log paths."),
        opt("results_file", "Results CSV", placeholder="results.csv", group=INPUT_GROUP,
            required=True, native_flag="results-file", visible_if=("@variant", "single"),
            tooltip="CSV the result row is appended to. ThermoMLIP writes no header in this "
                    "mode, so prepare one or use batch mode."),
        opt("max_parallel", "Parallel molecules", "number", placeholder="5", group="Batch",
            native_flag="max-parallel", visible_if=("@variant", "batch"),
            tooltip="Maximum number of molecules computed at the same time."),
        opt("timeout", "Timeout per molecule (s)", "number", placeholder="3600", group="Batch",
            visible_if=("@variant", "batch"),
            tooltip="A molecule still running after this many seconds is stopped."),
        opt("num_conformers", "Conformers", "number", placeholder="300", group="Calculation",
            native_flag="num-conformers", visible_if=("@variant", "single"),
            tooltip="Number of conformers generated before the MLIP optimization."),
        opt("mlip_model", "MLIP model", "choice", choices=("uma-s-1p1", "uma-m-1p1"),
            default="uma-s-1p1", group="Calculation", native_flag="mlip-model",
            visible_if=("@variant", "single"),
            tooltip="FairChem UMA model used for optimization and frequencies."),
        opt("n_cores", "CPU cores", "number", placeholder="10", group="Calculation",
            native_flag="n-cores", visible_if=("@variant", "single"),
            tooltip="CPU cores used for conformer generation."),
        opt("fmax_conf", "Force threshold", "number", placeholder="0.05", group="Calculation",
            native_flag="fmax-conf", visible_if=("@variant", "single"),
            tooltip="Force convergence threshold for the conformer optimization (eV/Angstrom)."),
        opt("max_steps", "Max optimization steps", "number", placeholder="4000", group="Calculation",
            native_flag="max-steps", visible_if=("@variant", "single"),
            tooltip="Maximum number of optimization steps per conformer."),
        opt("batch_size", "Conformer batch", "number", placeholder="64", group="Calculation",
            native_flag="batch-size", visible_if=("@variant", "single"),
            tooltip="Conformers optimized together on the device."),
        opt("temperature", "Temperature (K)", "number", placeholder="298.15", group="Thermochemistry",
            visible_if=("@variant", "single"),
            tooltip="Temperature for the thermochemistry."),
        opt("pressure", "Pressure (Pa)", "number", placeholder="101325", group="Thermochemistry",
            visible_if=("@variant", "single"),
            tooltip="Pressure for the thermochemistry."),
        opt("delta", "Finite displacement (Angstrom)", "number", placeholder="0.01",
            group="Thermochemistry", visible_if=("@variant", "single"),
            tooltip="Displacement used for the numerical vibrational frequencies."),
    ),
    notes="Batch mode runs every molecule with ThermoMLIP's default settings; the calculation "
          "options apply to single-molecule mode only.",
)

THERMOGNN = ProgramSpec(
    key="thermognn", name="universal_thermoGNN", layer="thermo",
    description="Gibbs formation energy predicted from SMILES by an evidential graph neural "
                "network, with uncertainty.",
    tags=Tags(inputs=("smiles",), cost=("cpu", "gpu")),
    variants=(Variant("default", "thermoGNN", env="thermognn",
                      launch=Launch("cli", ("python", "{source}/predict.py"),
                                    default_args=(("--checkpoint", "{source}/ckpt/iter6"),
                                                  ("--results_dir", "{output}"),
                                                  ("--output", "{output}/thermognn_predictions.csv")))),),
    docs_url="https://github.com/chimie-paristech-CTM/universal_thermoGNN",
    input_modes=(
        molecules_input("--input", help="CSV with the columns smiles and code_name, one molecule "
                                        "per row. An optional formation_gibbs column turns on the "
                                        "evaluation metrics."),
        smiles_input(),
    ),
    options=(
        opt("target_col", "Reference column", "columns", group=INPUT_GROUP,
            visible_if=("@input", "molecules"),
            tooltip="Optional column with reference values; when present LUCI also gets RMSE, "
                    "MAE and R2 (default: formation_gibbs)."),
        opt("checkpoint", "Model checkpoint", "path", group="Model", directory=True,
            tooltip="Folder holding the model checkpoint (.ckpt). Leave empty to use the model "
                    "shipped with the repository (ckpt/iter6)."),
        opt("batch_size", "Batch size", "number", placeholder="256", group="Model",
            tooltip="Molecules per batch."),
        opt("seed", "Random seed", "number", placeholder="42", group="Model",
            tooltip="Random seed."),
        opt("output", "Predictions CSV", "path", group="Model", save=True,
            file_filter=CSV_FILTER,
            tooltip="Where to write the predictions. Leave empty to write "
                    "thermognn_predictions.csv in the output directory."),
    ),
)

PROGRAMS = (GOODVIBES, THERMOMLIP, THERMOGNN)
