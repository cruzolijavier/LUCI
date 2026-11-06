"""LUCI-DESIGN: which experiments to run next (Bayesian optimization, scope selection).

These programs are loops with the lab: each run suggests a batch, the user
measures it, writes the results into the same table and runs again.
"""

from __future__ import annotations

from .common import CSV_FILTER, TABLE_FILTER, opt
from .model import INPUT_GROUP, InputMode, Launch, ProgramSpec, Tags, Variant

EDBOPLUS = ProgramSpec(
    key="edboplus", name="EDBO+", layer="design",
    description="Bayesian optimization of reaction conditions for one or more objectives "
                "(yield, selectivity, cost...): suggests the next batch of experiments.",
    tags=Tags(inputs=("table",), mode="loop"),
    variants=(Variant("default", "EDBO+", env="edboplus",
                      launch=Launch("runner", runner="edboplus_runner")),),
    docs_url="https://github.com/doyle-lab-ucla/edboplus",
    citation="Garrido Torres, J. A. et al. J. Am. Chem. Soc. 2022, DOI 10.1021/jacs.2c08592.",
    input_help="Create scope: no input file, describe the components below. Suggest: the scope "
               "CSV, with measured results typed into the objective columns (PENDING elsewhere).",
    input_modes=(
        InputMode("filename", "Scope CSV (suggest next batch)", "--filename", CSV_FILTER,
                  help="The reaction scope CSV. EDBO+ rewrites it in place with a priority column "
                       "(1 = run next, -1 = already measured)."),
        InputMode("new", "New scope (create)", "", "", dialog="none",
                  help="Build a new scope CSV from the components below."),
    ),
    options=(
        opt("components", "Components", placeholder="{'solvent': ['THF', 'DMSO'], 'temperature': [30, 50]}",
            group=INPUT_GROUP, visible_if=("@input", "new"), required=True,
            tooltip="Python dict: component name -> list of choices. Every combination becomes a row."),
        opt("scope_name", "Scope file name", placeholder="reaction.csv", group=INPUT_GROUP,
            visible_if=("@input", "new"),
            tooltip="Name of the scope CSV created in the output directory."),
        opt("objectives", "Objectives", placeholder="['yield', 'ee']", group="Objectives",
            visible_if=("@input", "filename"), required=True,
            tooltip="Names of the objective columns to optimize."),
        opt("objective_mode", "Maximize / minimize", placeholder="e.g. ['max', 'min']", group="Objectives",
            visible_if=("@input", "filename"), required=True,
            tooltip="max or min for each objective, in the same order."),
        opt("objective_thresholds", "Thresholds", placeholder="[0.0, 10.0]", group="Objectives",
            visible_if=("@input", "filename"),
            tooltip="Worst acceptable value of each objective (hypervolume reference point)."),
        opt("batch", "Batch size", "number", placeholder="5", group="Optimizer",
            visible_if=("@input", "filename"),
            tooltip="Number of experiments suggested this round; it can change between rounds."),
        opt("columns_features", "Feature columns", placeholder="all", group="Optimizer",
            visible_if=("@input", "filename"),
            tooltip="Columns used as model features: all, or a list such as ['temperature', 'solvent']."),
        opt("init_sampling_method", "First batch", "choice", choices=("cvt", "lhs", "random"),
            default="cvt", group="Optimizer", visible_if=("@input", "filename"),
            tooltip="How the first batch is chosen when no results exist yet."),
        opt("acquisition_function", "Acquisition function", "choice",
            choices=("NoisyEHVI", "EHVI"), default="NoisyEHVI", group="Optimizer",
            visible_if=("@input", "filename"),
            tooltip="NoisyEHVI handles noisy measurements and falls back to expected improvement "
                    "with a single objective; EHVI needs at least two objectives."),
        opt("acquisition_function_sampler", "Sampler", "choice",
            choices=("SobolQMCNormalSampler", "IIDNormalSampler"), default="SobolQMCNormalSampler",
            group="Optimizer", visible_if=("@input", "filename"),
            tooltip="Monte Carlo sampler for the acquisition function."),
        opt("seed", "Random seed", "number", placeholder="0", group="Optimizer",
            visible_if=("@input", "filename"), tooltip="Random seed."),
    ),
    notes="Each run is one round. Replace PENDING with the measured values in the scope CSV and "
          "run again for the next batch.",
)

