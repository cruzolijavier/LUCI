"""racerTS inside its environment: one conformer ensemble per molecule or structure.

racerTS takes one molecule per call (a SMILES or one structure file). LUCI hands
it a molecule CSV (smiles, code_name) or a folder of SDF files, so this runner
calls ``racerts <task> ...`` once per entry and writes ``<name>_racerts.xyz`` in
the output folder (LUCI then adds an SDF copy of every ensemble).

Atom indices are racerTS's own: 0-based, in the order of the structure file.
"""

import csv
import glob
import os
import re
import subprocess
import sys

from _luci_job import as_list, fail, load_job, say, sniff_delimiter

TASKS = ("gs", "ts", "constrained")
# LUCI option -> racerTS flag (values are passed as typed).
VALUE_FLAGS = (
    ("n_conformers", "--n-conformers"), ("conf_factor", "--conf-factor"), ("embed", "--embed"),
    ("refine", "--refine"), ("num_threads", "--num-threads"), ("seed", "--seed"),
    ("energy_threshold", "--energy-threshold"), ("rmsd_threshold", "--rmsd-threshold"),
    ("graph", "--graph"), ("config", "--config"),
)
LIST_FLAGS = (("reacting_atoms", "--reacting-atoms"), ("frozen_atoms", "--frozen-atoms"),
              ("hard", "--hard"))
CLI = "import sys; from racerts.cli import main; sys.exit(main())"


def safe_name(text):
    return re.sub(r"[^\w.-]+", "_", str(text)).strip("_") or "molecule"


def molecules_from_csv(path):
    """(name, smiles, charge, mult) for every row of LUCI's molecule CSV."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter=sniff_delimiter(path))
        fields = {name.lower().strip(): name for name in (reader.fieldnames or [])}
        smiles_col = fields.get("smiles")
        name_col = fields.get("code_name")
        if not smiles_col:
            fail("the molecule CSV has no smiles column")
        for number, row in enumerate(reader, 1):
            smiles = (row.get(smiles_col) or "").strip()
            if not smiles:
                continue
            name = (row.get(name_col) or "").strip() if name_col else ""
            rows.append((name or "mol_{}".format(number), smiles,
                         (row.get(fields.get("charge", ""), "") or "").strip(),
                         (row.get(fields.get("mult", ""), "") or "").strip()))
    return rows


def sdf_records(path):
    """The records of an SDF file, as text blocks ending in $$$$."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    blocks = [b.strip("\n") for b in text.split("$$$$") if b.strip()]
    return [b + "\n$$$$\n" for b in blocks]


def sdf_property(record, name):
    match = re.search(r"^>\s*<{}>.*\n(.*)".format(re.escape(name)), record, re.M)
    return match.group(1).strip() if match else ""


def structures_from(pattern, scratch):
    """(name, file, charge, mult) for every SDF; files with several records use the first."""
    paths = sorted(glob.glob(pattern)) if any(c in pattern for c in "*?[") else (
        sorted(glob.glob(os.path.join(pattern, "*.sdf"))) if os.path.isdir(pattern) else [pattern])
    items = []
    for path in paths:
        records = sdf_records(path) if path.lower().endswith(".sdf") else []
        name = os.path.splitext(os.path.basename(path))[0]
        target = path
        if len(records) > 1:
            os.makedirs(scratch, exist_ok=True)
            target = os.path.join(scratch, name + "_first.sdf")
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(records[0])
            say("{}: {} structures in the file, racerTS starts from the first one".format(
                name, len(records)))
        first = records[0] if records else ""
        items.append((name, target, sdf_property(first, "Real charge"), sdf_property(first, "Mult")))
    return items


def options(kwargs, task):
    args = []
    for key, flag in VALUE_FLAGS:
        value = kwargs.get(key)
        if value not in (None, ""):
            args += [flag, str(value)]
    for key, flag in LIST_FLAGS:
        values = [str(v) for v in as_list(kwargs.get(key))]
        if values:
            args.append(flag)
            args += values
    etkdg = str(kwargs.get("etkdg", "")).lower()
    if etkdg in ("on", "true", "yes"):
        args.append("--etkdg")
    elif etkdg in ("off", "false", "no"):
        args.append("--no-etkdg")
    if str(kwargs.get("no_fallback", "")).lower() in ("true", "1", "yes"):
        args.append("--no-fallback")
    if str(kwargs.get("crest_energies", "")).lower() in ("true", "1", "yes"):
        args.append("--crest-energies")
    if kwargs.get("topology_smiles"):
        args += ["--smiles"] + [str(s) for s in as_list(kwargs.get("topology_smiles"), smiles=True)]
    return args


def main():
    kwargs, job = load_job()
    outdir = job["output_dir"]
    task = str(kwargs.get("task") or "gs").strip().lower()
    if task not in TASKS:
        fail("unknown task '{}': use gs, ts or constrained".format(task))
    entries = []  # (name, molecule argument, charge, mult)
    if kwargs.get("molecules"):
        if task != "gs":
            fail("transition-state and constrained ensembles start from a 3D structure: choose "
                 "'Folder of 3D structures' as the input")
        entries = molecules_from_csv(str(kwargs["molecules"]))
    elif kwargs.get("structures"):
        entries = structures_from(str(kwargs["structures"]), os.path.join(outdir, ".luci", "racerts"))
    else:
        fail("no input: give a molecule CSV, one SMILES or a folder of 3D structures")
    if not entries:
        fail("the input holds no molecules")
    if task == "ts" and not (kwargs.get("reacting_atoms") or kwargs.get("frozen_atoms")):
        fail("a TS ensemble needs the reacting atoms (0-based), or the frozen atoms")
    if task == "constrained" and not kwargs.get("hard"):
        fail("a constrained ensemble needs the atoms to keep fixed (--hard, 0-based)")
    shared = options(kwargs, task)
    if kwargs.get("verbose") not in (None, "", False, "False"):
        shared.append("-v")
    done, failed = [], []
    say("racerTS {}: {} molecule(s)".format(task, len(entries)))
    for name, molecule, charge, mult in entries:
        stem = safe_name(name)
        target = os.path.join(outdir, stem + "_racerts.xyz")
        argv = [sys.executable, "-c", CLI, task, molecule, "-o", target] + shared
        user_charge = kwargs.get("charge")
        user_mult = kwargs.get("multiplicity")
        if user_charge not in (None, ""):
            argv += ["--charge", str(user_charge)]
        elif charge:
            argv += ["--charge", charge]
        if user_mult not in (None, ""):
            argv += ["--multiplicity", str(user_mult)]
        elif mult:
            argv += ["--multiplicity", mult]
        say("{} -> {}".format(name, os.path.basename(target)))
        result = subprocess.run(argv, cwd=outdir, stdin=subprocess.DEVNULL)
        if result.returncode == 0 and os.path.isfile(target) and os.path.getsize(target) > 0:
            with open(target, encoding="utf-8", errors="replace") as handle:
                lines = handle.read().splitlines()
            count, index = 0, 0
            while index < len(lines):
                try:
                    atoms = int(lines[index].strip())
                except ValueError:
                    break
                count += 1
                index += atoms + 2
            say("   {} conformer(s)".format(count))
            done.append(name)
        else:
            say("   failed (exit code {})".format(result.returncode))
            failed.append(name)
    say("Finished: {} of {} gave an ensemble.".format(len(done), len(entries)))
    if failed:
        say("Without ensemble: " + ", ".join(failed))
    raise SystemExit(0 if done else 1)


if __name__ == "__main__":
    main()
