"""LUCI's single source of truth: layers, programs, variants and environments.

Every other part of LUCI (CLI, GUI, environment manager, saved workflows,
docs) reads from here. To add a program, describe it in the layer file it
belongs to and give it an environment; nothing else needs editing.

Layers are named after what the user gets back, not after the internal steps
a program takes. A program that runs a whole pipeline (ThermoMLIP: SMILES ->
conformers -> MLIP -> G) lives in the layer of its result (THERMO).
"""

from __future__ import annotations

from . import design, feat, pred, react, struct, thermo
from .environments import ENV_BY_KEY, ENVIRONMENTS
from .model import (
    ALL_PLATFORMS, COST_LABELS, FLAG_ONLY, INPUT_GROUP, INPUT_HELP, INPUT_LABELS, MODE_LABELS,
    PLATFORM_LABELS, EnvSpec, InputMode, LayerSpec, Launch, OptionSpec, ProgramSpec, SourceSpec,
    Tags, Variant,
)

LAYERS: tuple[LayerSpec, ...] = (
    LayerSpec("struct", "LUCI-STRUCT", "LUCI-S", "Structures",
              "Generate and optimize 3D structures: conformer ensembles, optimized geometries "
              "and metal complexes.",
              delivers="3D structures", legacy_keys=("conf", "c", "gopt", "go")),
    LayerSpec("thermo", "LUCI-THERMO", "LUCI-T", "Thermochemistry",
              "Energies and thermochemistry: ZPE, enthalpy, entropy, free energies and "
              "formation energies.",
              delivers="Energies"),
    LayerSpec("react", "LUCI-REACT", "LUCI-R", "Reactivity",
              "Transition states, reaction paths and energy profiles from reactions.",
              delivers="Transition states"),
    LayerSpec("feat", "LUCI-FEAT", "LUCI-F", "Descriptors",
              "Molecular descriptors (electronic, steric, DFT) ready for modeling.",
              delivers="Descriptors", legacy_keys=("f",)),
    LayerSpec("pred", "LUCI-PRED", "LUCI-P", "Models",
              "Machine-learning models trained on your data, and their predictions.",
              delivers="Models and predictions", legacy_keys=("p",)),
    LayerSpec("design", "LUCI-DESIGN", "LUCI-D", "Experiment design",
              "Which experiments to run next: Bayesian optimization of conditions and substrate "
              "scope selection, round after round.",
              delivers="Next experiments"),
)

PROGRAMS: tuple[ProgramSpec, ...] = (
    *struct.PROGRAMS, *thermo.PROGRAMS, *react.PROGRAMS,
    *feat.PROGRAMS, *pred.PROGRAMS, *design.PROGRAMS,
)

LAYER_BY_KEY = {layer.key: layer for layer in LAYERS}
PROGRAM_BY_KEY = {program.key: program for program in PROGRAMS}

# LUCI 0.1 used four steps; their default programs keep old commands working.
LEGACY_LAYER_DEFAULT = {"conf": "aqme_csearch", "gopt": "aqme_cmin",
                        "feat": "aqme_qdescp", "pred": "robert"}


def layer(key: str) -> LayerSpec:
    """Return a layer by key, title or LUCI 0.1 alias (conf, gopt, ...)."""
    wanted = key.lower().removeprefix("luci-")
    for spec in LAYERS:
        if wanted in (spec.key, spec.short_name.lower().removeprefix("luci-"), *spec.legacy_keys):
            return spec
    raise KeyError(f"Unknown LUCI layer: {key}")


def program(key: str) -> ProgramSpec:
    """Return a program by key or by a legacy name."""
    wanted = key.lower().replace("-", "_")
    if wanted in PROGRAM_BY_KEY:
        return PROGRAM_BY_KEY[wanted]
    for spec in PROGRAMS:
        if wanted in {k.replace("-", "_") for k in spec.legacy_keys}:
            return spec
    raise KeyError(f"Unknown LUCI program: {key}")


def programs_in(layer_key: str) -> tuple[ProgramSpec, ...]:
    return tuple(p for p in PROGRAMS if p.layer == layer_key)


def environment(key: str) -> EnvSpec:
    return ENV_BY_KEY[key]


def program_platforms(spec: ProgramSpec) -> tuple[str, ...]:
    """Platforms on which at least one variant of the program can be installed."""
    found: list[str] = []
    for variant in spec.variants:
        for platform in ENV_BY_KEY[variant.env].platforms:
            if platform not in found:
                found.append(platform)
    return tuple(p for p in ALL_PLATFORMS if p in found)


