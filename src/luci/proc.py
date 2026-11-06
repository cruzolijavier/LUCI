"""Run a child process that dies with LUCI.

The GUI stops a run by terminating the ``luci`` process it started. On Linux
and macOS the program LUCI launched (pixi and the scientific code under it) is
put in its own process group, and a SIGTERM/SIGINT received by LUCI is passed
on to that whole group, so Stop really stops the calculation. On Windows the
GUI ends the whole tree with ``taskkill /T`` and Ctrl+C reaches every process
of the console, so the child is started normally.
"""

from __future__ import annotations

import os
import signal
import subprocess

from .settings import current_platform


def run_forwarding_signals(argv: list[str], **kwargs) -> int:
    """subprocess.run(argv), forwarding termination signals to the child's group.

    stdin is closed (DEVNULL): LUCI runs are non-interactive, and a program
    that asks a question (ROBERT's "Enter the column with y values") must fail
    at once instead of waiting forever for an answer nobody can type.
    """
    kwargs.setdefault("stdin", subprocess.DEVNULL)
    if current_platform() == "windows":
        return subprocess.run(argv, **kwargs).returncode
    child = subprocess.Popen(argv, start_new_session=True, **kwargs)

    def forward(signum, _frame):
        try:
            os.killpg(child.pid, signum)
        except OSError:
            pass

    previous = {sig: signal.signal(sig, forward) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        return child.wait()
    except BaseException:
        forward(signal.SIGTERM, None)
        child.wait()
        raise
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
