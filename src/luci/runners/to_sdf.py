"""Convert structures to SDF with Open Babel, inside a program's environment.

    python to_sdf.py job.json

job.json: {"files": [{"source", "text", "fmt", "target", "name", "charge", "mult"}],
           "results": "<path>"}

``text`` (XYZ written by LUCI from a Gaussian/ORCA file) is used instead of
``source`` when given. Each SDF record is titled with ``name`` and, when the
charge and multiplicity are known, carries AQME's ``Real charge`` and ``Mult``
properties. Atom order and coordinates are kept; hydrogens are neither added
nor removed. Standard library + Open Babel only, Python >= 3.8.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

PROPERTIES = ("Real charge", "Mult")


def _pybel():
    try:
        from openbabel import pybel
    except ImportError:
        try:
            import pybel  # Open Babel 2
        except ImportError:
            return None
    try:
        pybel.ob.obErrorLog.SetOutputLevel(0)
    except Exception:
        pass
    return pybel


# Valence of the neutral atom, and the formal charge an atom gets at another valence.
# Only the usual cases: ammonium, oxonium, alkoxide/carboxylate, borate, halide...
CHARGE_BY_VALENCE = {
    "N": {4: 1, 2: -1}, "P": {4: 1}, "O": {3: 1, 1: -1}, "S": {3: 1, 1: -1},
    "B": {4: -1}, "Al": {4: -1}, "F": {0: -1}, "Cl": {0: -1}, "Br": {0: -1}, "I": {0: -1},
    "Li": {0: 1}, "Na": {0: 1}, "K": {0: 1}, "Cs": {0: 1}, "C": {3: None},
}


def place_charges(mol, total):
    """Put the stated total charge on the atoms that carry it, as SDF readers expect.

    Open Babel perceives bonds from coordinates but leaves every formal charge
    at zero, so NH4+ comes out as a 4-valent N and acetate as an O radical,
    which RDKit-based programs (AQME) reject. Returns a warning, or "".
    """
    ob = mol.OBMol
    current = sum(atom.GetFormalCharge() for atom in ob_atoms(ob))
    if total is None or current == total:
        return ""
    needed = total - current
    changes = []
    for atom in ob_atoms(ob):
        if atom.GetFormalCharge() != 0:
            continue
        symbol = ELEMENT_TABLE.GetSymbol(atom.GetAtomicNum())
        rules = CHARGE_BY_VALENCE.get(symbol, {})
        valence = atom.GetExplicitValence() if hasattr(atom, "GetExplicitValence") else atom.GetTotalValence()
        if valence not in rules:
            continue
        charge = rules[valence]
        if charge is None:  # a carbon with three bonds: cation or anion, follow the total
            charge = 1 if needed > 0 else -1
        if (charge > 0) == (needed > 0):
            changes.append((atom, charge))
    placed = 0
    for atom, charge in changes:
        if placed == needed:
            break
        atom.SetFormalCharge(charge)
        atom.SetSpinMultiplicity(0)
        placed += charge
    if current + placed != total:
        for atom, _ in changes:
            atom.SetFormalCharge(0)
        return ("The charge %+d could not be placed on atoms; the SDF states it in 'Real charge' "
                "only, which programs reading formal charges may ignore." % total)
    return ""


def ob_atoms(ob):
    return [ob.GetAtom(index) for index in range(1, ob.NumAtoms() + 1)]


ELEMENT_TABLE = None


def to_records(fmt, path, pybel, charge):
    """(SDF text of every structure in the file, warnings)."""
    warnings = []
    if pybel is not None:
        records = []
        for mol in pybel.readfile(fmt, path):
            warning = place_charges(mol, charge) if fmt != "sdf" else ""
            if warning and warning not in warnings:
                warnings.append(warning)
            records.append(mol.write("sdf"))
        return records, warnings
    run = subprocess.run([shutil.which("obabel") or "obabel", "-i" + fmt, path, "-osdf"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    text = run.stdout
    return [record + "$$$$\n" for record in text.split("$$$$\n") if record.strip()], warnings


def finish(record, name, charge, mult):
    """Title the record and set AQME's charge and spin properties when they are known.

    Properties already in the record are kept unless LUCI knows a value for them.
    """
    lines = record.replace("\r", "").split("\n")
    if lines:
        lines[0] = name
    body = "\n".join(lines)
    end = body.rfind("$$$$")
    body = body[:end] if end >= 0 else body
    replace = [key for key, value in (("Real charge", charge), ("Mult", mult)) if value is not None]
    blocks = body.split("\n>")
    kept = [blocks[0]] + [b for b in blocks[1:]
                          if not any("<%s>" % key in b.split("\n")[0] for key in replace)]
    body = "\n>".join(kept).rstrip("\n")
    # A data item ends with a blank line; the molecule block with M  END alone.
    body += "\n\n" if len(kept) > 1 else "\n"
    for key, value in (("Real charge", charge), ("Mult", mult)):
        if value is not None:
            body += ">  <%s>\n%s\n\n" % (key, value)
    return body + "$$$$\n"


def _element_table(pybel):
    class _Table:
        def GetSymbol(self, number):
            try:
                return pybel.ob.GetSymbol(number)
            except AttributeError:
                return pybel.ob.OBElementTable().GetSymbol(number)
    return _Table()


def main():
    with open(sys.argv[1], encoding="utf-8") as handle:
        job = json.load(handle)
    pybel = _pybel()
    global ELEMENT_TABLE
    if pybel is not None:
        ELEMENT_TABLE = _element_table(pybel)
    results = {}
    if pybel is None and shutil.which("obabel") is None:
        results["_fatal"] = "Open Babel is not installed in this environment."
    else:
        scratch = tempfile.mkdtemp(prefix="luci-sdf-")
        try:
            for entry in job["files"]:
                target = entry["target"]
                try:
                    path = entry.get("source") or ""
                    if entry.get("text"):
                        path = os.path.join(scratch, "structure.xyz")
                        with open(path, "w", encoding="utf-8") as handle:
                            handle.write(entry["text"])
                    records, warnings = to_records(entry["fmt"], path, pybel, entry.get("charge"))
                    records = [r for r in records if "M  END" in r]
                    if not records:
                        results[target] = {"ok": False,
                                           "error": "Open Babel could not read a structure from it."}
                        continue
                    partial = target + ".partial"
                    with open(partial, "w", encoding="utf-8", newline="\n") as handle:
                        for record in records:
                            handle.write(finish(record, entry["name"], entry.get("charge"),
                                                entry.get("mult")))
                    os.replace(partial, target)
                    results[target] = {"ok": True, "structures": len(records), "warnings": warnings}
                except Exception as exc:  # one bad file never stops the others
                    results[target] = {"ok": False, "error": "Open Babel failed: %s" % exc}
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
    with open(job["results"], "w", encoding="utf-8") as handle:
        json.dump(results, handle)


if __name__ == "__main__":
    main()