def program_available(spec: ProgramSpec) -> bool:
    return any(ENV_BY_KEY[v.env].available for v in spec.variants)


def matches_inputs(spec: ProgramSpec, have: set[str]) -> bool:
    """True when the program can start from one of the inputs the user has.

    Programs that need no input file (MolSimplify builds from names) always match.
    """
    if not have or not spec.tags.inputs:
        return True
    return bool(have.intersection(spec.tags.inputs))


def validate() -> list[str]:
    """Return every inconsistency in the registry (empty when all is well)."""
    problems: list[str] = []
    seen: set[str] = set()
    for spec in PROGRAMS:
        if spec.key in seen:
            problems.append(f"duplicate program key {spec.key}")
        seen.add(spec.key)
        if spec.layer not in LAYER_BY_KEY:
            problems.append(f"{spec.key}: unknown layer {spec.layer}")
        if not spec.variants:
            problems.append(f"{spec.key}: no variants")
        keys = [o.key for o in spec.options]
        if len(keys) != len(set(keys)):
            problems.append(f"{spec.key}: duplicate option keys")
        variant_keys = {v.key for v in spec.variants}
        mode_keys = {m.key for m in spec.input_modes}
        for variant in spec.variants:
            if variant.env not in ENV_BY_KEY:
                problems.append(f"{spec.key}/{variant.key}: unknown environment {variant.env}")
            launch = variant.launch
            if launch.kind == "runner" and not launch.runner:
                problems.append(f"{spec.key}/{variant.key}: runner launch without a runner")
            if launch.kind in ("cli", "app") and not launch.command:
                problems.append(f"{spec.key}/{variant.key}: {launch.kind} launch without a command")
        kinds = [mode.kind for mode in spec.input_modes if mode.kind]
        if len(kinds) != len(set(kinds)):
            problems.append(f"{spec.key}: two inputs of the same standard kind")
        for mode in spec.input_modes:
            if mode.variant and mode.variant not in variant_keys:
                problems.append(f"{spec.key}: input {mode.key} names unknown variant {mode.variant}")
            if mode.kind == "smiles" and not mode.flag and "molecules" not in kinds:
                problems.append(f"{spec.key}: SMILES input without a flag needs a molecules input")
            if mode.name_flag and mode.kind != "smiles":
                problems.append(f"{spec.key}: name_flag only applies to a SMILES input")
            if mode.kind == "molecules":
                fields = {luci for luci, _ in mode.columns}
                if "smiles" not in fields or not fields <= {"smiles", "code_name"}:
                    problems.append(f"{spec.key}: molecule columns must map smiles (and code_name)")
            if mode.kind == "structures" and mode.dialog != "directory":
                problems.append(f"{spec.key}: a structures input is a folder")
        for option in spec.options:
            if option.visible_if is None:
                continue
            source, expected = option.visible_if
            values = {part.strip() for part in expected.split(",")}
            if source == "@input":
                missing = values - mode_keys
            elif source == "@variant":
                missing = values - variant_keys
            elif source in keys:
                continue
            else:
                missing = {source}
            if missing:
                problems.append(f"{spec.key}.{option.key}: visible_if refers to unknown {missing}")
            if option.kind == "multi_choice" and option.flag_only:
                problems.append(f"{spec.key}.{option.key}: multi_choice cannot be flag_only")
    for layer_spec in LAYERS:
        if not programs_in(layer_spec.key):
            problems.append(f"layer {layer_spec.key} has no programs")
    return problems


__all__ = [
    "ALL_PLATFORMS", "COST_LABELS", "ENVIRONMENTS", "ENV_BY_KEY", "EnvSpec", "FLAG_ONLY",
    "INPUT_GROUP", "INPUT_HELP", "INPUT_LABELS", "InputMode", "LAYERS", "LAYER_BY_KEY",
    "LEGACY_LAYER_DEFAULT", "LayerSpec", "Launch", "MODE_LABELS", "OptionSpec", "PLATFORM_LABELS",
    "PROGRAMS", "PROGRAM_BY_KEY", "ProgramSpec", "SourceSpec", "Tags", "Variant", "environment",
    "layer", "matches_inputs", "program", "program_available", "program_platforms", "programs_in",
    "validate",
]