SCOPEBO = ProgramSpec(
    key="scopebo", name="ScopeBO", layer="design",
    description="Substrate-scope selection: suggests which substrates to run next so the scope "
                "balances performance and structural diversity.",
    tags=Tags(inputs=("smiles", "table"), mode="loop"),
    variants=(Variant("default", "ScopeBO", env="scopebo",
                      launch=Launch("runner", runner="scopebo_runner")),),
    docs_url="https://github.com/doyle-lab-ucla/ScopeBO",
    citation="Roediger, S.; Sigman, M. S.; Doyle, A. G. J. Am. Chem. Soc. 2026, 148, 39911, "
             "DOI 10.1021/jacs.6c10981.",
    input_help="1) Featurize: a molecule CSV (smiles, code_name) for one starting material. 2) Build space: no input, "
               "list the descriptor CSVs. 3) Suggest: the reaction-space CSV with results typed in.",
    input_modes=(
        InputMode("molecules", "1. Molecules CSV (featurize)", "--smiles_csv", CSV_FILTER,
                  kind="molecules",
                  help="CSV with the columns smiles and code_name: the candidates for one starting "
                       "material."),
        InputMode("space", "2. Descriptor CSVs (build space)", "", "", dialog="none",
                  help="Combine one descriptor CSV per starting material into a reaction space."),
        InputMode("filename", "3. Reaction space (suggest)", "--filename", CSV_FILTER,
                  help="The reaction-space CSV; ScopeBO rewrites its priority column."),
    ),
    options=(
        opt("common_core", "Common core (SMARTS)", placeholder="e.g. CI", group=INPUT_GROUP,
            visible_if=("@input", "molecules"),
            tooltip="Atoms shared by every substrate that get atom-level descriptors. Empty: "
                    "maximum common substructure."),
        opt("features_name", "Descriptor CSV name", placeholder="reactant_features.csv",
            group=INPUT_GROUP, visible_if=("@input", "molecules"),
            tooltip="Name of the descriptor CSV written in the output directory."),
        opt("reactants", "Descriptor CSVs", placeholder="{'reactant1.csv': 'AlkI', 'reactant2.csv': 'Phos'}",
            group=INPUT_GROUP, visible_if=("@input", "space"), required=True,
            tooltip="Dict of descriptor CSV -> feature prefix, one per starting material."),
        opt("space_name", "Reaction space name", placeholder="reaction_space.csv",
            group=INPUT_GROUP, visible_if=("@input", "space"),
            tooltip="Name of the reaction-space CSV written in the output directory."),
        opt("objectives", "Objectives", placeholder="['yield']", group="Objectives",
            visible_if=("@input", "space,filename"),
            tooltip="Names of the objective columns."),
        opt("objective_mode", "Objective mode", placeholder="{'all_obj': 'max'}", group="Objectives",
            visible_if=("@input", "filename"),
            tooltip="Maximize or minimize, e.g. {'all_obj': 'max'}."),
        opt("batch", "Batch size", "number", placeholder="3", group="Optimizer",
            visible_if=("@input", "filename"),
            tooltip="Substrates suggested this round (3 is the optimized default)."),
        opt("Vendi_pruning_fraction", "Vendi pruning fraction", "number", placeholder="13",
            group="Optimizer", visible_if=("@input", "filename"),
            tooltip="Percentage of similar candidates pruned by the Vendi score each round."),
        opt("acquisition_function_mode", "Acquisition mode", "choice",
            choices=(("Balanced", "balanced"), ("Explorative", "explorative"),
                     ("Greedy", "greedy"), ("Random", "random")),
            default="balanced", group="Optimizer", visible_if=("@input", "filename"),
            tooltip="Balance between exploring diverse substrates and exploiting good ones."),
        opt("seed", "Random seed", "number", placeholder="42", group="Optimizer",
            visible_if=("@input", "filename"), tooltip="Random seed."),
    ),
    notes="The authors recommend choosing the first ~3 scope entries by hand. Each suggest run "
          "is one round; replace PENDING with the measured values and run again.",
)

BOREACT = ProgramSpec(
    key="boreact", name="BoReact", layer="design",
    description="Desktop interface for Bayesian optimization of experiments from a campaign "
                "table, with PCA, importance and convergence plots.",
    tags=Tags(inputs=("table",), mode="loop"),
    variants=(Variant("default", "BoReact", env="boreact",
                      launch=Launch("app", ("python", "{source}/BoReact/ui/main_window.py"))),),
    docs_url="https://github.com/chimie-paristech-CTM/BoReact",
    input_modes=(InputMode("experimental_data", "Campaign (CSV)", "--experimental_data",
                           TABLE_FILTER,
                           help="One row per experiment, one column per parameter or target."),),
    options=(),
    notes="BoReact opens its own window; LUCI only launches it.",
)

PROGRAMS = (EDBOPLUS, SCOPEBO, BOREACT)
