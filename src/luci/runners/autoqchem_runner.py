"""Auto-QChem inside its environment: parse, submit, retrieve or export descriptors."""

import csv
import glob
import os

from _luci_job import as_list, fail, load_job, pick, resolve, say


def _write_rows(rows, path):
    columns = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _scalars(data):
    """Flatten the global (scalar) descriptors of one parsed output."""
    if isinstance(data, dict) and isinstance(data.get("descriptors"), dict):
        data = data["descriptors"]
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, (int, float, str, bool))}


def parse(kwargs, outdir):
    from autoqchem.gaussian_log_extractor import gaussian_log_extractor
    pattern = resolve(kwargs.get("logs", ""), outdir)
    if os.path.isdir(pattern):
        files = sorted(glob.glob(os.path.join(pattern, "*.log")) + glob.glob(os.path.join(pattern, "*.out")))
    else:
        files = sorted(glob.glob(pattern))
        if pattern.endswith("*.log"):
            files += sorted(glob.glob(pattern[:-4] + ".out"))
    if not files:
        fail("no Gaussian outputs match " + pattern)
    rows = []
    for path in files:
        try:
            row = {"file": os.path.basename(path)}
            row.update(_scalars(gaussian_log_extractor(path).get_descriptors()))
            rows.append(row)
            say("parsed " + os.path.basename(path))
        except Exception as exc:  # one bad file should not stop the table
            say("skipped {}: {}".format(os.path.basename(path), exc))
    if not rows:
        fail("none of the {} file(s) could be parsed; see the messages above".format(len(files)))
    target = os.path.join(outdir, str(kwargs.get("output_csv") or "autoqchem_descriptors.csv"))
    _write_rows(rows, target)
    say("Descriptor table written to " + target)


def _smiles(kwargs, outdir):
    if kwargs.get("smiles"):
        return [str(kwargs["smiles"])]
    path = resolve(kwargs.get("smiles_csv", ""), outdir)
    column = kwargs.get("smiles_column") or "smiles"
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if column not in (reader.fieldnames or []):
            matches = [c for c in reader.fieldnames or [] if c.lower() == "smiles"]
            if not matches:
                fail("column '{}' not found in {}".format(column, path))
            column = matches[0]
        return [row[column] for row in reader if row.get(column)]


def _manager(kwargs):
    from autoqchem.sge_manager import sge_manager
    if not kwargs.get("user") or not kwargs.get("host"):
        fail("cluster user and host are required")
    if not kwargs.get("pem_path"):
        fail("an SSH key is required: LUCI cannot answer password prompts")
    return sge_manager(user=kwargs["user"], host=kwargs["host"], pem_path=kwargs["pem_path"])


def submit(kwargs, outdir):
    from autoqchem.molecule import molecule
    manager = _manager(kwargs)
    mol_options = pick(kwargs, "num_conf", "engine", "rdkit_ff", "large_mol")
    if "num_conf" in mol_options:
        mol_options["num_conf"] = int(mol_options["num_conf"])
    job_options = pick(kwargs, "workflow_type", "theory", "solvent", "light_basis_set",
                       "heavy_basis_set", "wall_time")
    # Free-text fields: "None" (no solvent) must stay the string Gaussian expects.
    job_options = {key: str(value) for key, value in job_options.items()}
    smiles = _smiles(kwargs, outdir)
    for item in smiles:
        say("creating jobs for " + item)
        manager.create_jobs_for_molecule(molecule(item, **mol_options), **job_options)
    manager.submit_jobs()
    say("{} molecule(s) submitted. Retrieve them later with the same tags.".format(len(smiles)))


def retrieve(kwargs, _outdir):
    manager = _manager(kwargs)
    manager.retrieve_jobs()
    tags = as_list(kwargs.get("tags"))
    if not tags:
        fail("dataset tags are required to store the finished molecules")
    manager.upload_done_molecules_to_db(tags=tags)
    say("finished molecules uploaded under tags " + ", ".join(tags))


def export(kwargs, outdir):
    from autoqchem.db_functions import descriptors
    tags = as_list(kwargs.get("tags"))
    if not tags:
        fail("dataset tags are required")
    tables = descriptors(tags=tags, presets=as_list(kwargs.get("presets")) or ["global"],
                         conf_option=kwargs.get("conf_option", "boltzmann"),
                         solvent="ALL", functional="ALL", basis_set="ALL",
                         substructure=kwargs.get("substructure", ""))
    if not tables:
        fail("nothing to export: check the tags and presets")
    stem = os.path.splitext(str(kwargs.get("output_csv") or "autoqchem_descriptors.csv"))[0]
    for name, frame in tables.items():
        path = os.path.join(outdir, "{}_{}.csv".format(stem, name))
        frame.to_csv(path)
        say("wrote " + path)


def _action(kwargs):
    """The input type decides the action; retrieve/export use the explicit choice."""
    if kwargs.get("logs"):
        return "parse"
    if kwargs.get("smiles") or kwargs.get("smiles_csv"):
        return "submit"
    return str(kwargs.get("action") or "export")


def main():
    kwargs, job = load_job()
    action = _action(kwargs)
    actions = {"parse": parse, "submit": submit, "retrieve": retrieve, "export": export}
    if action not in actions:
        fail("unknown action " + action)
    actions[action](kwargs, job["output_dir"])


if __name__ == "__main__":
    main()
