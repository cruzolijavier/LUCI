"""ScopeBO inside its environment: featurize, build the reaction space, or suggest."""

import csv
import os
import sys

from _luci_job import as_list, fail, load_job, pick, resolve, say


def _scopebo(source_dir):
    # ScopeBO is not a package: its code is imported from the repository folder.
    sys.path.insert(0, source_dir)
    try:
        from Code.predictor import ScopeBO
    except ImportError as exc:
        fail("ScopeBO is not importable from {}: {}".format(source_dir, exc))
    return ScopeBO


def _read_smiles(path, column=None):
    """SMILES from a CSV with a header: the named column, a 'smiles' column, or the first."""
    from _luci_job import sniff_delimiter
    with open(path, newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.reader(handle, delimiter=sniff_delimiter(path)) if any(row)]
    if len(rows) < 2:
        fail("no SMILES found in {} (it needs a header row and one molecule per row)".format(path))
    header = [h.strip() for h in rows[0]]
    if column:
        if column not in header:
            fail("column '{}' not found in {}. Columns: {}".format(column, path, ", ".join(header)))
        index = header.index(column)
    else:
        matches = [i for i, h in enumerate(header) if h.lower() in ("smiles", "smi")]
        index = matches[0] if matches else 0
        if not matches:
            say("No 'smiles' column: using the first column, '{}'".format(header[0]))
    values = [row[index].strip() for row in rows[1:] if len(row) > index and row[index].strip()]
    bad = [v for v in values if " " in v or ";" in v]
    if bad:
        fail("these do not look like SMILES: {}".format(", ".join(bad[:5])))
    return values


def _objective_mode(value, objectives):
    """ScopeBO wants {'all_obj': 'max'} or {objective: 'max'|'min'}."""
    if value in (None, ""):
        return None
    if isinstance(value, dict):
        return value
    modes = as_list(value)
    if len(modes) == 1:
        return {"all_obj": str(modes[0]).lower()}
    if len(modes) == len(objectives):
        return {o: str(m).lower() for o, m in zip(objectives, modes)}
    fail("objective_mode: give max/min, one per objective, or a dict like {'all_obj': 'max'}")


def main():
    kwargs, job = load_job()
    outdir = job["output_dir"]
    ScopeBO = _scopebo(job["source_dir"])

    if "smiles_csv" in kwargs:
        smiles = _read_smiles(resolve(kwargs["smiles_csv"], outdir), kwargs.get("smiles_column"))
        filename = os.path.join(outdir, str(kwargs.get("features_name") or "reactant_features.csv"))
        say("Featurizing {} molecules with GFN2-xTB / MORFEUS".format(len(smiles)))
        ScopeBO.generate_features(smiles, filename=filename,
                                  common_core=kwargs.get("common_core") or None)
        say("Descriptors written to " + filename)
        return

    if "reactants" in kwargs:
        reactants = kwargs["reactants"]
        if isinstance(reactants, (list, tuple)):
            reactants = [resolve(r, outdir) for r in reactants]
        elif isinstance(reactants, dict):
            reactants = {resolve(k, outdir): v for k, v in reactants.items()}
        else:
            fail("reactants must be a dict such as {'reactant1.csv': 'AlkI'}")
        filename = str(kwargs.get("space_name") or "reaction_space.csv")
        options = {}
        if kwargs.get("objectives"):
            options["objectives"] = as_list(kwargs["objectives"])
        ScopeBO.create_reaction_space(reactants=reactants, directory=outdir, filename=filename,
                                      draw_suggested_samples=False, **options)
        say("Reaction space written to " + os.path.join(outdir, filename))
        return

    if "filename" not in kwargs:
        fail("choose an input: a SMILES CSV, descriptor CSVs, or a reaction space")
    space = resolve(kwargs["filename"], outdir)
    if not os.path.isfile(space):
        fail("reaction space not found: " + space)
    objectives = as_list(kwargs.get("objectives")) or ["yield"]
    options = pick(kwargs, "batch", "Vendi_pruning_fraction", "acquisition_function_mode", "seed")
    mode = _objective_mode(kwargs.get("objective_mode"), objectives)
    if mode is not None:
        for wanted in mode.values():
            if wanted not in ("max", "min"):
                fail("objective_mode values must be max or min, got {!r}".format(wanted))
        options["objective_mode"] = mode
    for key in ("batch", "seed", "Vendi_pruning_fraction"):
        if key in options:
            options[key] = int(options[key])
    directory, filename = os.path.split(space)
    say("Suggesting the next substrates for " + filename)
    ScopeBO().run(objectives=objectives, directory=directory, filename=filename,
                  show_suggestions=False, **options)
    say("Updated {}: priority 1 marks the substrates to run next.".format(space))


if __name__ == "__main__":
    main()
