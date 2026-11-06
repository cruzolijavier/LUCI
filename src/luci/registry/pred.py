"""LUCI-PRED: machine-learning models trained on your data, and their predictions."""

from __future__ import annotations

from .common import CSV_FILTER, opt, switch
from .model import FLAG_ONLY, INPUT_GROUP, InputMode, Launch, ProgramSpec, Tags, Variant

ROBERT = ProgramSpec(
    key="robert", name="ROBERT", layer="pred",
    description="Automated machine-learning workflow: curation, model screening, validation, "
                "predictions and a PDF report.",
    tags=Tags(inputs=("table",)),
    variants=(Variant("default", "ROBERT", env="robert",
                      launch=Launch("cli", ("python", "{runners}/robert_cli.py"),
                                    copy_inputs=True)),),
    docs_url="https://robert.readthedocs.io/en/latest/",
    input_modes=(InputMode("csv_name", "Training CSV", "--csv_name", CSV_FILTER,
                           help="CSV with one row per datapoint and one column per descriptor."),),
    options=(
        opt("csv_test", "Test set", "path", group=INPUT_GROUP, file_filter=CSV_FILTER,
            tooltip="Optional CSV with an external test set, kept out of training and used only to "
                    "score the final model."),
        opt("names", "Name column", "columns", group=INPUT_GROUP, required=True,
            tooltip="Column holding the identifier of each datapoint, so predictions can be traced "
                    "back to a row."),
        opt("y", "Target column", "columns", group=INPUT_GROUP, required=True,
            tooltip="Column with the property the model learns to predict."),
        opt("type", "Problem type", "choice", choices=(("Regression", "reg"), ("Classification", "clas")), default="reg", group=INPUT_GROUP,
            tooltip="Whether the target is a number to fit (regression) or a label to assign "
                    "(classification). ROBERT switches to classification on its own when the target "
                    "only takes two values."),
        opt("ignore", "Ignored columns", "multi_columns", group=INPUT_GROUP,
            tooltip="Columns carried through to the output but not used as descriptors, such as "
                    "identifiers or notes."),
        opt("step", "Workflow step", "choice", group="Workflow", value_is_flag=True,
            choices=(("Full workflow", ""), ("CURATE only", "curate"), ("GENERATE only", "generate"),
                     ("VERIFY only", "verify"), ("PREDICT only", "predict"), ("REPORT only", "report")),
            tooltip="Run the whole ROBERT workflow (recommended) or a single module on the results "
                    "of a previous run."),
        opt("seed", "Random seed", "number", placeholder="0", group="Cross-validation",
            tooltip="Random seed used by the models and the splitting protocols, so a run can be reproduced."),
        opt("kfold", "Folds (k)", "number", placeholder="5", group="Cross-validation",
            tooltip="Number of folds the data is split into for cross-validation."),
        opt("repeat_kfolds", "Repeated k-folds", "number", placeholder="10", group="Cross-validation",
            tooltip="How many times the whole k-fold cross-validation is repeated."),
        opt("split", "Split method", "choice", default="auto", group="Cross-validation",
            choices=("auto", "even", "RND", "stratified", "KN", "extra_q1", "extra_q5"),
            tooltip="How datapoints are assigned to the training and test sets."),
        opt("categorical", "Categorical descriptors", "choice", choices=(("One-hot columns", "onehot"), ("Numbers", "numbers")), default="onehot",
            group="Curation",
            tooltip="How categorical descriptors are converted into numbers: one-hot columns, or a "
                    "single numbered column."),
        opt("corr_filter_x", "Remove correlated descriptors", "bool", default=True, group="Curation",
            tooltip="Discard descriptors that correlate too closely with another descriptor."),
        opt("corr_filter_y", "Remove descriptors unrelated to y", "bool", default=False, group="Curation",
            tooltip="Discard descriptors that barely correlate with the target property."),
        opt("rfecv_filter", "RFECV selection", "bool", default=True, group="Curation",
            tooltip="Select descriptors by recursive feature elimination with cross-validation, "
                    "capping how many are kept for the size of the dataset."),
        opt("thres_x", "Correlation threshold (x)", "number", placeholder="0.7", group="Curation",
            tooltip="R2 above which two descriptors count as redundant and one is discarded."),
        opt("thres_y", "Correlation threshold (y)", "number", placeholder="0.001", group="Curation",
            tooltip="R2 below which a descriptor is considered unrelated to the target and discarded."),
        opt("model", "Models", "multi_choice", group="Models",
            choices=("RF", "MVL", "GB", "NN", "GP", "AdaB", "Ridge", "Logistic"),
            default=("RF", "GB", "NN", "MVL"),
            tooltip="Machine-learning models screened during the search. Several can be selected and "
                    "ROBERT compares them."),
    ),
    legacy_keys=("robert", "pred"),
)

PROGRAMS = (ROBERT,)

__all__ = ["PROGRAMS", "FLAG_ONLY"]
