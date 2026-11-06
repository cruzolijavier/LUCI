"""EDBO+ inside its environment: create a scope, or suggest the next batch."""

import os

from _luci_job import as_list, fail, load_job, pick, resolve, say

RUN_OPTIONS = ("objective_thresholds", "batch", "columns_features", "init_sampling_method",
               "seed", "acquisition_function", "acquisition_function_sampler")


def _check_scope(scope, objectives):
    """Catch the edits that would silently restart a campaign."""
    import csv
    from _luci_job import sniff_delimiter
    if sniff_delimiter(scope) != ",":
        fail("{} is not comma-separated (Excel with a Spanish/European locale saves ';'). Save it "
             "as 'CSV UTF-8 (comma delimited)' with a decimal point.".format(scope))
    with open(scope, newline="", encoding="utf-8-sig") as handle:
        header = next(csv.reader(handle), [])
    if "priority" in header:
        missing = [o for o in objectives if o not in header]
        if missing:
            fail("objective column(s) {} not found in {}. Columns: {}".format(
                ", ".join(missing), scope, ", ".join(header)))


def main():
    kwargs, job = load_job()
    outdir = job["output_dir"]
    try:
        from edbo.plus.optimizer_botorch import EDBOplus
    except ImportError as exc:
        fail("EDBO+ is not importable in this environment: {}".format(exc))

    if "components" in kwargs:
        components = kwargs["components"]
        if not isinstance(components, dict):
            fail("components must be a dict such as {'solvent': ['THF', 'DMSO']}")
        filename = str(kwargs.get("scope_name") or "reaction.csv")
        target = os.path.join(outdir, filename)
        if os.path.exists(target):
            fail("{} already exists and may hold your results. Choose another scope file name "
                 "or output folder.".format(target))
        EDBOplus.generate_reaction_scope(components=components, directory=outdir,
                                         filename=filename, check_overwrite=False)
        say("Scope written to " + os.path.join(outdir, filename))
        return

    if "filename" not in kwargs:
        fail("give either a scope CSV (suggest) or components (create a scope)")
    scope = resolve(kwargs["filename"], outdir)
    if not os.path.isfile(scope):
        fail("scope file not found: " + scope)
    objectives = as_list(kwargs.get("objectives"))
    aliases = {"max": "max", "maximize": "max", "maximise": "max",
               "min": "min", "minimize": "min", "minimise": "min"}
    modes = []
    for mode in as_list(kwargs.get("objective_mode")):
        if str(mode).lower() not in aliases:
            fail("objective_mode must be max or min for each objective, got {!r}".format(mode))
        modes.append(aliases[str(mode).lower()])
    if not objectives:
        fail("objectives are required, e.g. ['yield']")
    if len(modes) != len(objectives):
        fail("objective_mode needs one max/min per objective")
    _check_scope(scope, objectives)
    options = pick(kwargs, *RUN_OPTIONS)
    if "objective_thresholds" in options:
        options["objective_thresholds"] = [None if str(t) == "None" else float(t)
                                           for t in as_list(options["objective_thresholds"])]
    if "columns_features" in options and options["columns_features"] != "all":
        options["columns_features"] = as_list(options["columns_features"])
    for key in ("batch", "seed"):
        if key in options:
            options[key] = int(options[key])
    directory, filename = os.path.split(scope)
    say("Suggesting the next batch for {} ({})".format(filename, ", ".join(objectives)))
    EDBOplus().run(objectives=objectives, objective_mode=modes, directory=directory,
                   filename=filename, **options)
    say("Updated {}: priority 1 marks the experiments to run next.".format(scope))
    predictions = os.path.join(directory, "pred_" + filename)
    if os.path.isfile(predictions):
        say("Model predictions: " + predictions)


if __name__ == "__main__":
    main()
