"""LUCI-REACT: transition states, reaction paths and energy profiles."""

from __future__ import annotations

from .common import REACTION_FILTER, opt, switch
from .model import INPUT_GROUP, InputMode, Launch, ProgramSpec, Tags, Variant

_TS_ARGS = (("--xtb-external-path", "{source}/xtb_external_script/xtb_external.py"),)
_TS_COMMAND = ("python", "{source}/run_scripts/run_ts_searcher.py")
_XTB_VARIANTS = "xtb,gxtb"

TS_TOOLS = ProgramSpec(
    key="ts_tools", name="TS-tools", layer="react",
    description="Automated transition-state search from atom-mapped reaction SMILES: TS guess, "
                "optimization and IRC to the connected minima.",
    tags=Tags(inputs=("reaction",), cost=("hpc", "license")),
    variants=(
        Variant("xtb", "GFN2-xTB", env="tstools",
                description="Reference version: GFN2-xTB through Gaussian 16.",
                launch=Launch("cli", _TS_COMMAND, default_args=_TS_ARGS),
                env_vars=(("XTB_PATH", "{env_bin}/xtb"), ("PATH", "{gaussian_dir}")),
                requires=("Gaussian 16 (g16 on PATH or set in Settings)",)),
        Variant("gxtb", "g-xTB", env="tstools_gxtb",
                description="More accurate g-xTB method; needs a g-xTB build.",
                launch=Launch("cli", _TS_COMMAND, default_args=_TS_ARGS),
                env_vars=(("XTB_PATH", "{gxtb_path}"), ("PATH", "{gaussian_dir}")),
                requires=("Gaussian 16", "g-xTB executable (set in Settings)")),
        Variant("mlip", "MLIP (UMA, GPU)", env="tstools_mlip",
                description="Beta: UMA machine-learned potential through ORCA, on GPU.",
                launch=Launch("cli", ("python", "{source}/run_scripts/run_ts_searcher.py")),
                env_vars=(("PATH", "{orca_dir}"), ("HF_TOKEN", "{hf_token}")),
                requires=("ORCA with the UMA wrapper", "Hugging Face access to the UMA weights",
                          "A CUDA GPU")),
    ),
    docs_url="https://github.com/chimie-paristech-CTM/TS-tools",
    citation="TS-tools, Stuyver group (Chimie ParisTech).",
    input_modes=(InputMode("input_file", "Reaction list (.txt)", "--input-file", REACTION_FILTER,
                           help="Text file with one reaction per line: an id, a space and the "
                                "atom-mapped reaction SMILES, e.g. "
                                "R1 [H:2][C:1]([H:3])([H:4])[Cl:5].[Br-:6]>>[H:2][C:1]([H:3])([H:4])[Br:6].[Cl-:5]"),),
    options=(
        opt("solvent", "Solvent", placeholder="water", group="Solvation",
            visible_if=("@variant", _XTB_VARIANTS),
            tooltip="Implicit solvent, by its xTB name. g-xTB only supports GBE solvation."),
        opt("reactive_complex_factors_intra", "Complex factors (intra)", placeholder="0 1.2 1.3 1.8",
            group="Search", multi_value=True, native_flag="reactive-complex-factors-intra",
            visible_if=("@variant", _XTB_VARIANTS),
            tooltip="Scaling factors used to build reactive complexes for intramolecular reactions."),
        opt("reactive_complex_factors_inter", "Complex factors (inter)", placeholder="2.5 1.8 1.5 1.3",
            group="Search", multi_value=True, native_flag="reactive-complex-factors-inter",
            visible_if=("@variant", _XTB_VARIANTS),
            tooltip="Scaling factors used to build reactive complexes for intermolecular reactions."),
        opt("freq_cut_off", "Imaginary frequency cut-off", "number", placeholder="50", group="Search",
            native_flag="freq-cut-off", visible_if=("@variant", _XTB_VARIANTS),
            tooltip="Imaginary-frequency threshold (cm-1) used to filter plausible TS starting points."),
        switch("intermediate_check", "Intermediate check", "Check for intermediates along the path.",
               group="Search", native_flag="intermediate-check", visible_if=("@variant", _XTB_VARIANTS)),
        opt("proc", "Processes", "number", placeholder="2", group="Resources",
            visible_if=("@variant", _XTB_VARIANTS),
            tooltip="Number of processes used for the Gaussian calculations."),
        opt("target_dir", "Work folder name", placeholder="work_dir", group="Resources",
            native_flag="target-dir", visible_if=("@variant", _XTB_VARIANTS),
            tooltip="Folder created inside the output directory. Warning: TS-tools deletes it "
                    "first if it already exists."),
    ),
    legacy_keys=("tstools", "ts-tools"),
)

PROGRAMS = (TS_TOOLS,)

__all__ = ["PROGRAMS", "TS_TOOLS", "INPUT_GROUP"]
