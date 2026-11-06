"""Helpers shared by the runners (standard library only, Python >= 3.8)."""

import json
import os
import sys


def load_job():
    """Return (kwargs, job) from the JSON file named on the command line."""
    if len(sys.argv) != 2:
        sys.exit("usage: python <runner>.py <job.json>")
    with open(sys.argv[1], encoding="utf-8") as handle:
        job = json.load(handle)
    os.makedirs(job["output_dir"], exist_ok=True)
    return dict(job.get("kwargs", {})), job


def as_list(value, smiles=False):
    """Accept a list, "[a, 'b']", "a, b" or "a b" and return a list.

    With ``smiles=True`` brackets belong to the items ("[Cl-], water"), so only
    real Python lists are unpacked and plain text is split on commas.
    """
    import ast
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    text = str(value).strip()
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)):
            return list(parsed)
    except (ValueError, SyntaxError):
        pass
    if smiles:
        return [p.strip().strip("'\"") for p in text.split(",") if p.strip()]
    inner = text[1:-1] if text.startswith("[") and text.endswith("]") else text
    if "[" in inner or "]" in inner:
        # Brackets inside the items (SMILES): only commas separate them.
        return [p.strip().strip("'\"") for p in text.split(",") if p.strip()]
    parts = [p.strip().strip("'\"") for p in inner.replace(",", " ").split()]
    return [p for p in parts if p]


def sniff_delimiter(path):
    """',' or ';' (Excel in Spanish/European locales) or tab, from the first line."""
    import csv
    with open(path, newline="", encoding="utf-8-sig") as handle:
        first = handle.readline()
    try:
        return csv.Sniffer().sniff(first, delimiters=",;\t").delimiter
    except csv.Error:
        return ","


def resolve(path, base):
    """Absolute path; relative ones are taken from ``base``."""
    path = os.path.expanduser(str(path))
    return path if os.path.isabs(path) else os.path.join(base, path)


def pick(kwargs, *names):
    """The subset of kwargs with these names that the user actually set."""
    return {name: kwargs[name] for name in names if name in kwargs and kwargs[name] != ""}


def say(message):
    print("[LUCI runner] " + str(message), flush=True)


def fail(message):
    print("[LUCI runner] Error: " + str(message), file=sys.stderr, flush=True)
    sys.exit(1)
