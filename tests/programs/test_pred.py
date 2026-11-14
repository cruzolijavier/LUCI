"""LUCI-PRED with real inputs: ROBERT's full workflow on a small regression dataset.

inputs/robert_regression.csv: 36 datapoints, y = 3*x1 - 2*x2 + 0.5*x3 + noise (sd 0.3),
plus a column of random numbers (noise_col) that carries no information.
"""

import pytest

from program_helpers import (  # noqa: F401 (luci and work are fixtures)
    luci, luci_data, read_csv, require_env, work,
)

pytestmark = pytest.mark.programs


def test_robert_full_workflow(work, luci):
    require_env("robert")
    run = luci(work, "pred", "--backend", "robert", "--", "--csv_name", "robert_regression.csv",
               "--names", "name", "--y", "yield", "--model", "[MVL,RF]", "--repeat_kfolds", "2").ok()
    folder = work / "LUCI_PRED" / "ROBERT"
    assert run.output_folder() == folder
    for step in ("CURATE", "GENERATE", "VERIFY", "PREDICT"):
        assert (folder / step).is_dir(), f"ROBERT did not run {step}"
    # LUCI copied the input next to the results (ROBERT rejects paths with spaces).
    assert (folder / "robert_regression.csv").is_file()
    assert list(folder.glob("ROBERT_report*.pdf")), "no PDF report"

    # The linear model wins on linear data, and its predictions are within the noise.
    best = sorted((folder / "GENERATE" / "Best_model" / "PFI").glob("*_PFI.csv"))
    assert best and best[0].name.startswith("MVL"), [p.name for p in best]
    predictions = read_csv(folder / "PREDICT" / "MVL_PFI.csv")
    assert len(predictions) == 36
    errors = [abs(float(r["yield"]) - float(r["yield_pred"])) for r in predictions]
    assert sum(errors) / len(errors) < 1.0
    # The model keeps the informative descriptors and drops the random one.
    columns = set(predictions[0])
    assert {"x1", "x2"} <= columns and "noise_col" not in columns
    assert "ROBERT" in luci_data(work / "LUCI_PRED")


def test_robert_missing_target_column_fails_clearly(work, luci):
    require_env("robert")
    run = luci(work, "pred", "--backend", "robert", "--", "--csv_name", "robert_regression.csv",
               "--names", "name", "--y", "selectivity")
    assert run.code != 0
    assert "selectivity" in run.output
