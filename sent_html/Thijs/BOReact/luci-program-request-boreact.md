# LUCI program request: BOReact

BoReact is a user-friendly desktop UI for Bayesian Optimization (BO) in chemistry workflows. It is designed for researchers who want practical experiment recommendations without having to build a BO stack from scratch.

**Docs:** https://github.com/chimie-paristech-CTM/BoReact

## Installation

```
uv sync
uv run python BoReact/ui/main_window.py
```

## Flags

| Flag | What it does | Default | Example / options |
|---|---|---|---|
| --experimental_data | Dataset | none | my_campaing.xlsx |
| --batch_size | Number of recommendations | 1 | 5 |
| --recommender | Algorithm for effectively explore the search space | bayesian | random / bayesian / LHS |
| --target | Observable to be optimized | none | ["yield"], ["yield", "cost"] |
| --acquisition_function | Evaluate the usefulness of one of more design points | qLogEI | qLogEI / UCB / qLogNEHVI / qLogNParEGO |

## Input

Users can upload an Excel file into the software, with all remaining configuration flags adjustable via dedicated buttons and panels. Each row in the file represents a single experiment, each column represents a parameter or target, and the first row contains the corresponding column headers. Excel example:

Experiment_ID | Temperature_C | Pressure_bar | Catalyst_pct | Reaction_Time_min | Yield_pct (Target)
----------------|------------------|----------------|--------------|-----------------------|-------------------
Exp_001          | 150                   | 2.5                  | 0.5               | 60                            | 82.1
Exp_002          | 160                   | 2.5                  | 0.5               | 60                            | 85.4
Exp_003          | 150                   | 3.0                  | 0.5               | 60                            | 88.2

## Output

The output will be the recommendations for the next experiments. The interface features five panels. The top four display statistical summaries from the surrogate model and data: a PCA plot of past experiments, parameter importance, the probability of the next value per parameter, and a convergence plot (or Pareto front). The bottom panel shows the recommendations, which can be exported directly to the original Excel upload template with the target column blanked out for easy reuse after the experiment.