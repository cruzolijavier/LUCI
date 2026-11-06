"""MolSimplify inside its environment: write an input file and run `molsimplify -i`."""

import os
import re
import subprocess

from _luci_job import as_list, fail, load_job, say


def main():
    kwargs, job = load_job()
    metal = str(kwargs.get("metal", "")).strip()
    ligands = [str(x) for x in as_list(kwargs.get("ligands"), smiles=True)]
    counts = [str(x) for x in as_list(kwargs.get("counts"))]
    if not metal:
        fail("a metal is required, e.g. fe")
    if not ligands:
        fail("at least one ligand is required")
    if counts and len(counts) != len(ligands):
        fail("ligands and counts must have the same length")
    name = re.sub(r"[^\w.-]+", "_", str(kwargs.get("jobname") or kwargs.get("name") or "complex"))
    rundir = os.path.join(job["output_dir"], "LUCI-MolSimplify")
    os.makedirs(rundir, exist_ok=True)
    # MolSimplify asks (keep/replace/skip) when a job folder exists: never reuse one.
    base, number = name, 2
    while os.path.exists(os.path.join(rundir, name)) or os.path.exists(os.path.join(rundir, name + ".inp")):
        name, number = "{}_{}".format(base, number), number + 1
    lines = ["-core " + metal.lower(), "-lig " + ",".join(ligands)]
    if counts:
        lines.append("-ligocc " + ",".join(counts))
    for key in ("oxstate", "coord", "geometry", "spin"):
        if kwargs.get(key) not in (None, ""):
            lines.append("-{} {}".format(key, kwargs[key]))
    lines += ["-rundir " + rundir, "-name " + name]
    inp = os.path.join(rundir, name + ".inp")
    with open(inp, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    say("MolSimplify input written to " + inp)
    say("\n".join(lines))
    result = subprocess.run(["molsimplify", "-i", inp], cwd=rundir, stdin=subprocess.DEVNULL)
    if result.returncode == 0:
        say("Structures written under " + os.path.join(rundir, name))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
