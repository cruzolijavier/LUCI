"""Compare declared flags with the real programs (only where environments are installed).

Uses the real LUCI home (``LUCI_HOME`` or the default); skipped otherwise.
"""

from pathlib import Path
import re
import subprocess

import pytest

from luci.commands import flag_for
from luci.envs.manager import EnvManager
from luci.registry import program

MANAGER = EnvManager()


def _site_packages(env):
    found = list(MANAGER.prefix(env).glob("lib/python3*/site-packages")) + \
        list(MANAGER.prefix(env).glob("Lib/site-packages"))
    return found[0] if found else None


def _help(env, command):
    argv = MANAGER.run_argv(env, [*command, "--help"])
    return subprocess.run(argv, capture_output=True, text=True, timeout=300).stdout


@pytest.mark.parametrize("key,command", [("dbstep", ["dbstep"]),
                                         ("goodvibes", ["python", "-m", "goodvibes"])])
def test_paton_flags_exist(key, command):
    if not MANAGER.is_installed(key):
        pytest.skip(f"{key} environment not installed")
    text = _help(key, command)
    missing = [flag_for(o.native_flag or o.key) for o in program(key).options
               if not re.search(r"(?<![\w-])" + re.escape(flag_for(o.native_flag or o.key)) + r"(?![\w-])", text)]
    assert missing == []


@pytest.mark.parametrize("key,package", [("aqme_csearch", "aqme"), ("aqme_cmin", "aqme"),
                                         ("aqme_qdescp", "aqme"), ("robert", "robert")])
def test_aqme_robert_options_exist(key, package):
    if not MANAGER.is_installed(package):
        pytest.skip(f"{package} environment not installed")
    parser = Path(_site_packages(package)) / package / "argument_parser.py"
    known = set(re.findall(r'^\s*"(\w+)"\s*:', parser.read_text(), re.M))
    spec = program(key)
    missing = []
    for option in spec.options:
        if option.value_is_flag:
            missing += [v for _, v in option.choices if v and v not in known]
        elif (option.native_flag or option.key) not in known:
            missing.append(option.key)
    missing += [m.flag for m in spec.input_modes if m.flag.lstrip("-") not in known]
    assert missing == []
