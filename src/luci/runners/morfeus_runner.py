"""Morfeus inside its environment: descriptors of every structure, in one CSV table.

Morfeus' own command line prints one descriptor of one file to the screen. LUCI
hands over a folder of SDF files, so this runner reads every structure (every
record of every SDF, e.g. all conformers of a CSEARCH output), computes the chosen
descriptors through the Morfeus Python API and writes one row per structure to
``morfeus_descriptors.csv`` (ready for LUCI-PRED).

Atom indices are Morfeus' own: 1-based, in the order of the structure file.
"""

import csv
import glob
import math
import os
import tempfile

from _luci_job import as_list, fail, load_job, say

ALL = ("sterimol", "buried_volume", "cone_angle", "solid_angle", "sasa", "dispersion",
       "pyramidalization", "visible_volume", "bite_angle", "xtb")


# ---------------------------------------------------------------------------
# Reading SDF (V2000 and V3000) without RDKit
# ---------------------------------------------------------------------------
def sdf_records(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    return [block.strip("\n") for block in text.split("$$$$") if block.strip()]


def parse_record(block):
    """(title, elements, coordinates, properties) of one SDF record."""
    lines = block.split("\n")
    title = lines[0].strip()
    counts = lines[3] if len(lines) > 3 else ""
    elements, coordinates = [], []
    if "V3000" in counts:
        inside = False
        for line in lines[4:]:
            if "BEGIN ATOM" in line:
                inside = True
                continue
            if "END ATOM" in line:
                break
            if inside and line.startswith("M  V30"):
                parts = line.split()
                elements.append(parts[3])
                coordinates.append([float(parts[4]), float(parts[5]), float(parts[6])])
    else:
        n_atoms = int(counts[:3])
        for line in lines[4:4 + n_atoms]:
            coordinates.append([float(line[0:10]), float(line[10:20]), float(line[20:30])])
            elements.append(line[31:34].strip())
    properties = {}
    for index, line in enumerate(lines):
        if line.startswith(">") and "<" in line and ">" in line[1:]:
            key = line[line.index("<") + 1:line.rindex(">")]
            properties[key] = lines[index + 1].strip() if index + 1 < len(lines) else ""
    return title, elements, coordinates, properties


def structures(pattern):
    if any(c in pattern for c in "*?["):
        paths = sorted(glob.glob(pattern))
    elif os.path.isdir(pattern):
        paths = sorted(glob.glob(os.path.join(pattern, "*.sdf")))
    else:
        paths = [pattern]
    for path in paths:
        name = os.path.splitext(os.path.basename(path))[0]
        records = sdf_records(path)
        for number, block in enumerate(records, 1):
            try:
                title, elements, coordinates, properties = parse_record(block)
            except (ValueError, IndexError) as exc:
                say("{} (structure {}): cannot be read ({})".format(name, number, exc))
                continue
            yield name, number, len(records), title, elements, coordinates, properties


# ---------------------------------------------------------------------------
# Descriptors
# ---------------------------------------------------------------------------
def index(kwargs, key, label, needed):
    value = kwargs.get(key)
    if value in (None, ""):
        if needed:
            raise ValueError("{} needs '{}' (1-based atom index)".format(needed, label))
        return None
    return int(value)


def indices(kwargs, key):
    return [int(v) for v in as_list(kwargs.get(key))]


def radii_type(kwargs, default):
    return str(kwargs.get("radii_type") or default)


def compute(name, elements, coordinates, kwargs, charge, unpaired):
    import morfeus
    import numpy as np
    coordinates = np.array(coordinates, dtype=float)
    row = {}
    wanted = [d for d in as_list(kwargs.get("descriptors")) if d in ALL] or ["sterimol"]
    excluded = indices(kwargs, "excluded_atoms") or None
    for descriptor in wanted:
        if descriptor == "sterimol":
            dummy = index(kwargs, "atom_1", "Atom 1", "Sterimol")
            attached = index(kwargs, "atom_2", "Atom 2", "Sterimol")
            s = morfeus.Sterimol(elements, coordinates, dummy, attached,
                                 radii_type=radii_type(kwargs, "crc"), excluded_atoms=excluded)
            if str(kwargs.get("buried_sterimol", "")).lower() in ("true", "1"):
                s.bury(sphere_radius=float(kwargs.get("radius") or 5.5), method="delete")
                row["sterimol_buried"] = "yes"
            row.update({"sterimol_L": s.L_value, "sterimol_B1": s.B_1_value, "sterimol_B5": s.B_5_value,
                        "sterimol_L_uncorrected": s.L_value_uncorrected,
                        "sterimol_bond_length": s.bond_length})
        elif descriptor == "buried_volume":
            center = index(kwargs, "atom_1", "Atom 1 (centre)", "Buried volume")
            bv = morfeus.BuriedVolume(
                elements, coordinates, center, excluded_atoms=excluded,
                include_hs=str(kwargs.get("include_hs", "")).lower() in ("true", "1"),
                radius=float(kwargs.get("radius") or 3.5), radii_type=radii_type(kwargs, "bondi"),
                radii_scale=float(kwargs.get("radii_scale") or 1.17))
            row["buried_volume_percent"] = 100 * bv.fraction_buried_volume
            row["buried_volume_A3"] = bv.buried_volume
            row["buried_volume_radius"] = float(kwargs.get("radius") or 3.5)
        elif descriptor == "cone_angle":
            center = index(kwargs, "atom_1", "Atom 1 (metal)", "Cone angle")
            try:
                import libconeangle  # noqa: F401  (fast and exact when installed)
                method = "libconeangle"
            except ImportError:
                method = "internal"
            ca = morfeus.ConeAngle(elements, coordinates, center, radii_type=radii_type(kwargs, "crc"),
                                   method=method)
            row["cone_angle"] = ca.cone_angle
        elif descriptor == "solid_angle":
            center = index(kwargs, "atom_1", "Atom 1 (metal)", "Solid angle")
            sa = morfeus.SolidAngle(elements, coordinates, center, radii_type=radii_type(kwargs, "crc"))
            row.update({"solid_angle": sa.solid_angle, "solid_cone_angle": sa.cone_angle, "solid_G": sa.G})
        elif descriptor == "sasa":
            sasa = morfeus.SASA(elements, coordinates, radii_type=radii_type(kwargs, "crc"),
                                probe_radius=float(kwargs.get("probe_radius") or 1.4))
            row.update({"sasa_area": sasa.area, "sasa_volume": sasa.volume})
            atom = index(kwargs, "atom_1", "Atom 1", "")
            if atom:
                row["sasa_atom_area"] = sasa.atom_areas[atom]
        elif descriptor == "dispersion":
            disp = morfeus.Dispersion(elements, coordinates, excluded_atoms=excluded)
            row.update({"dispersion_area": disp.area, "dispersion_volume": disp.volume,
                        "dispersion_p_int": disp.p_int})
            atom = index(kwargs, "atom_1", "Atom 1", "")
            if atom:
                row["dispersion_atom_p_int"] = disp.atom_p_int[atom]
        elif descriptor == "pyramidalization":
            atom = index(kwargs, "atom_1", "Atom 1", "Pyramidalization")
            neighbours = indices(kwargs, "neighbors") or None
            pyr = morfeus.Pyramidalization(coordinates, atom, neighbor_indices=neighbours, elements=elements)
            row.update({"pyramidalization_P": pyr.P, "pyramidalization_P_angle": pyr.P_angle})
        elif descriptor == "visible_volume":
            center = index(kwargs, "atom_1", "Atom 1 (metal)", "Visible volume")
            vv = morfeus.VisibleVolume(elements, coordinates, center,
                                       radius=float(kwargs.get("radius") or 3.5),
                                       include_hs=str(kwargs.get("include_hs", "True")).lower() not in
                                       ("false", "0"))
            row.update({"visible_volume": vv.visible_volume, "visible_area": vv.visible_area,
                        "proximal_visible_volume": vv.proximal_visible_volume,
                        "distal_visible_volume": vv.distal_visible_volume})
        elif descriptor == "bite_angle":
            metal = index(kwargs, "atom_1", "Atom 1 (metal)", "Bite angle")
            ligand_1 = index(kwargs, "atom_2", "Atom 2 (ligand atom)", "Bite angle")
            ligand_2 = index(kwargs, "atom_3", "Atom 3 (ligand atom)", "Bite angle")
            row["bite_angle"] = morfeus.BiteAngle(coordinates, metal, ligand_1, ligand_2).angle
        elif descriptor == "xtb":
            method = kwargs.get("xtb_method") or 2
            method = int(method) if str(method).isdigit() else str(method)
            with tempfile.TemporaryDirectory() as run_path:
                xtb = morfeus.XTB(elements, coordinates, method=method, charge=charge,
                                  n_unpaired=unpaired, solvent=kwargs.get("solvent") or None,
                                  run_path=run_path)
                row.update({"xtb_energy": xtb.get_energy(), "xtb_homo": xtb.get_homo(),
                            "xtb_lumo": xtb.get_lumo(), "xtb_gap": xtb.get_homo_lumo_gap(),
                            "xtb_ip": xtb.get_ip(), "xtb_ea": xtb.get_ea(),
                            "xtb_dipole": float(np.linalg.norm(xtb.get_dipole())),
                            "xtb_electrophilicity": xtb.get_global_descriptor("electrophilicity"),
                            "xtb_nucleophilicity": xtb.get_global_descriptor("nucleophilicity")})
                atom = index(kwargs, "atom_1", "Atom 1", "")
                if atom:
                    row["xtb_atom_charge"] = xtb.get_charges()[atom]
    return {key: (round(value, 6) if isinstance(value, float) and math.isfinite(value) else value)
            for key, value in row.items()}


def main():
    kwargs, job = load_job()
    source = kwargs.get("structures")
    if not source:
        fail("no input: choose a folder of 3D structures")
    target = os.path.join(job["output_dir"], str(kwargs.get("output_csv") or "morfeus_descriptors.csv"))
    rows, failed, names = [], [], set()
    wanted = [d for d in as_list(kwargs.get("descriptors")) if d in ALL] or ["sterimol"]
    say("Morfeus: " + ", ".join(wanted))
    for name, number, total, title, elements, coordinates, properties in structures(str(source)):
        names.add(name)
        label = name if total == 1 else "{} #{}".format(name, number)
        user_charge = kwargs.get("charge")
        charge = int(user_charge) if user_charge not in (None, "") else int(
            float(properties.get("Real charge") or 0))
        mult = properties.get("Mult") or ""
        unpaired = int(float(mult)) - 1 if mult else None
        try:
            values = compute(name, elements, coordinates, kwargs, charge, unpaired)
        except Exception as exc:  # one bad structure must not stop the table
            say("{}: {}".format(label, exc))
            failed.append(label)
            continue
        row = {"code_name": name, "structure": number, "title": title}
        if "Energy" in properties:
            row["energy"] = properties["Energy"]
        row.update(values)
        rows.append(row)
        say("{}: {}".format(label, ", ".join("{}={}".format(k, v) for k, v in values.items()
                                             if not isinstance(v, str))[:240]))
    if not rows:
        fail("no structure gave descriptors" + (" ({} failed)".format(len(failed)) if failed else ""))
    columns = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with open(target, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    say("Finished: {} structure(s) from {} file(s); table written to {}".format(len(rows), len(names), target))
    if failed:
        say("Without descriptors: " + ", ".join(failed))


if __name__ == "__main__":
    main()
