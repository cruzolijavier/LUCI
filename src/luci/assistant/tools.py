"""Tools (function calling) the model can use.

* Reading tools: the screen, LUCI's documentation, the user's files, the
  environments. Always available.
* Action tools: drive the window (open programs, fill inputs and options,
  run). Only with the CONTROL switch on.

Answers go back as compact JSON to spend few tokens.
"""

from __future__ import annotations

import json

from . import config as cfg


class Tool:
    def __init__(self, name, description, properties=None, required=(), function=None, thread="data",
                 control=False, label="Working..."):
        self.name = name
        self.description = description
        self.properties = properties or {}
        self.required = list(required)
        self.function = function
        self.thread = thread          # "data" (background thread) or "ui" (GUI thread)
        self.control = control        # needs the CONTROL switch
        self.label = label            # status text while it runs

    def schema(self):
        return {"type": "function", "name": self.name, "description": self.description,
                "parameters": {"type": "object", "properties": self.properties, "required": self.required,
                               "additionalProperties": False}}


class Wait:
    """Deferred result of a screen action: the session waits until ``ready()`` is true
    (a check finished, a page opened) and then returns ``result()``."""

    def __init__(self, ready, result, seconds=60):
        self.ready, self.result, self.seconds = ready, result, seconds


def serialize(result) -> str:
    text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str,
                                                              separators=(",", ":"))
    if len(text) > cfg.MAX_TOOL_CHARS:
        text = text[:cfg.MAX_TOOL_CHARS] + "...[cut: ask for less]"
    return text


def s(description):
    return {"type": "string", "description": description}


def enum(values, description):
    return {"type": "string", "enum": list(values), "description": description}


def integer(description):
    return {"type": "integer", "description": description}


def boolean(description):
    return {"type": "boolean", "description": description}


def strings(description):
    return {"type": "array", "items": {"type": "string"}, "description": description}
