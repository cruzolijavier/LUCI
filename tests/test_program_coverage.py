"""Every program LUCI offers has real-run tests and a CircleCI job.

Adding a program to the registry without a test in tests/programs and a group in
tools/ci_programs.py fails here, so nothing reaches users untested by accident.
"""

import importlib.util
from pathlib import Path

from luci.registry import ENV_BY_KEY, PROGRAMS, program_available

ROOT = Path(__file__).resolve().parents[1]


def _groups():
    spec = importlib.util.spec_from_file_location("ci_programs", ROOT / "tools" / "ci_programs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.GROUPS


def test_every_available_program_has_a_real_run_test():
    sources = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "tests" / "programs").glob("test_*.py"))
    missing = [p.key for p in PROGRAMS if program_available(p) and f'"--backend", "{p.key}"' not in sources]
    assert not missing, f"programs without a test in tests/programs: {missing}"


def test_every_available_program_has_a_ci_group():
    groups = _groups()
    covered = {key for _envs, programs, _sel in groups.values() for key in programs}
    missing = [p.key for p in PROGRAMS if program_available(p) and p.key not in covered]
    assert not missing, f"programs missing from tools/ci_programs.py: {missing}"
    for name, (envs, _programs, _sel) in groups.items():
        assert all(env in ENV_BY_KEY for env in envs), name


def test_ci_config_runs_every_group():
    config = (ROOT / ".circleci" / "config.yml").read_text(encoding="utf-8")
    for name in _groups():
        assert f"group: {name}" in config, f"group {name} has no job in .circleci/config.yml"
