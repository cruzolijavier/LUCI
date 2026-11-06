# universal_thermoGNN: upstream documentation

Source: https://github.com/chimie-paristech-CTM/universal_thermoGNN

## universal_thermoGNN/README.md

# universal_thermoGNN — Evidential Deep Learning + Active Learning

Code accompanying the paper. Active-learning training workflow built on an
evidential-deep-learning (EDL) head attached to a
[chemprop](https://github.com/chemprop/chemprop) v2.2.1 MPNN, plus the
postprocessing pipeline used to clean the ThermoMLIP-derived training data.

`chemprop/` is a **fork of chemprop v2.2.1** (MIT, preserved in `LICENSE.txt`).
All scripts at the repository root are new.

The evidential GNN scores an unlabelled pool, the query step picks the highest-uncertainty
molecules, ThermoMLIP labels them with thermodynamic properties (ΔE, ΔH, ΔG and the
formation version), the labelled set is folded back into training, and the loop repeats
until the desired final dataset is reached.

## Data and trained models

The repository includes all dataset splits locally:

```
dataset/
  initial/                 # initial train.csv, val.csv, test.csv split
  iteration_1/ ... iteration_6/
                           # train.csv, val.csv, test.csv per AL iteration
ckpt/
  iter6/model.ckpt.zst     # compressed iteration-6 checkpoint (75 MB)
```

The training data and corresponding trained checkpoints are also deposited on
figshare: **https://doi.org/10.6084/m9.figshare.32126155**

Each CSV contains columns: `mol_id`, `dataset`, `smiles`, `formation_ee`,
`formation_enthalpy`, `formation_gibbs`. The 6,476-molecule test set is fixed
across the initial split and all active-learning iterations. Training grows
from 51,939 molecules in `initial` to 201,411 molecules in `iteration_6` as
each active-learning cycle adds labelled molecules.

### Training and evaluation

```bash
# Train
python train_edl_mol_fp.py \
  --train_path dataset/iteration_6/train.csv \
  --val_path   dataset/iteration_6/val.csv \
  --test_path  dataset/iteration_6/test.csv \
  --results_dir results_iter6

# Reproduce paper results (decompress checkpoint first)
zstd -d ckpt/iter6/model.ckpt.zst -o ckpt/iter6/model.ckpt
python predict.py \
  --checkpoint ckpt/iter6 \
  --input dataset/iteration_6/test.csv

# Predict on new molecules (only a SMILES column is needed)
python predict.py \
  --checkpoint ckpt/iter6 \
  --input your_molecules.csv

# Optional: convert predicted formation energies back to absolute energies (Hartree)
python convert_formation_to_energy.py
```

## Install

```bash
conda env create -f environment.yml
conda activate universal-dataset-edl
pip install -e .
```

## Top-level scripts

| Script | Purpose |
|---|---|
| `train_baseline.py` | Train a baseline chemprop MPNN model. |
| `train_edl_atomic_fp.py` | Train the atomic-level EDL model (AtomicAggregation + AtomicEvidentialFFNv6). |
| `train_edl_mol_fp.py` | Train the molecular-level EDL model (NormAggregation + EvidentialFFN). |
| `hpopt_edl_atomic_fp.py` | Ray Tune hyperparameter sweep for the EDL model. |
| `predict.py` | Evaluate a trained checkpoint on a test set (RMSE, MAE, R2). |
| `convert_formation_to_energy.py` | Convert predicted formation energies (kcal/mol) back to absolute energies (Hartree). |
| `predict_remaining_uncertainty.py` | Predict + per-molecule uncertainty on the unlabelled pool. |
| `active_learning_sampling.py` | Select the next AL batch (uncertainty + Tanimoto diversity). |
| `extract_gas_thermo.py` | Postprocess 1 — parse gas-phase E/H/G/S/ZPE from `calculation.log`. |
| `check_structure_integrity.py` | Postprocess 2 — compare optimised-XYZ heavy-atom graph vs SMILES graph. |
| `filter_broken_structures.py` | Postprocess 3 — split thermo CSV into clean / broken using the check. |
| `remove_energy_outliers.py` | Postprocess 4 — per-element regression on `gas_gibbs`, drop residuals > Q3 + 3·IQR. |

Postprocess pipeline example:

```bash
python extract_gas_thermo.py        --input samples.csv         --output thermo.csv
python check_structure_integrity.py --input thermo.csv          --output check.csv
python filter_broken_structures.py  --input thermo.csv --check check.csv \
    --output-clean clean.csv --output-broken broken.csv
python remove_energy_outliers.py    --input clean.csv \
    --output-clean no_outliers.csv --output-outliers outliers.csv
```

## Citation

Cite this work (`CITATION.cff`) **and** the upstream chemprop paper:

```bibtex
@article{heid2024chemprop,
  title={Chemprop: a machine learning package for chemical property prediction},
  author={Heid, Esther and Greenman, Kevin P and Chung, Yunsie and Li, Shih-Cheng and Graff, David E and Vermeire, Florence H and Wu, Haoyang and Green, William H and McGill, Charles J},
  journal={Journal of Chemical Information and Modeling},
  volume={64}, number={1}, pages={9--17}, year={2024},
  publisher={ACS Publications}
}
```

## License

MIT — see `LICENSE.txt`.

## universal_thermoGNN/docs/source/quickstart.rst

.. _quickstart:

Quickstart
==========

To get started with Chemprop, first install the package using the instructions in the :ref:`installation` section. Once you have Chemprop installed, you can train a model on your own data or use the pre-packaged solubility dataset to get a feel for how the package works.

Let's use the solubility data that comes pre-packaged in the Chemprop directory:

.. code-block:: text

    $ head tests/data/regression.csv
    smiles,logSolubility
    OCC3OC(OCC2OC(OC(C#N)c1ccccc1)C(O)C(O)C2O)C(O)C(O)C3O,-0.77
    Cc1occc1C(=O)Nc2ccccc2,-3.3
    CC(C)=CCCC(C)=CC(=O),-2.06
    c1ccc2c(c1)ccc3c2ccc4c5ccccc5ccc43,-7.87
    c1ccsc1,-1.33
    c2ccc1scnc1c2,-1.5
    Clc1cc(Cl)c(c(Cl)c1)c2c(Cl)cccc2Cl,-7.32
    CC12CCC3C(CCc4cc(O)ccc34)C2CCC1O,-5.03
    ClC4=C(Cl)C5(Cl)C3C1CC(C2OC12)C3C4(Cl)C5(Cl)Cl,-6.29
    ...

Now we're ready to train a simple Chemprop model:

.. code-block:: bash

    chemprop train --data-path tests/data/regression.csv \
        --task-type regression \
        --output-dir train_example

This will train a model on the solubility dataset (``tests/data/regression.csv``) and save the model and training logs in the ``train_example`` directory. You should see some output printed to your terminal that shows the model architecture, number of parameters, and a progress bar for each epoch of training. At the end, you should see something like:

.. code-block:: text

    ───────────────────────────────────────────────────────
       Test metric             DataLoader 0
    ───────────────────────────────────────────────────────
        test/mse             0.7716904154601469
    ───────────────────────────────────────────────────────

With our trained model in hand, we can now use it to predict solubilities of new molecules. In the absence of additional data, for demonstration purposes, let's just test on the same molecules that we trained on:

.. code-block:: bash

    chemprop predict --test-path tests/data/regression.csv \
        --model-path train_example/model_0/best.pt \
        --preds-path train_example/predictions.csv

This should output a file ``train_example/predictions_0.csv`` containing the predicted log(solubility) values for the molecules contained in ``tests/data/regression.csv``.

.. code-block:: text

    $ head train_example/predictions_0.csv
    smiles,logSolubility,pred_0
    OCC3OC(OCC2OC(OC(C#N)c1ccccc1)C(O)C(O)C2O)C(O)C(O)C3O,-0.77,-1.0349703
    Cc1occc1C(=O)Nc2ccccc2,-3.3,-3.0304263
    CC(C)=CCCC(C)=CC(=O),-2.06,-2.0320206
    ...

Given that our test data is identical to our training data, it makes sense that the predictions are similar to the ground truth values.

In the rest of this documentation, we'll go into more detail about how to:

* :ref:`Install Chemprop<installation>`
* :ref:`Customize model architecture and task type<train>`
* :ref:`Specify training parameters: split type, learning rate, batch size, loss function, etc. <train>`
* :ref:`Use Chemprop as a Python package <notebooks>`
* :ref:`Perform a hyperparameter optimization <hpopt>`
* :ref:`Generate a molecular fingerprint <fingerprint>`
.. * :ref:`Quantify prediction uncertainty<predict>`

Summary
-------

* Install Chemprop using the instructions in the :ref:`installation` section
* Train a model with ``chemprop train --data-path <input_path> --task-type <task> --output-dir <dir>``
* Use a saved model for prediction with ``chemprop predict --test-path <test_path> --checkpoint-dir <dir> --preds-path <path>``

.. _GitHub repository: https://github.com/chemprop/chemprop
..
    .. _FreeSolv dataset: https://pubmed.ncbi.nlm.nih.gov/24928188/

## universal_thermoGNN/docs/source/tutorial/cli/predict.rst

.. _predict:

Prediction
----------

To load a trained model and make predictions, run:

.. code-block::
   
    chemprop predict --test-path <test_path> --model-paths <[model_paths]>

where :code:`<test_path>` is the path to the data to test on, and :code:`<[model_paths]>` is the location of checkpoint(s) or model file(s) to use for prediction. It can be a path to either a single pretrained model checkpoint (.ckpt) or single pretrained model file (.pt), a directory that contains these files, or a list of path(s) and directory(s). If a directory, will recursively search and predict on all found (.pt) models. By default, predictions will be saved to the same directory as the test path. If desired, a different directory can be specified by using :code:`--preds-path <path>`. The predictions <path> can end with either .csv or .pkl, and the output will be saved to the corresponding file type.

For example:

.. code-block::
  
    chemprop predict --test-path tests/data/smis.csv \
        --model-path tests/data/example_model_v2_regression_mol.ckpt \
        --preds-path preds.csv

Specifying Data to Parse
^^^^^^^^^^^^^^^^^^^^^^^^

By default, Chemprop will assume that the the 0th column in the data .csv will have the data. To use a separate column, specify:

 * :code:`--smiles-columns` Text label of the column that includes the SMILES strings

If atom-mapped reaction SMILES are used, specify:

 * :code:`--reaction-columns` Text labels of the columns that include the reaction SMILES

If :code:`--reaction-mode` was specified during training, those same flags must be specified for the prediction step.

.. _performant-prediction:

Performant Prediction
^^^^^^^^^^^^^^^^^^^^^

Prediction can be accelerated using molecular featurizer package called ``cuik-molmaker``. This package is not installed by default, but can be installed using the script ``check_and_install_cuik_molmaker.py``. In order to enable the accelerated featurizer, use the :code:`--use-cuikmolmaker-featurization` flag. This featurizer also performs on-the-fly featurization of molecules and reduces memory usage which is particularly useful for large datasets.

Uncertainty Quantification
--------------------------

To load a trained model and make uncertainty quantification, run:

.. code-block::
   
    chemprop predict --test-path <test_path> \
        --cal-path <cal_path> \
        --model-paths <[model_paths]> \
        --uncertainty-method <method> \
        --calibration-method <method> \
        --evaluation-methods <[methods]>

where :code:`<test_path>` is the path to the data to test on, :code:`<cal_path>` is the calibration dataset used for uncertainty calibration if needed, and :code:`<[model_paths]>` is the location of checkpoint(s) or model file(s) to use for prediction. The uncertianty estimation, calibration, and evaluations methods are detailed below. 

Uncertainty Estimation
^^^^^^^^^^^^^^^^^^^^^^

The uncertainty of predictions made in Chemprop can be estimated by several different methods. Uncertainty estimation is carried out alongside model value prediction and reported in the predictions csv file when the argument :code:`--uncertainty-method <method>` is provided. If no uncertainty method is provided, then only the model value predictions will be carried out. The available methods are:

 * :code:`dropout`
 * :code:`ensemble`
 * :code:`quantile-regression`
 * :code:`mve`
 * :code:`evidential-total`, :code:`evidential-epistemic`, :code:`evidential-aleatoric`
 * :code:`classification`
 * :code:`classification-dirichlet`
 * :code:`multiclass`
 * :code:`multiclass-dirichlet`

Uncertainty Calibration
^^^^^^^^^^^^^^^^^^^^^^^

Uncertainty predictions may be calibrated to improve their performance on new predictions. Calibration methods are selected using :code:`--calibration-method <method>`, options provided below. An additional dataset to use in calibration is provided through :code:`--cal-path <path>`, along with necessary features like :code:`--cal-descriptors-path <path>`. As with the data used in training, calibration data for multitask models are allowed to have gaps and missing targets in the data.

**Regression**:

 * :code:`zscaling` Assumes that errors are normally distributed according to the estimated variance for each prediction. Applies a constant multiple to all stdev or interval outputs in order to minimize the negative log likelihood for the normal distributions. (https://arxiv.org/abs/1905.11659)
 * :code:`zelikman-interval` Assumes that the error distribution is the same for each prediction but scaled by the uncalibrated standard deviation for each. Multiplies the uncalibrated standard deviation by a factor necessary to cover the specified interval of the calibration set. Does not assume a Gaussian distribution using :code:`--calibration-interval-percentile <float>` which is default ot 95. (https://arxiv.org/abs/2005.12496)
 * :code:`mve-weighting` For use with ensembles of models trained with mve or evidential loss function. Uses a weighted average of the predicted variances to achieve a minimum negative log likelihood of predictions. (https://doi.org/10.1186/s13321-021-00551-x)
 * :code:`conformal-regression` Generates an interval of variable size for each prediction based on quantile predictions of the data such that the actual value has probability :math:`1 - \alpha` of falling in the interval. The desired error rate is controlled using the parameter :code:`--conformal-alpha <float>` which is set by default to 0.1. (https://arxiv.org/abs/2107.07511)

**Classification**:

 * :code:`platt` Uses a linear scaling before the sigmoid function in prediction to minimize the negative log likelihood of the predictions. (https://arxiv.org/abs/1706.04599)
 * :code:`isotonic` Fits an isotonic regression model to the predictions. Prediction outputs are transformed using a stepped histogram-style to match the empirical probability observed in the calibration data. Number and size of the histogram bins are procedurally decided. Histogram bins are wider in the regions of the model output that are less reliable in ordering confidence. (https://arxiv.org/abs/1706.04599)
 * :code:`conformal-multilabel` Generates a pair of sets of labels :math:`C_{in} \subset C_{out}` such that the true set of labels :math:`S` satisfies the property :math:`C_{in} \subset S \subset C_{out}` with probability at least :math:`1-\alpha`. The desired error rate :math:`\alpha` can be controlled with the parameter :code:`--conformal-alpha <float>` which is set by default to 0.1. (https://arxiv.org/abs/2004.10181)

**Multiclass**:

 * :code:`conformal-multiclass` Generates a set of possible classes for each prediction such that the true class has probability :math:`1-\alpha` of falling in the set. The desired error rate :math:`\alpha` can be controlled with the parameter :code:`--conformal-alpha <float>` which is set by default to 0.1. Set generated using the basic conformal method. (https://arxiv.org/abs/2107.07511)
 * :code:`conformal-adaptive` Similar to conformal-multiclass, this method generates a set of possible classes but uses an adaptive conformal method. The desired error rate :math:`\alpha` can be controlled with the parameter :code:`--conformal_alpha <float>` which is set by default to 0.1. (https://arxiv.org/abs/2107.07511)
 * :code:`isotonic-multiclass` Calibrate multiclass classification datasets using isotonic regression. It uses a one-vs-all aggregation scheme to extend isotonic regression from binary to multiclass classifiers. (https://arxiv.org/abs/1706.04599)

Uncertainty Evaluation Metrics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The performance of uncertainty predictions (calibrated or uncalibrated) as evaluated on the test set using different evaluation metrics as specified with :code:`--evaluation-methods <[methods]>`.
Evaluation scores will only appear in the output trace. Multiple evaluation methods can be provided and they will be calculated separately for each model task. Evaluation is only available when the target values are provided with the data in :code:`--test-path <test_path>`. As with the data used in training, evaluation data for multitask models are allowed to have gaps and missing targets in the data.

 .. * Any valid classification or multiclass metric. Because classification and multiclass outputs are inherently probabilistic, any metric used to assess them during training is appropriate to evaluate the confidences produced after calibration.

 * :code:`nll-regression`, :code:`nll-classification`, :code:`nll-multiclass` Returns the average negative log likelihood of the real target as indicated by the uncertainty predictions. Enabled for regression, classification, and multiclass dataset types.
 * :code:`spearman` A regression evaluation metric. Returns the Spearman rank correlation between the predicted uncertainty and the actual error in predictions. Only considers ordering, does not assume a particular probability distribution.
 * :code:`ence` Expected normalized calibration error. A regression evaluation metric. Bins model prediction according to uncertainty prediction and compares the RMSE in each bin versus the expected error based on the predicted uncertainty variance then scaled by variance. (discussed in https://doi.org/10.1021/acs.jcim.9b00975)
 * :code:`miscalibration_area` A regression evaluation metric. Calculates the model's performance of expected probability versus realized probability at different points along the probability distribution. Values range (0, 0.5) with perfect calibration at 0. (discussed in https://doi.org/10.1021/acs.jcim.9b00975)
 * :code:`conformal-coverage-regression`, :code:`conformal-coverage-classification`, :code:`conformal-coverage-multiclass` Measures the empirical coverage of the conformal methods, that is the proportion of datapoints that fall within the output set or interval. Must be used with a conformal calibration method which outputs a set or interval. The metric can be used with multiclass, multilabel, or regression conformal methods.

Different evaluation metrics consider different aspects of uncertainty. It is often appropriate to consider multiple metrics. For intance, miscalibration error is important for evaluating uncertainty magnitude but does not indicate that the uncertainty function discriminates well between different outputs. Similarly, spearman tests ordering but not prediction magnitude.

Evaluations can be used to compare different uncertainty methods and different calibration methods for a given dataset. Using evaluations to compare between datasets may not be a fair comparison and should be done cautiously.
