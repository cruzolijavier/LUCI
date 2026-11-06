# ROBERT: upstream documentation

Source: https://github.com/jvalegre/robert

## robert/README.md

#
## <p align="center"> ROBERT (Refiner and Optimizer of a Bunch of Existing Regression Tools)</p>

[](https://app.circleci.com/pipelines/github/jvalegre/robert)
[](https://codecov.io/gh/jvalegre/robert)
[](https://www.pepy.tech/projects/robert)
[](https://robert.readthedocs.io/)
[](https://pypi.org/project/robert/)

## Documentation  
Full documentation with installation instructions, technical details and examples can be found in [Read the Docs](https://robert.readthedocs.io).  

Don't miss out the latest hands-on tutorials from our [YouTube channel](https://www.youtube.com/channel/UCHRqI8N61bYxWV9BjbUI4Xw)!

## Recommended installation
1. (Only once) Create new conda environment: `conda create -n robert python=3.10`  
2. Activate conda environment: `conda activate robert`  
3. Install ROBERT using pip: `pip install robert`
4. Install RDKit (only if you plan to use easyROB): `pip install rdkit`
5. Install libraries for the PDF report `conda install -y -c conda-forge glib gtk3 pango mscorefonts`
* Inexperienced users should visit the *Users with no Python experience* section in [Read the Docs](https://robert.readthedocs.io).
## Update the program
1. Update to the latest version: `pip install robert --upgrade`

## Developers and help desk  
List of main developers and contact emails:  
  - [ ] [Juan V. Alegre-Requena](https://orcid.org/0000-0002-0769-7168). Contact: [jv.alegre@csic.es](mailto:jv.alegre@csic.es)  
  - [ ] [David Dalmau Ginesta](https://orcid.org/0000-0002-2506-6546). Contact: [ddalmau@unizar.es](mailto:ddalmau@unizar.es)
  - [ ] [Miguel Martinez Fernandez](https://orcid.org/0009-0002-8538-7250). Contact [miguel.martinez@csic.es](mailto:miguel.martinez@csic.es)
  - [ ] [Luis Giner Tendero](https://github.com/LlGinerT/). Contact [lginertendero@gmail.com](mailto:lginertendero@gmail.com)

For suggestions and improvements of the code (greatly appreciated!), please reach out through the issues and pull requests options of Github.  

## License
ROBERT is freely available under an [MIT](https://opensource.org/licenses/MIT) License  

## Special acknowledgements
J.V.A.R. - The acronym ROBERT is dedicated to **ROBERT Paton**, who was a mentor to me throughout my years at Colorado State University and who introduced me to the field of cheminformatics. Cheers mate!

D.D.G. - The style of the ROBERT_report.pdf file was created with the help of **Oliver Lee** (2023, Zysman-Colman group at University of St Andrews).

J.V.A.R. and D.D.G. - The improvements from v1.0 to v1.2 are largely the result of insightful discussions with **Matthew Sigman** and his students, **Jamie Cadge** and **Simone Gallarati** (2024, University of Utah).

We really THANK all the testers for their feedback and for participating in the reproducibility tests, including:

* **David Valiente** (2022-2023, Universidad Miguel Hernández)
* **Heidi Klem** (2023, Paton group at Colorado State University)
* **Iñigo Iribarren** (2023, Trujillo group at Trinity College Dublin)
* **Guilian Luchini** (2023, Paton group at Colorado State University)
* **Alex Platt** (2023, Paton group at Colorado State University)
* **Oliver Lee** (2023, Zysman-Colman group at University of St Andrews)
* **Xinchun Ran** (2023, Yang group at Vanderbilt University)

## How to cite ROBERT
If you use any of the ROBERT modules, please include this citation:  
* Dalmau, D.; Alegre Requena, J. V. ROBERT: Bridging the Gap between Machine Learning and Chemistry. *Wiley Interdiscip. Rev. Comput. Mol. Sci.* **2024**, *14*, e1733.

If you use ROBERT in low-data regimes, please also include this citation:  
* Dalmau, D.; Sigman, M. S.; Alegre-Requena, J. V. Machine learning workflows beyond linear models in low-data regimes. *Chem. Sci.* **2025**, *16*, 8555–8560.

If you use the AQME module, please include this citation:  
* Alegre-Requena et al., AQME: Automated Quantum Mechanical Environments for Researchers and Educators. *Wiley Interdiscip. Rev. Comput. Mol. Sci.* **2023**, *13*, e1663.

Additionally, please include the corresponding reference for Scikit-learn, SHAP and BayesianOptimization:  
* Pedregosa et al., Scikit-learn: Machine Learning in Python. *J. Mach. Learn. Res.* **2011**, *12*, 2825-2830.  
* Lundberg et al., From local explanations to global understanding with explainable AI for trees. *Nat. Mach. Intell.* **2020**, *2*, 56–67.
* Fernando Nogueira, {Bayesian Optimization}: Open source constrained global optimization tool for {Python}, **2014**, https://github.com/bayesian-optimization/BayesianOptimization

## robert/docs/Modules/aqme.rst

.. aqme-modules-start

From SMILES to predictors
-------------------------

Overview of the AQME module
+++++++++++++++++++++++++++

.. |aqme_fig| image:: images/AQME.jpg
   :width: 600

.. centered:: |aqme_fig|

Input required
++++++++++++++

This module uses a CSV file equivalent to an input of the AQME program. This CSV file must include, at least, these three columns:

* code_name
* smiles
* y_NAME (name of the target y values, i.e., solubility)

All additional variables will be kept during the whole ROBERT workflow. By default, the workflow sets:

  - :code:`--ignore "[code_name,smiles]"` (variables ignored in the model)

  - :code:`--names code_name` (name of the column containing the names of the datapoints)  

Automated protocols
+++++++++++++++++++

When executing the command line `python -m robert --aqme [OPTIONS]`, ROBERT's AQME module connects to the AQME program to perform an initial CSEARCH-RDKit conformer sampling with the following options:

.. code-block:: shell

   python -m aqme --csearch --program rdkit --input CSV_NAME.csv --sample 5

Then, the AQME program is run again to generate more than 200 RDKit and xTB Boltzmann-averaged molecular descriptors with QDESCP, using the following options:

.. code-block:: shell

   python -m aqme --qdescp --files "CSEARCH/*.sdf" --program xtb --csv_name CSV_NAME.csv

A CSV file called **AQME-ROBERT_CSV_NAME.csv** is created in the folder where the command line was executed. Afterwards, ROBERT uses this new CSV file to start a full workflow.

Example
+++++++

An example is available in **Examples/Full workflow from SMILES**.

.. aqme-modules-end

## robert/docs/Modules/curate.rst

.. curate-modules-start

Data curation
-------------

Overview of the CURATE module
+++++++++++++++++++++++++++++

.. |curate_fig| image:: images/CURATE.jpg
   :width: 800

.. centered:: |curate_fig|

Input required
++++++++++++++

This module uses a CSV containing the initial database.

Automated protocols
+++++++++++++++++++

*  Filters off correlated descriptors (with R\ :sup:`2` higher than 0.7).
*  Filters off variables with very low correlation to the target values (noise, with R\ :sup:`2` lower than 0.001). (Disabled by default)
*  Filters off duplicates.
*  Converts categorical descriptors into one-hot or numerical descriptors.
*  At the end of the curation process, the program uses scikit-learn’s RFECV with repeated K-fold cross-validation to select the most relevant descriptors. The selection can average importances across multiple models (e.g., RF, GB, ADAB) and ensures that the number of descriptors is reduced to one third of the datapoints.

Technical information
+++++++++++++++++++++

The CURATE module offers features to improve data quality. These include the removal of correlated variables, noise, and duplicated entries. These options are activated by default to reduce the complexity of the resulting predictors, 
and users can set specific thresholds for the correlation and noise filters using the "thres_x" and "thres_y" parameters. Additionally, the module facilitates the conversion of categorical data, transforming columns containing categorical variables into 
numerical or one-hot encoding values. For example, consider a variable that represents four types of carbon atoms (e.g., primary, secondary, tertiary, quaternary). This variable can be converted using the "categorical" command, offering the following options:

*	“Numbers”: It assigns numerical values (e.g., 1, 2, 3, 4) to describe the different C atom types.
*	“Onehot”: It creates a separate descriptor for each C atom type using 0s and 1s to indicate their presence.

Example
+++++++

An example is available in **Examples/Use of individual modules**.

.. curate-modules-end

## robert/docs/Modules/database.rst

.. database-start

How to create a database
------------------------

CSV file
++++++++

A CSV file, known as a "comma-separated values" file, enables you to store data in a table-structured format. 
Data records are divided by line breaks (i.e., each data record starts a new line). 

.. note:: 

   Creating CSV files is most straightforward when using a spreadsheet application, such as Microsoft Excel.
   

Database generation using Excel
+++++++++++++++++++++++++++++++

*  **Step 1:** Open a new spreadsheet in Microsoft Excel. Any spreadsheet software can be employed to convert data to CSV files.

.. |database1_fig| image:: images/1.png
   :width: 800

.. centered:: |database1_fig|

*  **Step 2:** Specify the headers (one for the names of each data point, one for each descriptor, and one for the target values) in row 1 at the top of the spreadsheet. More information regarding the selection of appropriate descriptors is available in the following section.

.. |database2_fig| image:: images/2.png
   :width: 800

.. centered:: |database2_fig|

*  **Step 3:** Enter your data into the spreadsheet under each column as needed. For example, write the compound name in cell A2, the descriptor values in cells B2, C2 and D2, and the target values in cell E2.

.. |database3_fig| image:: images/3.png
   :width: 800

.. centered:: |database3_fig|

*  **Step 4:** Go to the "File" tab and select "Save As". Select "CSV" under the "Save as type" dropdown menu and input a title for your CSV file. Then, click the "Save" button to generate your CSV file.

.. |database5_fig| image:: images/5.png
   :width: 800

.. centered:: |database5_fig|

Selection of descriptors
++++++++++++++++++++++++

In machine learning, a "descriptor" refers to a specific feature or property of the data used 
to describe or represent an entity. In the context of chemistry, descriptors are characteristics 
of molecules or complexes that are used to define their structures, behaviors, or other relevant 
attributes. There are no strict limitations in defining descriptors, but ideally, descriptors 
should encompass relevant properties that assist machine learning models in differentiating between 
compounds within the database. Descriptors can be specified using experimental measurements (i.e., 
density, melting point, etc.) and theoretical methods (i.e., DFT properties, NBO charges, etc.). 

When creating a database, users have two approaches:

.. |br| raw:: html

   <br />

**1. User-Defined Descriptors**
|br|
Users can utilize their own descriptors, whether obtained experimentally or through computational methods.

**2. Automated: SMILES to Descriptors**
|br|
If users don't have pre-calculated descriptors, they can use the automatic generation of descriptors with the AQME module.

.. |database6_fig| image:: images/6.png
   :width: 800

.. centered:: |database6_fig|

* **User-defined descriptors**

If users want to use descriptors that have been measured or calculated before, they have 
to enter them manually into the database. Researchers can use experimental or 
theoretical descriptors, or a mix of both to define their problem. For example,  
in the article `J. Am. Chem. Soc. 2022, 144, 9586 <https://pubs.acs.org/doi/10.1021/jacs.1c13397>`__, 
the authors wanted to correlate the equilibrium energies (ΔG) obtained with 20 different solvents 
using a machine learning model.

.. |database7_fig| image:: images/7.png
   :width: 800

.. centered:: |database7_fig|

In this case, the authors needed to differentiate the solvents using properties/descriptors 
(defining the problem). To achieve this, they constructed a set of 17 molecular descriptors that captured 
electronic and structural differences between the solvents. These descriptors included the 
dielectric constant (ε), the second COSMO σ-moment, which characterizes a molecule's overall electrostatic 
polarity (Sig2), and the McGowan molar volume (V). This is how the database was structured:

.. |database8_fig| image:: images/8.png
   :width: 800

.. centered:: |database8_fig|

* **Automated: SMILES to descriptors**

When users don't have previously measured/calculated descriptors, they can employ AQME to generate 
molecular and atomic descriptors. Let's consider the article 
`J. Chem. Inf. Comput. Sci. 2004, 44, 1000 <https://pubs.acs.org/doi/10.1021/ci034243x>`__, 
which includes a database with SMILES strings and aqueous solubility values in its electronic supporting 
information. A solubility predictor can be developed using this database, as it includes 
columns with the names of the molecules, SMILES strings of the molecules, and the property to be 
predicted (aqueous solubility in this case). The titles of the first two columns must be adjusted 
to "code_name" and "SMILES", respectively. This is how the database would be structured:

.. |database9_fig| image:: images/9.png
   :width: 800

.. centered:: |database9_fig|

ROBERT will then be executed with one command line (see the *From SMILES to predictors* section and the *Full workflow from SMILES* example), 
generating results like these:

.. |database10_fig| image:: images/10.png
   :width: 800

.. centered:: |database10_fig|

## robert/docs/Modules/generate.rst

.. generate-modules-start

Screening of ML models
----------------------

Overview of the GENERATE module
+++++++++++++++++++++++++++++++

.. |generate_fig| image:: images/GENERATE.jpg
   :width: 600

.. centered:: |generate_fig|

BO hyperoptimization
+++++++++++++++++++++

.. |bo_fig| image:: images/BO.jpg
   :width: 600

.. centered:: |bo_fig|

Input required
++++++++++++++

This module uses a curated CSV (preferrably coming from a CURATE job).

Automated protocols
+++++++++++++++++++

*  Splits the dataset into training and test sets using various strategies (KN, RND, STRATIFIED, EVEN, EXTRA_Q1, EXTRA_Q5). By default, the "EVEN" strategy is used, which creates bins across the full y-value range and selects central points. For unbalanced data, a stratified approach is applied.
*  Hyperoptimizes multiple ML models using a Bayesian Optimization approach, employing an objective function that combines the error from a 10-times 5-fold CV and a sorted CV to minimize overfitting.
*  Filters off descriptors with low permutation feature importance (PFI). New models are generated parallely, (1) No PFI and (2) PFI-filtered models.  
*  Creates a heatmap plot with different model types. One plot is generated for No PFI models and another for PFI-filtered models.  
*  Selects and stores the best No PFI and PFI models.  

Technical information
+++++++++++++++++++++

The GENERATE module performs an exploration of various ML algorithms. It uses built-in ML models from scikit-learn [1]. These models are hyperoptimized using Bayesian Optimization [2] to find their optimal parameters.

The software automatically generates a heatmap displaying RMSE values obtained from hyperoptimized algorithms. Furthermore, it performs permutation feature importance (PFI) analysis to identify the most influential descriptors and generate new models with only those descriptors. Users have the flexibility to fine-tune the PFI filter threshold using the "PFI_threshold" parameter. By default, this threshold removes features that contribute less than 4% to the model's R2. While this filter is activated by default, users can deactivate it by setting the "pfi_filter" option to False.

Users can choose between different modes for data splitting using the "split" option: (KN, RND, STRATIFIED, EVEN, EXTRA_Q1, EXTRA_Q5). The selection of ML algorithms during screening is tuned through the "model" parameter, offering a range of popular options such as Random Forests (RF), Multivariate Linear Models (MVL), Gradient Boosting (GB), Gaussian Process (GP), AdaBoost Regressor (AdaB), MLP Regressor Neural Network (NN), and Voting Regressor (VR).

20% of the data is used as a test set before hyperoptimization. This algorithm ensures an even distribution of data points across the range of y values, facilitating a balanced evaluation of predictions across the low, mid, and high y-value ranges.

This module is designed to handle both regression and classification problems, optimizing either the RMSE (regression) or MCC (classification) of the validation set during the hyperoptimization process. Users can adjust the error type for optimization with the "error_type" keyword, which offers the following options: RMSE, MAE, and R2 for regression tasks, and Matthew's correlation coefficient (MCC), F1 score, and accuracy for classification tasks.

* [1] `Scikit-learn: Machine Learning in Python <https://jmlr.csail.mit.edu/papers/v12/pedregosa11a.html>`__
* [2] `Bayesian Optimization: Open source constrained global optimization tool for Python <https://github.com/bayesian-optimization/BayesianOptimization>`

Example
+++++++

An example is available in **Examples/Use of individual modules**.

.. generate-modules-end

## robert/docs/Modules/predict.rst

.. predict-modules-start

New predictions and feature analysis
------------------------------------

Overview of the PREDICT module
++++++++++++++++++++++++++++++

.. |predict_fig| image:: images/PREDICT.jpg
   :width: 600

.. centered:: |predict_fig|

Input required
++++++++++++++

This module uses a GENERATE folder created in a GENERATE job.

Automated protocols
+++++++++++++++++++

   *  Calculates R2, MAE and RMSE (for regression) or accuracy, F1 score and MCC (for classification) for the 10x 5-fold CV (training+validation) and test sets of the best No PFI and PFI models found in a GENERATE job.
   *  Predicts values for the test set or an external test set (if any). If the measured y values are included in the external test set, the model metrics from the previous point will be included, otherwise only the predicted y values will be retrieved. 
   *  Performs an outlier analysis.
   *  Performs a SHAP feature analysis.
   *  Performs a PFI feature analysis.

Technical information
+++++++++++++++++++++

The PREDICT module uses models obtained in the GENERATE module to compute various metrics, including R2, MAE, and RMSE (regression), and accuracy, F1 score, and MCC (classification). This module also enables predictions for an external test dataset, incorporating predictor metrics when measured y-values are available. In cases where measured y-values are absent, the module shows predicted y-values in the resulting PDF report and within the csv_test folder created inside the PREDICT main folder.
Furthermore, this module conducts feature importance analysis through PFI and SHAP methods, which analyze how descriptors impact model performance. The PREDICT module also identifies outliers by measuring the absolute errors between predicted and measured y values. The detection of outliers is based on the “t_value” option, defaulted to two and measured in SD units. This default t-value identifies outliers in predictions exhibiting errors surpassing two SDs (approx. 5% of a normal population).

Example
+++++++

An example is available in **Examples/Use of individual modules**.

.. predict-modules-end

## robert/docs/Modules/verify.rst

.. verify-modules-start

Predictive ability tests
------------------------

Overview of the VERIFY module
+++++++++++++++++++++++++++++

.. |verify_fig| image:: images/VERIFY.jpg
   :width: 600

.. centered:: |verify_fig|

Input required
++++++++++++++

This module uses a GENERATE folder created in a GENERATE job.

Automated protocols
+++++++++++++++++++

*  y-mean test: Calculates the accuracy of the model when all the predicted y values are fixed to the mean of the measured y values (straight line when plotting measured vs predicted y values).  
*  y-shuffle test: Calculates the accuracy of the model after shuffling randomly all the measured y values.
*  onehot test: Calculates the accuracy of the model when replacing all descriptors for 0s and 1s. If the x value is 0, the value will be 0, otherwise it will be 1.

Technical information
+++++++++++++++++++++

The test-pass thresholds are 15% (for unclear results) and 30% (for passed tests), determined by the percentage of error difference (RMSE or MCC by default) relative to the original model.
Lastly, the VERIFY module generates a bar plot summarizing the test outcomes. This visual representation distinguishes between passed, unclear and failed tests, using blue, yellow and red colors, respectively.

Example
+++++++

An example is available in **Examples/Use of individual modules**.

.. verify-modules-end

## robert/docs/Tutorials/checkml_database.rst

Prepare a database for CheckML
==============================

Columns included
++++++++++++++++

Before using CheckML to evaluate a model, prepare a tabular database with one
row per compound or data point. Include **ONLY** the following columns:

* **Names or IDs**: one column with a unique name or identifier for each row.
* **Target (y values)**: one column with the target values.
* **Descriptors (X values)**: one column for each descriptor used by the model.

An optional **SMILES** column can be included to display molecules in
interactive graphs. It is additional to the name, target, and descriptor
columns (SMILES strings are not included as descriptors).

.. |br| raw:: html

   <br />

.. warning::
  During testing, we found that some users wanted to include additional columns 
  that were not used by the model, such as unused descriptors or predefined data splits. 
  However, these columns were sometimes inadvertently included in the evaluation 
  rather than excluded using the initially available "Ignore" option, leading to 
  misleading CheckML scores. Similarly, requiring other researchers to manually 
  exclude unused descriptors also increases the potential for reproducibility errors.
  |br| 
  For these reasons, we decided to **accept only the minimum data required to evaluate 
  a model.** This standardized format allows users to include the input CSV directly 
  in the Supporting Information alongside the CheckML PDF report.

For example:

.. csv-table::
   :header-rows: 1

   "Molecule_name", "Target_property", "descriptor_1", "descriptor_2", "...", "descriptor_n"
   "molecule_1", "1.25", "0.41", "2.7", "...", "3.2"
   "molecule_2", "0.82", "0.36", "1.9", "...", "2.5"
   "...", "...", "...", "...", "...", "..."
   "molecule_n", "0.98", "0.46", "1.7", "...", "4.1"

The column names above are illustrative and their order does not affect the results. Use
the column names expected by the model you are evaluating.

And with SMILES:

.. csv-table::
   :header-rows: 1

   "Molecule_name", "Target_property", "descriptor_1", "descriptor_2", "SMILES"
   "molecule_1", "1.25", "0.41", "2.7", "CCO"
   "molecule_2", "0.82", "0.36", "1.9", "CCN"

|br|

Data points included and user-defined data splits
+++++++++++++++++++++++++++++++++++++++++++++++++

As stated in the previous section, **do not specify data partitions in the input CSV.**

CheckML uses a standardized and systematic data-splitting strategy to evaluate models, 
rather than relying on user-defined training, validation, and test splits. This avoids 
potential inconsistencies caused by small differences in data partitioning, which 
can have a substantial impact on model evaluation, particularly for small datasets.

The input database provided to CheckML should therefore contain all data points 
used to train, validate, and test the original model. For example:

.. csv-table::
   :header-rows: 1

   "Original model split","Data points to include in CheckML"
   "80 training + 20 test","All 100 data points"
   "80 training + 20 validation + 20 test","All 120 data points"

For more information, see the :ref:`CheckML score section <robert-score-start>`.

## robert/docs/Tutorials/checkml_evaluation.rst

Perform a CheckML evaluation
============================

Step 1. Dataset
++++++++++++++++

Upload a tabular dataset containing the required columns. An error will appear 
if the dataset does not meet all criteria. In such cases, the program will provide 
a message describing the issue; alternatively, users can 
visit :doc:`checkml_database` for more details.

Step 2. Evaluation setup
++++++++++++++++++++++++

Adjust the following three options:

- **Target column:** select the column with the target values (y values)
- **Name / ID column:** select the column with the names or identifiers
- **Problem type:** select the type of problem (regression or classification)

Optionally, users can also select:

- **SMILES column:** to display molecules in interactive graphs

Step 3. Model configuration
+++++++++++++++++++++++++++

Select your model through any of the following options:

- **Multivariate linear model (MVL)**
- **Other scikit-learn models:** in the interactive table that appears, select a model from the scikit-learn library and provide its hyperparameters
- **From a hyperparameters CSV:** For a hyperparameters CSV, use columns "param,value" and include a row such as "model,RandomForestRegressor"

.. warning::
  Saved pickle/joblib uploads are disabled by default on public Spaces because 
  loading them can execute code.

Step 4. Execute CheckML
+++++++++++++++++++++++

Press the **Evaluate model** button to run the evaluation. The evaluation may take 
a few minutes depending on the dataset size and model complexity.

Step 5. Analyze and report CheckML results
++++++++++++++++++++++++++++++++++++++++++

All scores, warnings, interactive plots, and other results will be available once 
the evaluation is complete. These results can be viewed and downloaded 
from the sections at the bottom of the page (**Report & Downloads**, 
**PDF Preview Figures**, **Interactive Predictions**, etc.).

PDF reports can be downloaded from the **Report & Downloads** section. 
These reports contain all the information needed to document the evaluation 
and can be directly included in the Supporting Information of a publication, 
together with the input CSV used in CheckML.

## robert/docs/Tutorials/chemdraw.rst

.. container:: step

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='1'>

      In this tutorial we start from molecular structures created
   in **ChemDraw**.

   ChemDraw files contain only chemical structures, without
   descriptors or datasets.

   easyROB can read these structures, convert them into a dataset,
   and then use them to train a machine learning model.

   .. raw:: html

      <div class="step-nav">
         <button onclick="nextStep('chemdraw',1)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='2'>

      First, enable the **AQME Workflow** to unlock the
   **AQME** tab.

   This tab contains the tools required to process ChemDraw
   files and convert them into a dataset that can be used
   for modelling.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',2)">Previous</button>
         <button onclick="nextStep('chemdraw',2)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='3'>

      In the **AQME** tab, click
   **Generate CSV from ChemDraw files**.

   This option converts ChemDraw structures into a dataset
   that can later be used to train the model.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',3)">Previous</button>
         <button onclick="nextStep('chemdraw',3)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='4'>

      A pop-up window will appear explaining the requirements
   for ChemDraw files.

   The structures must be saved in **CDXML format**, and
   the chemical drawings should be correct, since incorrect
   structures may lead to errors when the GUI reads them.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',4)">Previous</button>
         <button onclick="nextStep('chemdraw',4)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='5'>

      Next, select the ChemDraw file containing the molecular
   structures.

   Browse to the file location and load it into the program.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',5)">Previous</button>
         <button onclick="nextStep('chemdraw',5)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='6'>

      Once the file is loaded, a table will appear containing
   the molecules extracted from the ChemDraw file.

   Two columns are displayed: **code_name** and
   **Target**.

   Assign a name to each molecule in the **code_name**
   column.

   The **Target** column should contain the property that
   will be predicted by the machine learning model.

   In this example, the target column is renamed to
   **Yield** and filled with the corresponding values.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',6)">Previous</button>
         <button onclick="nextStep('chemdraw',6)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='7'>

      After completing the information, click **Save as CSV**.

   A dialog window will appear asking you to choose the location
   and the name of the CSV file to be saved.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',7)">Previous</button>
         <button onclick="nextStep('chemdraw',7)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='8'>

      A confirmation pop-up will then appear indicating that the
   CSV file has been successfully saved and automatically
   loaded into the GUI.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',8)">Previous</button>
         <button onclick="nextStep('chemdraw',8)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='9'>

      Return to the **ROBERT** tab.

   The newly generated CSV dataset will appear automatically
   as the training input.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',9)">Previous</button>
         <button onclick="nextStep('chemdraw',9)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='10'>

      Next, configure the model parameters.

   Select the **target column** (Yield), choose the
   prediction type (**regression**), and specify the
   column containing the molecule identifiers.

   No columns need to be ignored in this example.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',10)">Previous</button>
         <button onclick="nextStep('chemdraw',10)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='11'>

      Press **Run ROBERT** to launch the workflow.

   easyROB will automatically generate molecular descriptors
   from the structures and train the machine learning model.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',11)">Previous</button>
         <button onclick="nextStep('chemdraw',11)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='12'>

      A message will appear indicating that only structural
   descriptors will be generated in this workflow.

   Atom-based descriptors can also be generated using the
   **AQME** tab, as shown in the **From CSV** tutorial.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',12)">Previous</button>
         <button onclick="nextStep('chemdraw',12)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='chemdraw' data-step='13'>

      Once the workflow finishes, a pop-up message confirms
   that the process has completed successfully.

   The **Reports** and **Images** tabs become available,
   providing access to the results generated during the
   workflow.

   These result sections are explained in more detail in the
   **Overview** tutorial.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('chemdraw',13)">Previous</button>
      </div>

   .. raw:: html

      </div>

## robert/docs/Tutorials/csv.rst

.. container:: step

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='1'>

      In this tutorial we will build a machine learning model starting
   from a simple CSV dataset.

   We will first show how to create the input CSV file containing
   the molecular structures and the target property to be predicted.

   In this example we will use **SMILES** representations so that
   molecular descriptors can be generated automatically with AQME,
   but if descriptors are already available they can be included
   directly in the CSV instead of SMILES.

   This dataset will then be used to train the machine learning
   model within the ROBERT workflow.

   .. raw:: html

      <div class="step-nav">
         <button onclick="nextStep('csv',1)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='2'>

      Open a new spreadsheet in Microsoft Excel. 
   Any spreadsheet software can be used to create or edit CSV files.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',2)">Previous</button>
         <button onclick="nextStep('csv',2)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='3'>

      In this example we will create a dataset containing three columns:
   **code_name** (unique identifiers for each molecule), 
   **target** (the property that the machine learning model will 
   learn to predict), and **SMILES** (the molecular structures).

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',3)">Previous</button>
         <button onclick="nextStep('csv',3)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='4'>

      The **SMILES strings** can be obtained in several ways.

   For example, they can be copied from molecular drawing software
   such as **ChemDraw**, or retrieved from online chemical
   databases that provide both the structure and the corresponding
   SMILES string.

   In this tutorial we will copy the SMILES directly from ChemDraw,
   as shown in the image.

   Select the structure and go to **Edit → Copy As → SMILES**.
   You can also use the shortcut **Ctrl + Alt + C**.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',4)">Previous</button>
         <button onclick="nextStep('csv',4)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='5'>

      Once the dataset is complete and all molecular structures have
   been added as SMILES, the file must be saved as a CSV file.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',5)">Previous</button>
         <button onclick="nextStep('csv',5)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='6'>

      Go to the **File** tab and select **Save As**. 
   Choose **CSV** under the **Save as type** dropdown menu,
   provide a name for the dataset, and click **Save**.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',6)">Previous</button>
         <button onclick="nextStep('csv',6)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='7'>

      The first step in the workflow is loading the input dataset.

   Select the **training CSV file** that will be used to build
   the machine learning model.

   Optionally, an **external test dataset** can also be provided.
   If included, ROBERT will generate predictions for these
   molecules after the model has been trained.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',7)">Previous</button>
         <button onclick="nextStep('csv',7)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='8'>

      Next, configure the basic model parameters.

   Select the **target column**, choose the prediction type

   (in this example **regression**), and specify the column

   containing the molecule identifiers.

   No columns need to be excluded in this case, since the

   SMILES column is handled automatically.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',8)">Previous</button>
         <button onclick="nextStep('csv',8)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='9'>

      Enable the **AQME Workflow** to generate molecular

   descriptors from the SMILES structures.

   Once this option is activated, the **AQME** tab becomes

   available and can be used to adjust descriptor generation

   settings.

   **Note:** If the input CSV already contains molecular

   descriptors, this step can be skipped and the workflow can

   be run directly.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',9)">Previous</button>
         <button onclick="nextStep('csv',9)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='10'>

      In the **AQME** tab, the interface may detect a common

   molecular scaffold across the dataset.

   In this example, the molecules share a carboxylic acid

   functional group, which is displayed in the structure viewer.

   Atoms from this structure can be selected to generate

   additional atom-based descriptors.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',10)">Previous</button>
         <button onclick="nextStep('csv',10)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='11'>

      Here, two atoms from the carboxylic acid group have been

   selected: the carbonyl oxygen and the hydroxyl oxygen.

   These selections will be used during descriptor generation.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',11)">Previous</button>
         <button onclick="nextStep('csv',11)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='12'>

      Once the configuration is complete, return to the

   **ROBERT** tab and press **Run ROBERT** to launch

   the workflow.

   The program will automatically generate descriptors,

   train the machine learning models, and produce the results.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',12)">Previous</button>
         <button onclick="nextStep('csv',12)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='13'>

      After the workflow finishes, a message will indicate that

   the process has completed successfully.

   You can then choose to open the generated report to

   inspect the results.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',13)">Previous</button>
         <button onclick="nextStep('csv',13)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='csv' data-step='14'>

      The report summarizes the machine learning results, including

   model performance metrics and validation information.

   Once the workflow has generated results, the **Reports**,

   **Images**, and **Predictions** tabs become available.

   The **Reports** tab displays the PDF summary of the modelling

   results, the **Images** tab provides access to the figures

   generated during the workflow, and the **Predictions** tab

   shows the predicted values for the external test dataset used

   in this example.

   These result sections are described in more detail in the

   **Overview** tutorial.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('csv',14)">Previous</button>
      </div>

   .. raw:: html

      </div>

## robert/docs/Tutorials/descriptors.rst

.. container:: step

   .. raw:: html

      <div class='step-content' data-prefix='descriptors' data-step='1'>

      This tutorial shows how to generate molecular descriptors
   using the **AQME** workflow.

   Descriptor generation can be useful when preparing datasets
   for machine learning models or when molecular descriptors
   are required for other types of analysis.

   .. raw:: html

      <div class="step-nav">
         <button onclick="nextStep('descriptors',1)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='descriptors' data-step='2'>

      Load a **CSV file** containing the molecules for which
   descriptors should be generated.

   The dataset must contain a **SMILES column**, which
   AQME will use to compute the molecular descriptors.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('descriptors',2)">Previous</button>
         <button onclick="nextStep('descriptors',2)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='descriptors' data-step='3'>

      Press **Run AQME** to start the descriptor generation
   workflow.

   AQME will automatically generate three descriptor datasets:
   **denovo**, **interpret**, and **full**.

   These files contain increasing numbers of descriptors,
   ranging from smaller and more interpretable sets to the
   complete descriptor collection.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('descriptors',3)">Previous</button>
         <button onclick="nextStep('descriptors',3)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='descriptors' data-step='4'>

      A pop-up window will indicate that only **molecular
   descriptors** will be generated in this workflow.

   Atomic descriptors can also be generated using the
   **AQME** tab. An example of this workflow is shown
   in the **From CSV** tutorial.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('descriptors',4)">Previous</button>
         <button onclick="nextStep('descriptors',4)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='descriptors' data-step='5'>

      Once the process finishes, a message will indicate that
   the descriptor datasets have been generated successfully.

   The three CSV files (**denovo**, **interpret**, and
   **full**) will be saved in the working directory.

   These descriptor datasets can be used directly for further
   analysis or loaded into the **ROBERT** workflow to
   build machine learning models.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('descriptors',5)">Previous</button>
         <button onclick="nextStep('descriptors',5)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='descriptors' data-step='6'>

      In this example, the **interpret** dataset is loaded,
   but any of the generated descriptor sets can be used
   depending on your needs.

   At this stage, the descriptors can be inspected, filtered,
   or modified before building a machine learning model.

   If you want to train a predictive model using these descriptors,
   the dataset must contain a **target column** with the property
   you want to predict.

   If the original CSV did not include a target value, it can be
   added later before running the **ROBERT** workflow.

   Alternatively, the generated descriptor datasets can also be
   used independently of ROBERT for other analyses or workflows.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('descriptors',6)">Previous</button>
      </div>

   .. raw:: html

      </div>

## robert/docs/Tutorials/overview.rst

.. container:: step

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='1'>

      Welcome to the **easyROB graphical interface**. easyROB integrates two complementary engines
   designed for computational chemistry workflows:

   • **AQME** — generates molecular descriptors from molecular structures

   • **ROBERT** — builds and evaluates machine learning models

   Together, these tools allow users to move from raw molecular structures to predictive models within
   a single interface. This overview briefly introduces the main sections of the GUI before moving to
   the practical tutorials.

   .. raw:: html

      <div class="step-nav">
         <button onclick="nextStep('overview',1)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='2'>

      When easyROB starts, the interface opens in the **ROBERT tab**. This tab contains the main controls
   used to:

   • Load datasets

   • Configure machine learning workflows

   • Train predictive models

   Most users will perform the majority of their work in this section.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',2)">Previous</button>
         <button onclick="nextStep('overview',2)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='3'>

      The first step is loading a **dataset**. To train a machine learning model, the dataset must contain
   **molecular descriptors**, which are numerical features describing each molecule. Two scenarios are
   possible:

   • If your CSV file already contains descriptors, they will be used directly to train the model.

   • If the dataset only contains a **SMILES column**, descriptors can be generated automatically using
      the **AQME workflow**.

   This descriptor generation process will be explained later in the tutorial. Optionally, you may also
   provide a separate **test CSV file** to evaluate predictions on an external dataset.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',3)">Previous</button>
         <button onclick="nextStep('overview',3)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='4'>

      This section defines the **model configuration**. First, select the **Target value**. The target is
   the property that the machine learning model will learn from the dataset and later attempt to
   predict for new molecules. Next, choose the **prediction type**, such as:

   • **Regression** for continuous values

   • **Classification** for categorical outcomes

   In addition, you must provide a column containing **unique identifiers** for each row in the
   dataset. These identifiers allow easyROB to correctly track molecules and report predictions in a
   clear and reproducible way.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',4)">Previous</button>
         <button onclick="nextStep('overview',4)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='5'>

      Some dataset columns may contain information that should not be used to build the model. These
   columns can be **excluded** here. Typical examples include metadata columns, comments, or
   experimental annotations that are not meaningful descriptors. **Important:** The columns selected as
   **Target value**, **Name column**, and the **SMILES column** are automatically handled by easyROB
   and do not need to be excluded manually.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',5)">Previous</button>
         <button onclick="nextStep('overview',5)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='6'>

      Enabling the **AQME workflow** allows easyROB to generate molecular descriptors directly from SMILES
   structures. When this option is activated, the **AQME tab** becomes available in the interface. This
   tab provides advanced options for descriptor generation and molecular processing. These settings are
   optional and will be explained in detail later in this tutorial.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',6)">Previous</button>
         <button onclick="nextStep('overview',6)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='7'>

      The ROBERT machine learning pipeline can be executed automatically using the **Full Workflow**
   option. This option is **enabled by default**, so in most cases you do not need to modify anything
   before running the workflow. Alternatively, advanced users can run individual stages of the pipeline
   separately:

   **CURATE → GENERATE → PREDICT → VERIFY → REPORT**

   Running steps individually can be useful for debugging or for inspecting intermediate results.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',7)">Previous</button>
         <button onclick="nextStep('overview',7)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='8'>

      Press the **ROBERT** button to launch the automated machine learning workflow. This will execute the
   selected stages of the ROBERT pipeline using the dataset and configuration provided. Alternatively,
   the **AQME** button can be used independently to generate molecular descriptors before training a
   model. The **Stop** button allows interrupting the workflow at any moment if necessary.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',8)">Previous</button>
         <button onclick="nextStep('overview',8)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='9'>

      The **console panel** displays log messages and progress information generated during execution.
   This output helps track which steps are running and identify potential warnings or errors.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',9)">Previous</button>
         <button onclick="nextStep('overview',9)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='10'>

      When the **Enable AQME Workflow** option is activated, the **AQME tab** becomes available in the
   interface. If a dataset containing a **SMILES column** has already been loaded, easyROB will
   automatically generate molecular descriptors when the workflow is executed. The AQME tab provides
   **advanced options** for users who want more control over the descriptor generation process. For
   example, if your molecules share a common structure, the interface can display the molecular
   scaffold and allow you to **select specific atoms** to generate atom-based descriptors. You can also
   configure additional **AQME descriptor parameters**. A documentation button is available to access
   detailed information about these options. This tab is also used when starting from **ChemDraw
   outputs**. In this case, the ChemDraw file can be loaded here to extract the relevant information
   and generate a CSV dataset that can then be used in the AQME and ROBERT workflows.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',10)">Previous</button>
         <button onclick="nextStep('overview',10)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='11'>

      The **Advanced Options** tab provides additional controls for the ROBERT machine learning workflow.
   This section allows advanced users to modify specific parameters used during different stages of the
   pipeline, including:

   • **GENERAL** – parameters affecting the overall workflow

   • **CURATE** – dataset preparation and preprocessing

   • **GENERATE** – model training and descriptor selection

   • **PREDICT** – prediction settings

   These options are intended for users who want more control over the modelling process. In most
   cases, the default settings are sufficient to run the workflow successfully. Help buttons are
   available throughout this tab to access the documentation and obtain detailed explanations of each
   parameter.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',11)">Previous</button>
         <button onclick="nextStep('overview',11)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='12'>

      The **MolSSI Databases** tab provides access to molecular libraries developed through the
   **Descriptor Libraries** project, a collaborative initiative between the Molecular Sciences Software
   Institute (MolSSI) and the Center for Computer Assisted Synthesis (C-CAS). These libraries contain
   curated collections of molecules organised by functional group, such as carboxylic acids, amines,
   sulfonamides, and many others. Users can explore these datasets directly within the interface,
   inspect the available molecules, and download the corresponding libraries for further analysis. The
   downloaded datasets already include molecular descriptors as well as machine learning predictions
   generated within the Descriptor Libraries project, allowing them to be used directly in modelling
   workflows.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',12)">Previous</button>
         <button onclick="nextStep('overview',12)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='13'>

      The **Reports**, **Images**, and **Predictions** tabs remain disabled until the ROBERT workflow has
   been executed and results have been generated. Once the workflow finishes, these tabs become
   available and allow users to explore the different outputs produced during the machine learning
   process. Each tab focuses on a different type of result: reports summarizing model performance,
   images generated during the workflow, and predictions obtained for external datasets. **Note:** The
   **Predictions** tab is only available if an external test dataset was provided before running the
   workflow.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',13)">Previous</button>
         <button onclick="nextStep('overview',13)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='14'>

      The **Reports** tab displays the PDF report automatically generated by the ROBERT workflow. This
   report provides a complete summary of the machine learning process, including the selected model,
   performance metrics, identified outliers, boundary robustness analysis, and statistical validation
   tests. The report helps users evaluate whether the generated model is robust and reliable for making
   predictions.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',14)">Previous</button>
         <button onclick="nextStep('overview',14)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='15'>

      The **Images** tab provides access to all figures generated during the ROBERT workflow. These images
   are organised into sections corresponding to the different stages of the pipeline, including
   **CURATE**, **GENERATE**, **VERIFY**, and **PREDICT**. Users can browse these figures directly in
   the interface. By right-clicking on an image, it can be copied, saved to a file, opened in full
   size, or the folder containing the image can be opened.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',15)">Previous</button>
         <button onclick="nextStep('overview',15)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='overview' data-step='16'>

      The **Predictions** tab displays the prediction results generated for an external test dataset, if
   one was provided. The results are organised into two sub-tabs: **PFI** and **no PFI**. ROBERT
   automatically builds two models: one applying a descriptor reduction step (**PFI**) and another
   without this reduction. Each tab shows the predictions generated by one of these models. For each
   molecule in the test dataset, the table displays the predicted value together with the associated
   standard deviation. The table also provides several interactive options. By right-clicking on the
   prediction columns, users can sort the values or generate simple plots such as histograms to quickly
   explore the distribution of the predicted results.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('overview',16)">Previous</button>
      </div>

   .. raw:: html

      </div>

## robert/docs/Tutorials/predictions.rst

.. container:: step

   .. raw:: html

      <div class='step-content' data-prefix='predictions' data-step='1'>

      This workflow is used when you already have a trained ROBERT model
   and want to generate predictions for new candidate molecules.

   For example, you may have trained a model previously and now want
   to evaluate new structures using that model.

   .. raw:: html

      <div class="step-nav">
         <button onclick="nextStep('predictions',1)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='predictions' data-step='2'>

      To run predictions, provide a **CSV file** containing the molecules
   for which predictions should be calculated.

   The CSV file must be placed in the same directory where the ROBERT
   model was generated, as shown in the example. This allows the workflow
   to automatically detect the model and use it to generate predictions.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('predictions',2)">Previous</button>
         <button onclick="nextStep('predictions',2)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='predictions' data-step='3'>

      Select the **Test CSV** file in the interface to load the
   molecules for prediction.

   This dataset must contain the information required by the
   trained model.

   If descriptors were originally generated using AQME, the
   CSV should contain an **ID column** and a **SMILES
   column** so descriptors can be generated automatically.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('predictions',3)">Previous</button>
         <button onclick="nextStep('predictions',3)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='predictions' data-step='4'>

      Since the model has already been trained, only the
   **PREDICT** step needs to be executed.

   Select the **PREDICT** option in the workflow
   configuration.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('predictions',4)">Previous</button>
         <button onclick="nextStep('predictions',4)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='predictions' data-step='5'>

      Once the test dataset is loaded and the **PREDICT**
   option is selected, press **Run ROBERT** to start
   the prediction workflow.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('predictions',5)">Previous</button>
         <button onclick="nextStep('predictions',5)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='predictions' data-step='6'>

      A pop-up window will ask how the descriptors should be handled
   for the prediction workflow.

   If the original model was built using **AQME**, the GUI can
   generate the descriptors again automatically from the SMILES
   structures.

   If the model was trained using **custom descriptors**, then
   the test CSV must already contain the same descriptors that
   were used when training the model.

   In this tutorial we use the **AQME** option, but you should
   select the option that matches how your model was originally
   trained.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('predictions',6)">Previous</button>
         <button onclick="nextStep('predictions',6)">Next</button>
      </div>

   .. raw:: html

      </div>

   .. raw:: html

      <div class='step-content' data-prefix='predictions' data-step='7'>

      Once the process finishes successfully, a confirmation
   message will appear.

   The **Predictions** tab will become available, where
   the generated prediction results can be inspected.

   More details about this results tab are explained in the
   **Overview** tutorial.

   .. raw:: html

      <div class="step-nav">
         <button onclick="prevStep('predictions',7)">Previous</button>
      </div>

   .. raw:: html

      </div>

## robert/docs/Tutorials/tutorials.rst

=======================
easyROB Tutorial Guides
=======================

These tutorials guide you step-by-step through the **easyROB graphical interface**.

You will learn how to:

- Build models from CSV datasets  
- Generate descriptors  
- Process ChemDraw files  
- Run predictions  

-----

Select a tutorial workflow:

Each tutorial is a step-by-step interactive guide.  
Use the controls at the bottom to navigate through the different stages of the workflow.

.. tab-set::

   .. tab-item:: Overview

      .. include:: overview.rst

   .. tab-item:: From CSV

      .. include:: csv.rst

   .. tab-item:: From ChemDraw

      .. include:: chemdraw.rst

   .. tab-item:: Generate Descriptors

      .. include:: descriptors.rst

   .. tab-item:: Predictions

      .. include:: predictions.rst

## robert/docs/Tutorials/videos.rst

===============
Video Tutorials
===============

ROBERT (Command Line Interface)
===============================

This section contains tutorials showing how to use **ROBERT** from the command line.

.. |robert 1| image:: https://i3.ytimg.com/vi/-oSQyMoGUow/maxresdefault.jpg
   :alt: ROBERT examples: Full workflow from CSV
   :width: 400
   :target: https://www.youtube.com/watch?v=-oSQyMoGUow&t=2s

Full workflow from CSV
----------------------
|robert 1|

EasyROB (Graphical User Interface)
==================================

A series of short tutorials showing how to install and use **easyROB** — no coding required.

.. |easyrob 1| image:: https://i3.ytimg.com/vi/yIMCCJF0Kl0/hqdefault.jpg
   :alt: EasyROB at-a-glance in 1 min
   :width: 400
   :target: https://www.youtube.com/watch?v=yIMCCJF0Kl0&t=2s

.. |easyrob 2| image:: https://i3.ytimg.com/vi/Dl-8owb3RRQ/hqdefault.jpg
   :alt: EasyROB Installation — ready to use in seconds
   :width: 400
   :target: https://www.youtube.com/watch?v=Dl-8owb3RRQ&t=2s

.. |easyrob 3| image:: https://i3.ytimg.com/vi/-pLzXzFKFq8/hqdefault.jpg
   :alt: EasyROB Tutorial 1 — Full workflow from CSV
   :width: 400
   :target: https://www.youtube.com/watch?v=-pLzXzFKFq8&t=2s

.. |easyrob 4| image:: https://i3.ytimg.com/vi/VkDy-ssoaow/hqdefault.jpg
   :alt: EasyROB Tutorial 2 — From ChemDraw to automated predictions
   :width: 400
   :target: https://www.youtube.com/watch?v=VkDy-ssoaow&t=2s

easyROB at-a-glance in 1 min
-----------------------------
|easyrob 1|

Installation — ready to use in seconds
--------------------------------------
|easyrob 2|

Full workflow from CSV
----------------------
|easyrob 3|

Full workflow from ChemDraw 
---------------------------
|easyrob 4|

## robert/docs/Report/repro.rst

.. robert-repro-start

Reproducibility and Transparency
--------------------------------

Overview
++++++++

ROBERT aims to improve the reproducibility and transparency of chemical machine learning protocols, addressing two long-standing concerns within the scientific community when publishing in peer-reviewed journals. Several authors have emphasized the critical necessity of establishing and enforcing standards in this regard since a significant proportion of publications are challenging or even impossible to replicate (see references below).

The generated ROBERT_report.pdf files include a **reproducibility section** that instructs authors on which files they should upload as supporting information. This section also provides other researchers with the precise programs, versions, and commands required to replicate the results. Additionally, there is a **transparency section** containing comprehensive information about the machine learning models used and other relevant details regarding ROBERT protocols.

* `Best practices in ML for chemistry <https://www.nature.com/articles/s41557-021-00716-z>`__
* `Artificial intelligence faces reproducibility crisis <https://www.science.org/doi/10.1126/science.359.6377.725>`__

Reproducibility section
+++++++++++++++++++++++

This is a screenshot of the reproducibility section shown in the PDF report.

.. |repro_fig| image:: images/repro.jpg
   :width: 600

|repro_fig|

Transparency section
++++++++++++++++++++

This is a screenshot of the transparency section shown in the PDF report.

.. |trans_fig| image:: images/trans.jpg
   :width: 600

|trans_fig|

.. robert-repro-end

## robert/docs/Report/score.rst

.. _robert-score-start:

CheckML score
-------------

Overview
++++++++

.. |br| raw:: html

   <br />

.. |u| raw:: html

   <u>

.. |/u| raw:: html

   </u>

.. |space| raw:: html

   &nbsp;

**How should we assess whether a published ML model is sufficiently robust, reliable, and applicable
to the chemical problem it is intended to address?**

In practice, model quality is often communicated
through a small number of statistical metrics (ie R2, RMSE, MCC, etc.). Although these metrics are useful, 
they provide only a partial view of model reliability, making it difficult 
for readers and reviewers to assess the robustness and domain of applicability of the reported models. 

To this end, we have developed CheckML, a set of tools that systematically analyze descriptor-based tabular 
ML models, evaluates multiple aspects of their performance, and provides quality scores and diagnostic 
alerts associated with potential weaknesses. The framework examines predictive performance, 
overfitting, generalization, prediction stability, and behavior at the boundaries of the modeled chemical space 
(related to extrapolation). These analyses are compiled into standardized PDF reports that document the evaluation 
and highlight aspects requiring further consideration.

|br|

.. note:: 

   Please note that the CheckML score was developed based on the following:
   
   * Established recommendations for robust ML
   * Experience with chemical ML models across a broad community of expert chemists
   * A comprehensive benchmarking process
   
   **We are completely open to discuss any advice on how to improve the thresholds used in the score or make the score more robust!**

Please, see the CheckML publication for more details.

|br|

Protocols followed by CheckML
+++++++++++++++++++++++++++++

Before evaluation, CheckML applies a standardized splitting procedure. The random seed is fixed, and rows 
and columns are sorted so that the results are independent of the order in which data are provided. 80% of 
the data are used for cross-validation (CV), while the remaining 20% (or a minimum of four data points) 
are reserved as an independent test set. 

CheckML uses 10-times repreated 5-fold CV (10x 5-fold CV) because this type of CV 
is widely used in the ML community and is the default repeated CV strategy recommended
by scikit-learn. Benchmarking across low-data regimes also showed that 10x 5-fold CV 
remains informative across a broad range of dataset sizes (16–4200 data points, 
see the CheckML publication). 

.. note::
  Although leave-one-out CV (LOOCV) is sometimes used for low-data chemical problems,
  each validation estimate is based on a single observation and the resulting 
  estimates can be highly correlated. Thus, 10x 5-fold CV provides a more informative 
  validation framework for the intended application of CheckML.

.. note::
  A potential concern during development of the scoring system was whether reserving 
  20% of the data as an independent test set, in addition to the CV set, 
  could adversely affect model performance in the low-data regime. The overall 
  effect was small (MAE in 10x 5-fold CV scaled RMSE = 1.3% across 14 exampes, 
  see the CheckML publication). Based on these results, we retained the 20% test-set
  holdout for all datasets. This provides a more informative assessment of overfitting
  and generalization while having only a minor effect on the resulting score, 
  even in the low-data regime.

After this initial splitting, different ROBERT routines are applied to evaluate the 
model as explained in the following sections.

|br|

How is the score calculated?
++++++++++++++++++++++++++++

The numerical thresholds used to assign points across the different sections were calibrated using 112 
representative models. Their suitability was further assessed based on the diverse perspectives of the 
chemical ML community represented among the co-authors of the CheckML manuscript.

Importantly, the resulting scores should not be interpreted as replacements for the underlying statistical 
metrics or as universal guarantees of predictive validity. Rather, they provide a standardized, quantitative 
quality-control layer that integrates multiple diagnostics. By explicitly testing performance against 
flawed baselines, evaluating overfitting and generalization, 
quantifying prediction stability, and probing both response- and descriptor-space boundaries, CheckML provides 
a systematic assessment of the conditions under which a model's predictions can reasonably be considered 
reliable. 

.. warning:: 
   In this context, a published model may still be useful for its intended application even when weak scores or 
   warnings are obtained. For example, a model may receive a poor extrapolatin score, but it could still be 
   useful if it is intended to cover only a well-defined region of the data space. Therefore, a low score should 
   not necessarily be interpreted as evidence that a model is unusable; rather, it should prompt the authors to 
   assess whether the identified limitation is relevant to the intended application and to provide an 
   appropriate justification within the corresponding manuscript.

|br|

Interpolation (0 to 10)
^^^^^^^^^^^^^^^^^^^^^^^

**How reliably the model predicts within the range of data it was trained on.**

**Section B.1. Model vs "flawed" models (from -8 to 0 points for regression, -6 to 0 for
classification):**

The tests conducted within the VERIFY module are regarded as score indicators:

*  y-mean test: Calculates the accuracy of the model when all the predicted y values are fixed to the mean of the measured y values (straight line when plotting measured vs predicted y values).
*  y-shuffle test: Calculates the accuracy of the model after shuffling randomly all the measured y values.
*  onehot test: Calculates the accuracy of the model when replacing all descriptors for 0s and 1s. Continuous descriptors are binarized using their own median as the cutoff (value ≥ median → 1, otherwise → 0), while descriptors that are already binary are left untouched.
*  cluster test (regression only): Calculates the accuracy of a trivial baseline that splits the descriptors (X) into two groups with k-means and predicts each point using its own group's average y value. This flags datasets that are really just two separated point clouds, where a model can look deceptively good while only having learned "which group is this point in." This baseline's own prediction (a cluster's mean y) isn't a valid class label, so it doesn't carry over to classification as-is - it's shown as N/A there instead of being scored.

The y-mean and y-shuffle tests are valuable in identifying overfitted and underfitted models.
The one-hot test identifies models that are insensitive to specific values but instead focus
on the presence of such values (i.e., reaction datasets filled with 0s where compounds are not used).
The cluster test identifies models that succeed only by exploiting a coarse split in descriptor space
rather than a genuine structure-property relationship.

============== ========================================================
Points         Condition
============== ========================================================
-••  -2         Each of the VERIFY tests failed
-• -1           Each of the unclear VERIFY tests
0               Each of the VERIFY tests passed (4 for regression, 3 for classification)
============== ========================================================

The following examples might help clarify these points:

|br|

**Section B.2. CV predictions of the model (2 points):**

In regression, two metrics (RMSE and R\ :sup:`2`) are used to ensure a more robust assessment, as a model may show low R\ :sup:`2` while maintaining an acceptable RMSE. In classification, points are assigned based on the MCC, on the same 0-2 scale as regression.

============ =======================================================
Points       Scaled RMSE
============ =======================================================
|br|         **Regression**
•• 2         ≤ 10% (high predictive ability)
•\ |space| 1 ≤ 20% (moderate predictive ability)
0            > 20% (low predictive ability)
|br|         **Classification**
•• 2         MCC > 0.60 (high predictive ability)
•\ |space| 1 0.60 ≥ MCC ≥ 0.30 (moderate predictive ability)
0            MCC < 0.30 (low predictive ability)
============ =======================================================

============ =======================================================
Points        R\ :sup:`2` (penalty)
============ =======================================================
|br|         **Regression**
-•• -2          R\ :sup:`2` < 0.5
-• -1           R\ :sup:`2` < 0.7
0               R\ :sup:`2` >= 0.70
============ =======================================================

|br|

**Section B.3. Test set, generalization and stability (up to 8 points for both regression and classification):**

All the tests from this section use a combined dataset with training and validation sets. B.3a-B.3d all apply
to both prediction types, using an MCC-based definition for classification wherever regression would
otherwise use RMSE/y-range.

|u| Section B.3a. Predictions test set (2 points) |/u|

In regression, two metrics (RMSE and R\ :sup:`2`) are used to ensure a more robust assessment, as a model may show low R\ :sup:`2` while maintaining an acceptable RMSE. In classification, points are assigned based on the MCC, on the same 0-2 scale as regression.

============ =======================================================
Points       Scaled RMSE
============ =======================================================
|br|         **Regression**
•• 2         ≤ 10% (high predictive ability)
•\ |space| 1 ≤ 20% (moderate predictive ability)
0            > 20% (low predictive ability)
|br|         **Classification**
•• 2         MCC > 0.60 (high predictive ability)
•\ |space| 1 0.60 ≥ MCC ≥ 0.30 (moderate predictive ability)
0            MCC < 0.30 (low predictive ability)
============ =======================================================

============ =======================================================
Points        R\ :sup:`2` (penalty)
============ =======================================================
|br|         **Regression**
-•• -2          R\ :sup:`2` < 0.5
-• -1           R\ :sup:`2` < 0.7
0               R\ :sup:`2` >= 0.70
============ =======================================================

|u| Section B.3b. Train vs validation gap (2 points) |/u|

**Regression**

Compares the out-of-fold validation RMSE with the in-fold training RMSE, both averaged over all the folds
and repeats of the CV, to catch a model that fits its training data much better than it generalizes to
held-out points — a classic sign of overfitting that the CV-average metrics in B.2 can otherwise hide.

============== ======================================================
Points         Scaled RMSE ratio
============== ======================================================
•• 2            Validation RMSE ≤ 1.25*train RMSE
•\ |space| 1    Validation RMSE ≤ 1.50*train RMSE
0               Validation RMSE > 1.50*train RMSE
============== ======================================================

**Classification**

Same idea, expressed as a ΔMCC instead of an RMSE ratio (a discrete label has no RMSE): compares the
in-fold training MCC against the out-of-fold CV MCC from Section B.2, using the same ΔMCC thresholds as
B.3c below.

============ ==============================================
Points       Condition
============ ==============================================
•• 2         MCC difference (ΔMCC) < 0.15 (low overfitting)
•\ |space| 1 0.15 ≤ ΔMCC ≤ 0.30 (moderate overfitting)
0            ΔMCC > 0.30 (high overfitting)
============ ==============================================

|u| Section B.3c. CV vs test consistency (2 points, or MCC difference for classification) |/u|

**Regression**

Differences in scaled RMSE between CV predictions of the model and Predictions test set.

============== ================================
Points         Scaled RMSE ratio
============== ================================
•• 2            Scaled RMSE (test) ≤ 1.25*scaled RMSE (CV)
•\ |space| 1    Scaled RMSE (test) ≤ 1.50*scaled RMSE (CV)
0               Scaled RMSE (test) >1.50*scaled RMSE (CV)
============== ================================

**Classification**

Calculates the model's uncertainty by comparing the MCC obtained from the model with the MCC of the CV from Section 3a.

============ ==============================================
Points       Condition
============ ==============================================
•• 2         MCC difference (ΔMCC) < 0.15 (low uncertainty)
•\ |space| 1 0.15 ≤ ΔMCC ≤ 0.30 (moderate uncertainty)
0            ΔMCC > 0.30 (high uncertainty)
============ ==============================================

|u| Section B.3d. Prediction stability (2 points) |/u|

**Regression**

The model's uncertainty is estimated from the 10 repetitions of the 10x 5-fold CV, combining three facets
of stability into one averaged, rounded score:

*  **(a) Test-set stability:** SD of the repeated-CV predictions on the test set, ×4 to approximate a 95% CI, as a percentage of the y range.
*  **(b) Train/validation stability:** the same SD-based check, computed instead on the out-of-fold train+validation predictions.
*  **(c) RMSE stability:** the coefficient of variation (SD / mean) of the aggregate RMSE across the 10 CV repeats.

============ ======================================================================
Points       Condition — facets (a) and (b)
============ ======================================================================
•• 2         95% CI (or 4*SD) spans less than 25% of the y range (low uncertainty)
•\ |space| 1 95% CI spans between 25% and 50% of the y range (moderate uncertainty)
0            95% CI spans more than 50% of the y range (high uncertainty)
============ ======================================================================

============ ======================================================================
Points       Condition — facet (c)
============ ======================================================================
•• 2         RMSE coefficient of variation ≤ 15%
•\ |space| 1 RMSE coefficient of variation ≤ 25%
0            RMSE coefficient of variation > 25%
============ ======================================================================

The final score for this item is the average of (a), (b) and (c), rounded to the nearest point.

*Real (a) test-set and (b) train/validation SD plots from an actual ROBERT v2.2.0 report — facet (c),*
*RMSE coefficient of variation, is a single number and isn't plotted.*

The examples below illustrate facet (a), the test-set stability check, in more detail:

**Classification**

The same three facets, adapted for a discrete label instead of a continuous one — computed from the same
repeated-CV predictions, using the majority-voted class already reported in Section B.2/B.3a:

*  **(a) Test-set stability:** disagreement rate between individual CV repeats and the majority-voted class, on the test set.
*  **(b) Train/validation stability:** the same disagreement-rate check, computed on the out-of-fold train+validation predictions.
*  **(c) MCC stability:** the coefficient of variation of the MCC computed separately for each of the 10 CV repeats.

============ ======================================================================
Points       Condition — facets (a), (b) and (c)
============ ======================================================================
•• 2         ≤ 15% (low uncertainty)
•\ |space| 1 ≤ 25% (moderate uncertainty)
0            > 25% (high uncertainty)
============ ======================================================================

The final score is the average of (a), (b) and (c), rounded to the nearest point — the same combination
rule as regression, reusing regression facet (c)'s 15%/25% thresholds directly for all three, since all
three are now plain percentages rather than a percentage of the y-range.

|br|

Boundary robustness (0 to 10 for regression only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**How well the model holds up at the edges of y ranges and on the most descriptor-wise unusual points (related to extrapolation).**

Not defined for classification: none of the sub-metrics below have a well-defined discrete-label
equivalent yet, so classification reports show only the Interpolation score (see `Score ranges`_ below).

For regression, ROBERT sorts the dataset by its target value and runs **two independent 80/20 splits**
of it — not one three-way split. The "Low" split holds out the bottom 20% of points as its test fold and
trains on the remaining top 80%; the "High" split holds out the top 20% and trains on the remaining
bottom 80%. Each split is evaluated with its own 10x 5-fold CV over its own 80% training portion, so
a point in the top 80% of one split can be in the held-out 20% of the other. Four of the five sub-metrics
below come from these two extreme folds; the fifth uses a different, X-descriptor space definition of
"boundary" instead.

*Not statistical outliers — simply the most extreme 20% of real values in the dataset. Sub-metrics 1-4*
*below all follow this Low/High fold pattern; sub-metric 5 breaks it on purpose (see* |u| 5. Applicability domain (leverage) |/u| *below).*

|u| 1-2. Low / High — scaled RMSE (2 points each) |/u|

============== ================================
Points         Scaled RMSE (Low or High fold)
============== ================================
•• 2            ≤ 10%
•\ |space| 1    ≤ 20%
0               > 20%
============== ================================

Each of these two items also carries a **crossing-rate penalty**, based on the fraction of Low/High
predictions that actually extrapolate past the training range instead of being clipped back into it
(a model that never truly leaves the training range at the boundary is not really being tested there):

============== ================================================
Penalty        Crossing rate (Low or High fold)
============== ================================================
-•• -2          < 20% cross the boundary
-• -1           < 50% cross the boundary
0               ≥ 50% of predictions cross the training boundary
============== ================================================

*Same four extreme points, two different model behaviors. "Crossing" is the fraction of Low/High*
*predictions that actually land beyond the training range rather than clipping to it — logged in the*
*PDF as* ``Beyond training range (Low/High)``. *Tree-based models (RF, GB) tend to score poorly here: a*
*decision tree's prediction is always the average of some training leaf, so it structurally cannot*
*predict a value outside the range it was trained on.*

The RMSE score and the crossing penalty are combined and floored at 0, so this item can never go negative.

*Real Low/High fold scatter plots from an actual ROBERT v2.2.0 report — this is what Section B of the*
*PDF actually shows for sub-metrics 1-2.*

|u| 3. Spearman rank (2 points) |/u|

Spearman rank correlation between measured and predicted y values, computed separately within each
extreme fold, to check that the model still ranks points correctly even where it can't hit them exactly.
A model can be systematically biased at the edges (consistently predicting a bit high or low) and still
be useful if it correctly tells you which of two extreme points is more extreme than the other — getting
the order wrong is a worse sign than getting the scale wrong.

*Parallel lines mean the model's predicted order matches the true order; crossings mean it doesn't.*

============== ================================
Points         Spearman (Low or High fold)
============== ================================
•\ |space| 1    ≥ 0.5
0               < 0.5
============== ================================

|u| 4. Degradation ratio (2 points) |/u|

Compares each extreme fold's scaled RMSE against the RMSE of the *remaining* 80% of the data, so a
model can't hide a badly-degraded boundary behind a fine-looking interior.

*Reported in the PDF as e.g.* ``Degradation vs 80% RMSE: High 1.65x, Low 1.61x`` *— both sides scored*
*independently against the same 1.5x line, so one badly-degraded side can't hide behind a fine one.*

============== ================================
Points         RMSE vs remaining 80% (Low or High fold)
============== ================================
•\ |space| 1    ≤ 1.5x
0               > 1.5x
============== ================================

|u| 5. Applicability domain (leverage) (2 points) |/u|

Unlike items 1-4, this metric measures robustness in **X-descriptor space** rather than y-space: ROBERT
trains on the 80% "typical" points and tests on the 20% highest-leverage points, using the classical QSAR
statistical leverage (the diagonal of the hat matrix, :math:`h_i = x_i^T (X_{train}^T X_{train})^{-1} x_i`)
to identify which points are the most structurally/descriptor-wise extreme — the same quantity plotted on
a Williams plot, with the usual warning threshold :math:`h^* = 3(p+1)/n`.

*Leverage looks at X, not y. A point can have a perfectly ordinary target value and still be structurally*
*novel — an unusual combination of descriptors the model has barely seen examples of.*

*Real output from an actual ROBERT v2.2.0 report: the applicability-domain scatter (left) and the*
*Williams plot itself — leverage on the x-axis, standardized residual on the y-axis, with the*
*h\* threshold marked as a vertical dashed line (right).*

============== ================================
Points         Scaled RMSE (high-leverage 20%)
============== ================================
•• 2            ≤ 10%
•\ |space| 1    ≤ 20%
0               > 20%
============== ================================

Score ranges
++++++++++++

For regression, each of the two scores (Interpolation and Boundary robustness) is rated independently on
the same five-tier scale below — a model can, for example, be a "very strong" interpolator while only
"moderate" at the boundary. For classification, only Interpolation is rated (see above).

Some of the most common reasons for getting low scores are:

* Unbalanced datasets (i.e., too many points in a region, too few in others)
* Including too few datapoints
* Including too few descriptors
* Overfitted and underfitted models

Different causes that might be affecting your score are included in the CheckML score section of the PDF report.

**Very weak models:** very unreliable models. 

**Weak models:** unreliable models. 

**Moderate models:** somewhat reliable models. 

**Strong models:** reliable models.

**Very strong models:** highly reliable models.

.. robert-score-end

## robert/docs/Examples/full_workflow/full_workflow.rst

Full workflow from CSV
======================

Overview
++++++++

.. |fullworkflow_fig| image:: ../../Modules/images/FullWorkflow.jpg
   :width: 600

.. centered:: |fullworkflow_fig|

Required inputs
+++++++++++++++

.. |csv_FW| image:: ../images/csv_icon.jpg
   :target: ../../_static/Robert_example.csv
   :width: 30

* **Robert_example.csv:** CSV file with data to use as the training and validation sets. The full CSV file can be 
  found in the `"Examples" folder of the ROBERT repository <https://github.com/jvalegre/robert/tree/master/Examples/CSV_workflow>`__ 
  or downloaded here: |csv_FW|

.. csv-table:: 
   :file: CSV/Robert_example.csv
   :header-rows: 1

Executing the job
+++++++++++++++++

**Instructions:**

1. Download the **Robert_example.csv** file specified in Required inputs.
2. Go to the folder containing the CSV file in your terminal (using the "cd" command, i.e. :code:`cd C:/Users/test_robert`).
3. Activate the conda environment where ROBERT was installed (:code:`conda activate robert`).
4. Run the following command line:

.. code:: shell

   python -m robert --names Name --y Target_values --csv_name Robert_example.csv

**Options used:**

* :code:`--names Name`: Name of the column containing the names of the datapoints. This feature allows to print the names of the outlier points (if any).  

* :code:`--y Target_values`: Name of the column containing the response y values.  

* :code:`--csv_name Robert_example.csv`: CSV with the database.   

Execution time and versions
+++++++++++++++++++++++++++

Time: ~3.5 min

System: 8 processors (11th Gen Intel(R) Core(TM) i7-1165G7 @ 2.80GHz) using 16.0 GB RAM memory

ROBERT version: 2.0.1

scikit-learn-intelex version: 2025.2.0

Results
+++++++

.. |pdf_report_test| image:: ../images/pdf_icon.jpg
   :target: ../../_static/ROBERT_report.pdf
   :width: 30

A PDF file called **ROBERT_report.pdf** should be created in the folder where ROBERT was executed. The PDF file can be visualized here: |pdf_report_test|

The PDF report contains all the results of the workflow. In this case, two Neural Network (NN) models were the optimal model found from: 

   * Four different models (Gradient Boosting GB, MultiVariate Linear MVL, Neural Network NN, Random Forest RF) 

The first part of the PDF file is shown below as a preview:

.. |pdf_preview| image:: ../images/FW/preview.png
   :width: 400

|pdf_preview|

## robert/docs/Examples/full_workflow/full_workflow_test.rst

New predictions
===============

Required inputs
+++++++++++++++

.. |csv_FW_test| image:: ../images/csv_icon.jpg
   :target: ../../_static/Robert_example_test.csv
   :width: 30

* **Robert_example_test.csv:** CSV file with data to use as the external test set. The full CSV file can be 
  found in the `"Examples" folder of the ROBERT repository <https://github.com/jvalegre/robert/tree/master/Examples/CSV_workflow>`__ 
  or downloaded here: |csv_FW_test|

.. csv-table:: 
   :file: CSV/Robert_example_test.csv
   :header-rows: 1

Executing the job
+++++++++++++++++

**Instructions:**

1. Run the **Full workflow from CSV** workflow from the Examples.
2. Download the **Robert_example_test.csv** file specified in Required inputs and paste it in the same working folder.
3. Go to the working folder in your terminal (using the "cd" command, i.e. :code:`cd C:/Users/test_robert`).
4. Activate the conda environment where ROBERT was installed (:code:`conda activate robert`).
5. Run the following command line:

.. code:: shell

    python -m robert --predict --csv_test Robert_example_test.csv

.. note:: 

   The --csv_test option can be used as part of end-to-end workflows. For example, this option can be added
   to the "Full workflow from CSV" example:
   
   :code:`python -m robert --names Name --y Target_values --csv_name Robert_example.csv --csv_test Robert_example_test.csv`

**Options used:**

* :code:`--predict`: only runs the PREDICT module.  

* :code:`--names Name`: Name of the column containing the names of the datapoints. This feature allows to print the names of the outlier points (if any).  

* :code:`--csv_test Robert_example_test.csv`: CSV with the external test set.  

Execution time and versions
+++++++++++++++++++++++++++

Time: ~10 sec

System: 8 processors (11th Gen Intel(R) Core(TM) i7-1165G7 @ 2.80GHz) using 16.0 GB RAM memory

ROBERT version: 2.0.1

scikit-learn-intelex version: 2025.2.0

Results
+++++++

.. |csv_no_pfi| image:: ../images/csv_icon.jpg
   :target: ../../_static/Robert_example_test_NN_No_PFI.csv
   :width: 30

.. |csv_pfi| image:: ../images/csv_icon.jpg
   :target: ../../_static/Robert_example_test_NN_PFI.csv
   :width: 30

Two CSV files called **Robert_example_test_NN_No_PFI** and **Robert_example_test_NN_PFI** should be created inside the PREDICT folder. The two files 
contain the predictions from the two different Neural Network (NN) models, with and without PFI filtering,
obtained in the Full workflow example.

The CSV files can be visualized here: |csv_no_pfi| (No PFI), |csv_pfi| (PFI)

If you want to tabulate your results inside a report PDF, run this command line:

.. code:: shell

    python -m robert --report

.. |pdf_report_test| image:: ../images/pdf_icon.jpg
   :target: ../../_static/predictions_report.pdf
   :width: 30

The PDF file can be visualized here: |pdf_report_test|

The predictions are sorted at the end of the PDF report (including both the No_PFI and the PFI models):

.. |predictions_fig| image:: ../images/FW_test/Predictions.jpg
   :width: 600

.. centered:: |predictions_fig|

## robert/docs/Examples/full_workflow/smiles_vaskas.rst

SMILES workflow with atomic properties
======================================

Overview
++++++++

This is a modified version of the workflow used in the ROBERT manuscript for Vaska's catalysts, 
with a smaller database size.

.. |aqme_fig| image:: ../images/FW_vaska/vaska.jpg
   :width: 600

.. centered:: |aqme_fig|

Reproducibility warning
+++++++++++++++++++++++

.. warning::

   **Update to AQME v1.6.0 or higher to obtain fully reproducible results!** You can do it with :code:`pip install aqme --upgrade`.
   Otherwise, it may not be possible to exactly reproduce the results due to subtle differences in the 
   generated xTB descriptors (0.1% changes in most cases).

Required inputs
+++++++++++++++

* **vaska_short.csv:** CSV file with SMILES to generate descriptors that will be used as the training and validation sets. The full CSV file can be downloaded here: |csv_smi|

.. |csv_smi| image:: ../images/csv_icon.jpg
   :target: ../../_static/vaska_short.csv
   :width: 30  

.. csv-table:: 
   :file: CSV/vaska_short.csv
   :header-rows: 1
   :widths: 10, 10, 10, 10, 10, 10, 10

The CSV database contains parameters used in the AQME workflow:

* :code:`code_name`: compound names.  

* :code:`smiles`: SMILES strings of the Ir complexes.  

* :code:`barrier`: activation energy barriers.  

* :code:`charge`: charge of the Ir complexes.  

* :code:`mult`: multiplicity of the Ir complexes.  

* :code:`complex_type`: defines squareplanar geometry during conformer generation.  

* :code:`geom`: filters off conformers based on ligand positions of Ir squareplanar complexes.  

Required packages
+++++++++++++++++

* **Openbabel:** Install Openbabel with conda-forge:

.. code:: shell

    conda install -y -c conda-forge openbabel=3.1.1

* **AQME:** Install (or update) AQME with conda-forge (or follow the instructions from `their ReadtheDocs <https://aqme.readthedocs.io>`__):

.. code:: shell

    pip install aqme

* **xTB:** Install xTB with conda-forge (or follow the instructions from `their documentation <https://xtb-docs.readthedocs.io>`__):

.. code:: shell

    conda install -y -c conda-forge xtb

.. warning::

  Due to an update in the libgfortran library, **xTB** and **CREST** may encounter issues during optimizations. If you plan to use them, please make sure to run the following command **after** installing them:

.. code-block:: shell 

   conda install conda-forge::libgfortran=14.2.0

Executing the job
+++++++++++++++++

**Instructions:**

1. Install the programs specified in Required packages.
2. Download the **vaska_short.csv** file specified in Required inputs.
3. Go to the folder containing the CSV file in your terminal (using the "cd" command, i.e. :code:`cd C:/Users/test_robert`).
4. Activate the conda environment where ROBERT was installed (:code:`conda activate robert`).
5. Run the following command line:

.. code:: shell

    python -m robert --aqme --y "barrier" --csv_name "vaska_short.csv" --qdescp_keywords "--qdescp_atoms ['Ir']"

**Options used:**

* :code:`--aqme`: Calls the AQME module to convert SMILES into RDKit and xTB descriptors, retrieving a new CSV database. 

* :code:`--y barrier`: Name of the column containing the response y values.  

* :code:`--csv_name vaska_short.csv`: CSV with the SMILES strings.  

* :code:`--qdescp_keywords "--qdescp_atoms ['Ir']"`: activates the generation of atomic descriptors with xTB using SMARTS patterns.  

.. |br| raw:: html

   <br />

.. note:: 

   In this example, the SMARTS pattern used is 'Ir', which specifies Ir atoms. The program allows 
   the use of multiple SMARTS patterns simultaneously, using commas as separators, and it accepts atoms, 
   bonds, and other structural motifs. For example:

   1.	Atomic descriptors at Zn and Ir centers: :code:`"--qdescp_atoms ['Zn','Ir']"` |br|
   2. At the two C atoms of a triple bond: :code:`"--qdescp_atoms ['C#C']"` |br|
   3.	At the C and Zn atoms from a C-Zn bond: :code:`"--qdescp_atoms ['[C][Zn]']"` |br|
   4.	At the C and Zn atoms from a C-Zn bond, and at the two C atoms of a triple bond: :code:`"--qdescp_atoms ['[C][Zn]','C#C']"` |br|
   5.	At a Zn atom and at the two C atoms of a triple bond: :code:`"--qdescp_atoms ['Zn','C#C']"`

   For more information about SMARTS patterns, follow `this link <https://www.daylight.com/dayhtml/doc/theory/theory.smarts.html>`__.

.. warning::

   When :code:`--qdescp_keywords "--qdescp_atoms ['Ir']"` is used, all the molecules in the database that 
   do not contain Ir atoms will not be included in the workflow. 

By default, the workflow sets:

* :code:`--ignore "[code_name]"` (variables ignored in the model)

* :code:`--discard "[smiles,charge,mult,complex_type,geom]"` (variables discarded after descriptor generation)

* :code:`--names code_name` (name of the column containing the names of the datapoints)  

Execution time and versions
+++++++++++++++++++++++++++

Time: ~3 min

System: 4 processors (Intel Xeon Ice Lake 8352Y) using 8.0 GB RAM memory

ROBERT version: 1.2.0

scikit-learn-intelex version: 2024.5.0

AQME version: 1.6.1

xTB version: 6.6.1

Results
+++++++

**Initial AQME workflow**

.. |csv_report_vaska| image:: ../images/csv_icon.jpg
   :target: ../../_static/AQME-ROBERT_vaska_short.csv
   :width: 30

* The workflow starts with a CSEARCH-RDKit conformer sampling (using RDKit by default, although CREST is also available if :code:`--csearch_keywords "--program crest"` is added).

* Then, QDESCP is used to generate more than 200 RDKit and xTB Boltzmann-averaged molecular descriptors (using xTB geometry optimizations and different single-point calculations).

A CSV file called **AQME-ROBERT_vaska_short.csv** should be created in the folder where ROBERT was executed. The CSV 
file can be downloaded here: |csv_report_vaska|

**Following ROBERT workflow**

.. |pdf_report_vaska| image:: ../images/pdf_icon.jpg
   :target: ../../_static/ROBERT_report_vaska.pdf
   :width: 30

A PDF file called **ROBERT_report.pdf** should be created in the folder where ROBERT was executed. The PDF 
file can be visualized here: |pdf_report_vaska|

The PDF report contains all the results of the workflow. In this case, a Random Forest (RF) model with 60% training size and a Neural Network (NN) with 70% training size were the optimal models found from: 

  * Four different models (Gradient Boosting GB, MultiVariate Linear MVL, Neural Network NN, Random Forest RF) 
  * Two different partition sizes (60%, 70%) 

The first part of the PDF file is shown below as a preview:

.. |pdf_preview| image:: ../images/FW_vaska/preview_vaska.png
   :width: 400

|pdf_preview|

## robert/docs/Examples/full_workflow/smiles_workflow.rst

Full workflow from SMILES
=========================

Overview
++++++++

.. |aqme_fig| image:: ../../Modules/images/AQME.jpg
   :width: 600

.. centered:: |aqme_fig|

Reproducibility warning
+++++++++++++++++++++++

.. warning::

   **Update to AQME v1.6.0 or higher to obtain fully reproducible results!** You can do it with :code:`pip install aqme --upgrade`.
   Otherwise, it may not be possible to exactly reproduce the results due to subtle differences in the 
   generated xTB descriptors (0.1% changes in most cases).

Required inputs
+++++++++++++++

* **solubility_short.csv:** CSV file with SMILES to generate descriptors that will be used as the training and validation sets. The full CSV file can be found in the `Examples folder of the ROBERT repository <https://github.com/jvalegre/robert/tree/master/Examples/SMILES_workflow>`__ or downloaded here: |csv_smi|

.. |csv_smi| image:: ../images/csv_icon.jpg
   :target: ../../_static/solubility_short.csv
   :width: 30  

.. csv-table:: 
   :file: CSV/solubility_short.csv
   :header-rows: 1
   :widths: 25, 25, 25

The CSV database contains the following columns:

* :code:`code_name`: compound names.  

* :code:`smiles`: SMILES strings of the compounds.  

* :code:`solubility`: solubility of the compounds.  

Required packages
+++++++++++++++++

* **Openbabel:** Install Openbabel with conda-forge:

.. code:: shell

    conda install -y -c conda-forge openbabel=3.1.1

* **AQME:** Install (or update) AQME with conda-forge (or follow the instructions from `their ReadtheDocs <https://aqme.readthedocs.io>`__):

.. code:: shell

    pip install aqme

* **xTB:** Install xTB with conda-forge (or follow the instructions from `their documentation <https://xtb-docs.readthedocs.io>`__):

.. code:: shell

    conda install -y -c conda-forge xtb

.. warning::

  Due to an update in the libgfortran library, **xTB** and **CREST** may encounter issues during optimizations. If you plan to use them, please make sure to run the following command **after** installing them:

.. code-block:: shell 

   conda install conda-forge::libgfortran=14.2.0

Executing the job
+++++++++++++++++

**Instructions:**

1. Install the programs specified in Required packages.
2. Download the **solubility_short.csv** file specified in Required inputs.
3. Go to the folder containing the CSV file in your terminal (using the "cd" command, i.e. :code:`cd C:/Users/test_robert`).
4. Activate the conda environment where ROBERT was installed (:code:`conda activate robert`).
5. Run the following command line:

.. code:: shell

    python -m robert --aqme --y solubility --csv_name solubility_short.csv

**Options used:**

* :code:`--aqme`: Calls the AQME module to convert SMILES into RDKit and xTB descriptors, retrieving a new CSV database. 

* :code:`--y solubility`: Name of the column containing the response y values.  

* :code:`--csv_name solubility_short.csv`: CSV with the SMILES strings.  

By default, the workflow sets:

* :code:`--ignore "[code_name]"` (variables ignored in the model)

* :code:`--discard "[smiles]"` (variables discarded after descriptor generation)

* :code:`--names code_name` (name of the column containing the names of the datapoints)  

Execution time and versions
+++++++++++++++++++++++++++

Time: ~1.5 min

System: 4 processors (Intel Xeon Ice Lake 8352Y) using 8.0 GB RAM memory

ROBERT version: 1.2.0

scikit-learn-intelex version: 2024.5.0

AQME version: 1.6.1

xTB version: 6.6.1

Results
+++++++

**Initial AQME workflow**

.. |csv_report_smi| image:: ../images/csv_icon.jpg
   :target: ../../_static/AQME-ROBERT_solubility_short.csv
   :width: 30

* The workflow starts with a CSEARCH-RDKit conformer sampling (using RDKit by default, although CREST is also available if :code:`--csearch_keywords "--program crest"` is added).

* Then, QDESCP is used to generate more than 200 RDKit and xTB Boltzmann-averaged molecular descriptors (using xTB geometry optimizations and different single-point calculations).

A CSV file called **AQME-ROBERT_solubility_short.csv** should be created in the folder where ROBERT was executed. The CSV 
file can be downloaded here: |csv_report_smi|

**Following ROBERT workflow**

.. |pdf_report_smiles| image:: ../images/pdf_icon.jpg
   :target: ../../_static/ROBERT_report_smiles.pdf
   :width: 30

A PDF file called **ROBERT_report.pdf** should be created in the folder where ROBERT was executed. The PDF 
file can be visualized here: |pdf_report_smiles|

The PDF report contains all the results of the workflow. In this case, two Random Forest (RF) models with 70% training sizes were the optimal models found from: 

  * Four different models (Gradient Boosting GB, MultiVariate Linear MVL, Neural Network NN, Random Forest RF) 
  * Two different partition sizes (60%, 70%) 

The first part of the PDF file is shown below as a preview:

.. |pdf_preview| image:: ../images/FW_smiles/preview_smiles.png
   :width: 400

|pdf_preview|

## robert/docs/Examples/modules/curation.rst

CURATE (data curation)
----------------------

Overview
++++++++

.. |curate| image:: ../../Modules/images/CURATE.jpg
   :width: 600

.. centered:: |curate|

Required inputs
+++++++++++++++

.. |csv_FW| image:: ../images/csv_icon.jpg
   :target: ../../_static/Robert_example.csv
   :width: 30

* **Robert_example.csv:** CSV file with data to curate. The full CSV file can be found in the `Examples folder of the ROBERT repository <https://github.com/jvalegre/robert/tree/master/Examples/CSV_workflow>`__ or downloaded here: |csv_FW|

.. csv-table:: 
   :file: ../full_workflow/CSV/Robert_example.csv
   :header-rows: 1

Executing the job
+++++++++++++++++

**Instructions:**

1. First, go to the folder containing the CSV files in your terminal.
2. Run the following command line:

.. code:: shell

    python -m robert --names Name --y Target_values --csv_name Robert_example.csv --curate

**Options used:** 

* :code:`--names Name`: Name of the column containing the names of the datapoints.  

* :code:`--y Target_values`: Name of the column containing the response y values.  

* :code:`--csv_name Robert_example.csv`: CSV with the data to curate.  

* :code:`--curate`: Use only the CURATE module.  

Execution time
++++++++++++++

Time: ~5 seconds

System: 4 processors (Intel Xeon Ice Lake 8352Y) using 8.0 GB RAM memory

Results
+++++++

* A CSV file containing the curated database (Robert_example_CURATE.csv) should be created inside the CURATE folder.

## robert/docs/Examples/modules/prediction.rst

PREDICT (predict external test set and feature importance analysis)
-------------------------------------------------------------------

Overview
++++++++

.. |predict| image:: ../../Modules/images/PREDICT.jpg
   :width: 600

.. centered:: |predict|

Required inputs
+++++++++++++++

.. |csv_FW_test| image:: ../images/csv_icon.jpg
   :target: ../../_static/Robert_example_test.csv
   :width: 30

* Previous folder from a GENERATE job.
* **Robert_example_test.csv:** CSV file with data to use as the external test set. The full CSV file can be found in the `Examples folder of the ROBERT repository <https://github.com/jvalegre/robert/tree/master/Examples/CSV_workflow>`__ or downloaded here: |csv_FW_test|

.. csv-table:: 
   :file: ../full_workflow/CSV/Robert_example_test.csv
   :header-rows: 1

Executing the job
+++++++++++++++++

**Instructions:**

1. First, go to the folder where GENERATE was previously run in your terminal. You should see a folder called GENERATE on it.
2. Run the following command line:

.. code:: shell

    python -m robert --csv_test Robert_example_test.csv --names Name --predict

**Options used:**

* :code:`--csv_test Robert_example_test.csv`: CSV with the external test set.  

* :code:`--names Name`: Name of the column containing the names of the datapoints. This feature allows to print the names of the outlier points (if any).  

* :code:`--predict`: Use only the PREDICT module.  

Execution time
++++++++++++++

Time: ~10 seconds

System: 4 processors (Intel Xeon Ice Lake 8352Y) using 8.0 GB RAM memory

Results
+++++++

* Two graphs, for No_PFI and for PFI (in /PREDICT), with: representation of predictions, SHAP feature analysis, PFI feature analysis and outlier analysis .
* Six CSV files with the predictions of each set, for No_PFI and for PFI (in /PREDICT).

## robert/docs/Examples/modules/screening.rst

GENERATE (screening of ML models)
---------------------------------

Overview
++++++++

.. |generate| image:: ../../Modules/images/GENERATE.jpg
   :width: 600

.. centered:: |generate|

Required inputs
+++++++++++++++

* **Robert_example_CURATE.csv:** Curated CSV file with data to use as the training and validation sets. It is created in a previous CURATE job.

.. csv-table:: 
   :file: Robert_example_CURATE.csv
   :header-rows: 1

Executing the job
+++++++++++++++++

**Instructions:**

1. First, go to the folder where CURATE was previously run in your terminal. You should see a folder called CURATE on it.
2. Run the following command line:

.. code:: shell

    python -m robert --csv_name CURATE/Robert_example_CURATE.csv --generate

**Options used:**

* :code:`--csv_name CURATE/Robert_example_CURATE.csv`: CSV with the curated database.  

* :code:`--generate`: Use only the GENERATE module.  

Execution time
++++++++++++++

Time: ~2 min

System: 4 processors (Intel Xeon Ice Lake 8352Y) using 8.0 GB RAM memory

Results
+++++++

* Four CSV files for each combination of ML model/training size (in /GENERATE/Raw_data). Half of the CSVs relate to models with all the variables (No_PFI folder) and the other half for models that use only the msot important features based on PFI (PFI folder). For each pair of CSVs, one contains the parameters of the model and the other contains the database already split into training/validation sets (_db suffix).
* The two best models, for No_PFI (all descriptors) and for PFI (only important descriptors), are stored in /GENERATE/Best_model.
* Two heatmaps with a summary of the results for all the models, created in /GENERATE/Raw_data.

## robert/docs/Examples/modules/verification.rst

VERIFY (verification of predictive ability)
-------------------------------------------

Overview
++++++++

.. |verify| image:: ../../Modules/images/VERIFY.jpg
   :width: 600

.. centered:: |verify|

Required inputs
+++++++++++++++

* Previous folder from a GENERATE job.

Executing the job
+++++++++++++++++

**Instructions:**

1. First, go to the main folder where GENERATE was run in your terminal. You should see a folder called GENERATE on it.
2. Run the following command line:

.. code:: shell

    python -m robert --verify

**Options used:**

* :code:`--verify`: Use only the VERIFY module.  

Execution time
++++++++++++++

Time: ~2 seconds

System: 4 processors (Intel Xeon Ice Lake 8352Y) using 8.0 GB RAM memory

Results
+++++++

* Two donut plots (for No_PFI and PFI) with a summary of the results of the four verification tests, created in /VERIFY.

## robert/docs/Misc/abbreviations.rst

=============
Abbreviations
=============

===========================================   =======================================
A to M                                        N to Z
===========================================   =======================================
**ACC:** accuracy                             **NN:** neural network
**ADAB:** AdaBoost                            **PFI:** permutation feature importance
**CSV:** comma separated values               **R2:** coefficient of determination
**CLAS:** classification                      **REG:** Regression
**CV:** cross-validation                      **RF:** random forest
**F1 score:** balanced F-score                **RMSE:** root mean square error
**GB:** gradient boosting                     **RND:** random
**GP:** gaussian process                      **SHAP:** Shapley additive explanations
**KN:** k-nearest neighbors                   **VR:** voting regressor
**MAE:** root-mean-square error 
**MCC:** Matthew's correlation coefficient
**ML:** machine learning                         
**MVL:** multivariate lineal models
===========================================   =======================================

## ROBERT parameters (curate.py, from the installed package)

Parameters
----------

    csv_name : str, default=''
        Name of the CSV file containing the database. A path can be provided (i.e. 'C:/Users/FOLDER/FILE.csv'). 
    y : str, default=''
        Name of the column containing the response variable in the input CSV file (i.e. 'solubility'). 
    discard : list, default=[]
        List containing the columns of the input CSV file that will not be included as descriptors
        in the curated CSV file (i.e. "['name','SMILES']").
    ignore : list, default=[]
        List containing the columns of the input CSV file that will be ignored during the curation process
        (i.e. "['name','SMILES']"). The descriptors will be included in the curated CSV file. The y value
        is automatically ignored.
    names : str, default=''
        Column of the names for each datapoint. Names are used to print outliers.
    destination : str, default=None,
        Directory to create the output file(s).
    varfile : str, default=None
        Option to parse the variables using a yaml file (specify the filename, i.e. varfile=FILE.yaml).  
    categorical : str, default='onehot'
        Mode to convert data from columns with categorical variables. As an example, a variable containing 4
        types of C atoms (i.e. primary, secondary, tertiary, quaternary) will be converted into categorical
        variables. Options: 
        1. 'onehot' (for one-hot encoding, ROBERT will create a descriptor for each type of
        C atom using 0s and 1s to indicate whether the C type is present)
        2. 'numbers' (to describe the C atoms with numbers: 1, 2, 3, 4).
    corr_filter_x : bool, default=True
        Activate the correlation filters of descriptors, based on the correlation
        of the descriptors with other descriptors (x filter).
    corr_filter_y : bool, default=False
        Activate the correlation filters of descriptors, based on the correlation
        of the descriptors with the y values (y filter, for noise). This filter is only
        suggested for MVL.
    rfecv_filter : bool, default=True
        Activate RFECV/PFI descriptor selection, used when descriptors still outnumber
        one-third of the datapoints after the correlation filter(s) above. Runs independently
        of corr_filter_x/corr_filter_y, so either filter can be used on its own (e.g. disable
        rfecv_filter to keep only the correlation filter, or disable corr_filter_x/y to rely
        only on RFECV/PFI).
    desc_thres : float, default=25
        Threshold for the descriptor-to-datapoints ratio to loose the correlation filter. By default,
        the correlation filter is loosen if there are 25 times more datapoints than descriptors.
    thres_x : float, default=0.7
        Thresolhold to discard descriptors based on high R**2 correlation with other descriptors (i.e. 
        if thres_x=0.7, variables that show R**2 > 0.7 will be discarded).
    thres_y : float, default=0.001
        Thresolhold to discard descriptors with poor correlation with the y values based on R**2 (i.e.
        if thres_y=0.001, variables that show R**2 < 0.001 will be discarded).
    seed : int, default=0
        Random seed used in RFECV feature selector and other protocols.
    kfold : int, default=5
        Number of random data splits for the cross-validation of the RFECV feature selector. 
    repeat_kfolds : int, default=10
        Number of repetitions for the k-fold cross-validation of the RFECV feature selector.
    auto_type : bool, default=True
        If there are only two y values, the program automatically changes the type of problem to classification.
    auto_fill : bool, default = True
        Complete missing values in columns with descriptors of "float" type using a KNN imputer

## ROBERT parameters (generate.py, from the installed package)

Parameters
----------

    csv_name : str, default=''
        Name of the CSV file containing the database. A path can be provided (i.e. 'C:/Users/FOLDER/FILE.csv'). 
    y : str, default=''
        Name of the column containing the response variable in the input CSV file (i.e. 'solubility'). 
    discard : list, default=[]
        List containing the columns of the input CSV file that will not be included as descriptors
        in the curated CSV file (i.e. ['name','SMILES']).
    ignore : list, default=[]
        List containing the columns of the input CSV file that will be ignored during the curation process
        (i.e. ['name','SMILES']). The descriptors will be included in the curated CSV file. The y value
        is automatically ignored.
    destination : str, default=None
        Directory to create the output file(s).
    varfile : str, default=None
        Option to parse the variables using a yaml file (specify the filename, i.e. varfile=FILE.yaml).  
    auto_type : bool, default=True
        If there are only two y values, the program automatically changes the type of problem to classification.
    model : list, default=['RF','GB','NN','MVL'] (regression) and default=['RF','GB','NN','AdaB'] (classification) 
        ML models available: 
        1. 'RF' (Random forest)
        2. 'MVL' (Multivariate lineal models)
        3. 'GB' (Gradient boosting)
        4. 'NN' (MLP neural network)
        5. 'GP' (Gaussian Process)
        6. 'AdaB' (AdaBoost)
        7. 'RIDGE' (Ridge regression, regression only)
        8. 'LOGISTIC' (Logistic regression, classification only)
    type : str, default='reg'
        Type of the pedictions. Options:
        1. 'reg' (Regressor)
        2. 'clas' (Classifier)
    all_models : bool, default=True
        Runs the full VERIFY/PREDICT/REPORT pipeline for every screened model (from the 'model'
        option), each producing its own PDF report - instead of only the single best one. All
        the PDFs are moved into a REPORT_models folder, keeping one overall-best model and
        variant report in the working directory. Set to False to run only the
        GENERATE-selected model; REPORT can still create both No PFI and PFI PDFs
        for that model when PFI filtering is enabled (faster).
    seed : int, default=0
        Random seed used in the ML predictor models and other protocols.
    error_type : str, default: rmse (regression), mcc (classification)
        Target value used during the hyperopt optimization. Options:
        Regression:
        1. rmse (root-mean-square error)
        2. mae (mean absolute error)
        3. r2 (R-squared, not recommended since R2 might be good even with high errors in small datasets)
        Classification:
        1. mcc (Matthew's correlation coefficient)
        2. f1 (F1 score)
        3. acc (accuracy, fraction of correct predictions)
    init_points : int, default=10
        Number of initial points for Bayesian optimization (exploration)
    n_iter : int, default=10
        Number of iterations for Bayesian optimization (exploitation)
    expect_improv : int, default=0.05
        Expected improvement for Bayesian optimization
    pfi_filter : bool, default=True
        Activate the PFI filter of descriptors.
    pfi_epochs : int, default=5
        Sets the number of times a feature is randomly shuffled during the PFI analysis
        (standard from sklearn webpage: 5).
    pfi_threshold : float, default=0.2
        The PFI filter is X% of the model's score (% adjusted, 0.2 = 20% of the total score during PFI).
    pfi_max : int, default=0
        Number of features to keep after the PFI filter. If pfi_max is 0, all the features that pass the PFI
        filter are used.
    auto_test : bool, default=True
        Raises % of test points to 20% if test_set is lower than that.
    test_set : float, default=0.2
        Amount of datapoints to separate as external test set (0.2 = 20%). These points will not be used during the
        hyperoptimization, and PREDICT will use the points as test set during ROBERT workflows. Select
        --test_set 0 to use only training and validation.
    kfold : int, default=5
        Number of random data splits for the cross-validation of the models. 
    repeat_kfolds : int, default=10
        Number of repetitions for the k-fold cross-validation of the models.
    split : str, default='auto' (resolves to 'even' for regression, 'stratified' for classification)
        Specifies how the data is split into training and test sets. Options:
        1. 'auto': resolves to 'even' (regression) or 'stratified' (classification).
        2. 'even': splits the data evenly into training and test sets.
        3. 'RND': randomly splits the data.
        4. 'stratified': splits the data while preserving the distribution of the target variable.
        5. 'KN': uses a k-means approach to select representative samples for training (good for intrapolation, bad for boundary robustness).
        6. 'extra_q1': selects the 20% lowest values.
        7. 'extra_q5': selects the 20% highest values.
        

## ROBERT parameters (verify.py, from the installed package)

Parameters
----------

    destination : str, default=None,
        Directory to create the output file(s).
    varfile : str, default=None
        Option to parse the variables using a yaml file (specify the filename, i.e. varfile=FILE.yaml).  
    params_dir : str, default=''
        Folder containing the database and parameters of the ML model to analyze.
    seed : int, default=0
        Random seed used in the ML predictor models and other protocols.
    kfold : int, default=5
        Number of random data splits for the cross-validation of the models. 
    repeat_kfolds : int, default=10
        Number of repetitions for the k-fold cross-validation of the models.

## ROBERT parameters (predict.py, from the installed package)

Parameters
----------

    destination : str, default=None,
        Directory to create the output file(s).
    varfile : str, default=None
        Option to parse the variables using a yaml file (specify the filename, i.e. varfile=FILE.yaml).  
    params_dir : str, default=''
        Folder containing the database and parameters of the ML model.
    csv_test : str, default=''
        Name of the CSV file containing the test set (if any). A path can be provided (i.e. 
        'C:/Users/FOLDER/FILE.csv'). 
    t_value : float, default=2
        t-value that will be the threshold to identify outliers (check tables for t-values elsewhere).
        The higher the t-value the more restrictive the analysis will be (i.e. there will be more 
        outliers with t-value=1 than with t-value = 4).
    alpha : float, default=0.05
        Significance level, or probability of making a wrong decision. This parameter is related to
        the confidence intervals (i.e. 1-alpha is the confidence interval). By default, an alpha value
        of 0.05 is used, which corresponds to a confidence interval of 95%.
    shap_show : int, default=10,
        Number of descriptors shown in the plot of the SHAP analysis.
    pfi_show : int, default=10,
        Number of descriptors shown in the plot of the PFI analysis.
    pfi_epochs : int, default=5,
        Sets the number of times a feature is randomly shuffled during the PFI analysis
        (standard from sklearn webpage: 5).
    names : str, default=''
        Column of the names for each datapoint. Names are used to print outliers.

## ROBERT parameters (report.py, from the installed package)

Parameters
----------

    destination : str, default=None,
        Directory to create the output file(s).
    varfile : str, default=None
        Option to parse the variables using a yaml file (specify the filename, i.e. varfile=FILE.yaml).
    report_modules : list of str, default=['CURATE','GENERATE','VERIFY','PREDICT']
        List of the modules to include in the report.
    debug_report : bool, default=False
        Debug mode using during the pytests of report.py

## ROBERT parameters (aqme.py, from the installed package)

Parameters
----------

    csv_name : str, default=''
        Name of the CSV file containing the database with SMILES and code_name columns. A path can be provided (i.e. 'C:/Users/FOLDER/FILE.csv'). 
    destination : str, default=None,
        Directory to create the output file(s).
    varfile : str, default=None
        Option to parse the variables using a yaml file (specify the filename, i.e. varfile=FILE.yaml).  
    y : str, default=''
        Name of the column containing the response variable in the input CSV file (i.e. 'solubility'). 
    qdescp_keywords : str, default=''    
        Add extra keywords to the AQME-QDESCP run (i.e. qdescp_keywords="--qdescp_atoms ['Ir']")
    descp_lvl : str, default='interpret'
        Type of descriptor to be used in the AQME-ROBERT workflow. Options are 'interpret', 'denovo' or 'full'.
