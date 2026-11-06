"""One problem found in a user's input, worded for the user."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Level = Literal["error", "warning", "info"]
LEVEL_ORDER = {"error": 0, "warning": 1, "info": 2}


@dataclass
class Issue:
    """``error`` stops the run, ``warning`` deserves a look, ``info`` is just good to know.

    ``hint`` says how to fix it.
    """

    level: Level
    code: str
    message: str
    hint: str = ""

    def text(self) -> str:
        return f"{self.message} {self.hint}".strip()


def worst(issues) -> str:
    """'error', 'warning', 'info' or 'ok' for a list of issues."""
    levels = {issue.level for issue in issues}
    for level in ("error", "warning", "info"):
        if level in levels:
            return level
    return "ok"
