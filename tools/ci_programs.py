"""Which environments and real-run tests each CircleCI job covers (.circleci/config.yml).

    python tools/ci_programs.py list                 the groups
    python tools/ci_programs.py lockhash GROUP       a file to key the environment cache on
    python tools/ci_programs.py install GROUP        luci env install for each environment
    python tools/ci_programs.py test GROUP [args]    pytest on the group's tests, environments required

Run the same commands on a laptop to reproduce a CircleCI job. Every available
program must appear in one group (tests/test_program_coverage.py checks it).
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "src" / "luci" / "envs" / "manifests"

# group -> (environments, programs covered, pytest selection)
GROUPS: dict[str, tuple[tuple[str, ...], tuple[str, ...], list[str]]] = {
    "aqme": (("aqme", "morfeus"), ("aqme_csearch", "aqme_cmin", "aqme_qdescp"),
             ["tests/programs/test_struct.py", "tests/programs/test_feat.py",
              "tests/programs/test_workflow.py", "-k", "csearch or cmin or qdescp or struct_then_feat"]),
    "racerts": (("racerts",), ("racerts",), ["tests/programs/test_struct.py", "-k", "racerts"]),
    "molsimplify": (("molsimplify",), ("molsimplify",),
                    ["tests/programs/test_struct.py", "-k", "molsimplify"]),
    "goodvibes": (("goodvibes",), ("goodvibes",), ["tests/programs/test_thermo.py", "-k", "goodvibes"]),
    "thermognn": (("thermognn",), ("thermognn",), ["tests/programs/test_thermo.py", "-k", "thermognn"]),
    "steric": (("dbstep", "morfeus"), ("dbstep", "morfeus"),
               ["tests/programs/test_feat.py", "tests/programs/test_workflow.py",
                "-k", "dbstep or morfeus or failed_run"]),
    "autoqchem": (("autoqchem",), ("autoqchem",), ["tests/programs/test_feat.py", "-k", "autoqchem"]),
    "robert": (("robert",), ("robert",), ["tests/programs/test_pred.py"]),
    "edboplus": (("edboplus",), ("edboplus",), ["tests/programs/test_design.py", "-k", "edboplus"]),
    "scopebo": (("scopebo",), ("scopebo",), ["tests/programs/test_design.py", "-k", "scopebo"]),
    # Optional jobs (see the pipeline parameters in .circleci/config.yml): ThermoMLIP needs a
    # Hugging Face token for the UMA weights, TS-tools needs Gaussian 16.
    "thermomlip": (("thermomlip",), ("thermomlip",), ["tests/programs/test_thermo.py", "-k", "thermomlip"]),
    "tstools": (("tstools",), ("ts_tools",), ["tests/programs/test_react.py"]),
}


def _luci(*args: str) -> int:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", ""))
    return subprocess.call([sys.executable, "-m", "luci", *args], env=env, cwd=ROOT)


def main(argv: list[str]) -> int:
    if not argv or argv[0] == "list":
        for name, (envs, programs, _) in GROUPS.items():
            print(f"{name:<12} envs={','.join(envs):<18} programs={','.join(programs)}")
        return 0
    action, group, *rest = argv
    envs, _programs, selection = GROUPS[group]
    if action == "lockhash":
        # The cache key changes whenever one of the group's lock files (or manifests) changes.
        for env in envs:
            for name in ("pixi.toml", "pixi.lock"):
                print(f"{env}/{name}")
                sys.stdout.write((MANIFESTS / env / name).read_text(encoding="utf-8"))
        return 0
    if action == "install":
        sys.path.insert(0, str(ROOT / "src"))
        from luci.envs.manager import EnvManager
        manager = EnvManager()
        for env in envs:
            if manager.is_installed(env) and not manager.is_outdated(env):
                print(f"{env}: installed from the cache, nothing to do")
                continue
            code = _luci("env", "install", env)
            if code:
                return code
        return 0
    if action == "test":
        env = dict(os.environ, LUCI_REQUIRE_PROGRAMS=",".join(envs))
        return subprocess.call([sys.executable, "-m", "pytest", *selection, *rest], env=env, cwd=ROOT)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
