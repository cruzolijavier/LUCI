"""The isolated environments LUCI can create.

Each entry matches a folder ``luci/envs/manifests/<key>/`` holding its own
``pixi.toml``. One manifest per environment (instead of one shared file) keeps
failures local: if EDBO+'s 2021 pins cannot be solved on a machine, DBSTEP
still installs. Every program has its own environment (the three AQME
modules are one program), so one program's pins never break another.
Each manifest ships with its pixi.lock: installs reuse those exact versions
(``pixi install --frozen``) instead of solving on the user's machine.
"""

from __future__ import annotations

from .model import ALL_PLATFORMS, UNIX_ONLY, EnvSpec, SourceSpec

ENVIRONMENTS: tuple[EnvSpec, ...] = (
    EnvSpec(
        key="aqme", title="AQME",
        size_hint="~2 GB", tested=True, needs_git=True,
        note="CREST (conformer search) is only packaged for Linux; RDKit sampling works everywhere.",
    ),
    EnvSpec(
        key="robert", title="ROBERT",
        size_hint="~1.5 GB", tested=True, needs_git=True,
    ),
    EnvSpec(
        key="molsimplify", title="MolSimplify",
        size_hint="~1.5 GB",
    ),
    EnvSpec(
        key="dbstep", title="DBSTEP",
        platforms=ALL_PLATFORMS, size_hint="~300 MB", tested=True,
    ),
    EnvSpec(
        key="racerts", title="racerTS",
        size_hint="~600 MB", needs_git=True,
        note="Installed from GitHub (the gs / ts / constrained command line is not on PyPI yet).",
    ),
    EnvSpec(
        key="morfeus", title="Morfeus",
        size_hint="~500 MB",
    ),
    EnvSpec(
        key="goodvibes", title="GoodVibes",
        platforms=ALL_PLATFORMS, size_hint="~300 MB", tested=True,
    ),
    EnvSpec(
        key="thermognn", title="universal_thermoGNN",
        source=SourceSpec("https://github.com/chimie-paristech-CTM/universal_thermoGNN", "edl"),
        size_hint="~3 GB", postinstall=True,
    ),
    EnvSpec(
        key="thermomlip", title="ThermoMLIP",
        platforms=UNIX_ONLY,
        source=SourceSpec("https://github.com/chimie-paristech-CTM/ThermoMLIP", "main"),
        size_hint="~6 GB", postinstall=True,
        note="Linux only: ThermoMLIP uses fcntl and Linux compilers. On Windows, run LUCI inside WSL.",
    ),
    EnvSpec(
        key="tstools", title="TS-tools (xTB)",
        platforms=UNIX_ONLY,
        source=SourceSpec("https://github.com/chimie-paristech-CTM/TS-tools", "master"),
        size_hint="~2 GB", postinstall=True,
        note="Linux only: Gaussian 16 drives xTB through its external= keyword.",
    ),
    EnvSpec(
        key="tstools_gxtb", title="TS-tools (g-xTB)",
        platforms=UNIX_ONLY,
        source=SourceSpec("https://github.com/maximeferrer/ts-tools-gxtb", "main"),
        available=False,
        note="The ts-tools-gxtb repository is not public yet.",
    ),
    EnvSpec(
        key="tstools_mlip", title="TS-tools (MLIP / UMA)",
        platforms=UNIX_ONLY,
        source=SourceSpec("https://github.com/maximeferrer/ts-tools-MLIP", "main"),
        available=False,
        note="Beta; the ts-tools-MLIP repository is not public yet.",
    ),
    EnvSpec(
        key="autoqchem", title="Auto-QChem",
        size_hint="~1.5 GB",
        note="Upstream lists Windows as untested.",
    ),
    EnvSpec(
        key="edboplus", title="EDBO+",
        source=SourceSpec("https://github.com/doyle-lab-ucla/edboplus", "main"),
        size_hint="~2.5 GB", postinstall=True,
        note="Pinned to torch 1.10 / Python 3.9 by upstream.",
    ),
    EnvSpec(
        key="scopebo", title="ScopeBO",
        source=SourceSpec("https://github.com/doyle-lab-ucla/ScopeBO", "main"),
        size_hint="~3 GB",
        note="Pinned to torch 1.10 / Python 3.9 by upstream.",
    ),
    EnvSpec(
        key="boreact", title="BoReact",
        source=SourceSpec("https://github.com/chimie-paristech-CTM/BoReact", "main"),
        available=False,
        note="The BoReact repository is not public yet.",
    ),
)

ENV_BY_KEY = {env.key: env for env in ENVIRONMENTS}

__all__ = ["ENVIRONMENTS", "ENV_BY_KEY", "ALL_PLATFORMS"]
