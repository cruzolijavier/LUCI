# AQME (CSEARCH, CMIN, QDESCP): upstream documentation

Source: https://github.com/jvalegre/aqme

## aqme/README.md

#
## <p align="center"> AQME (Automated Quantum Mechanical Environments)</p>

[](https://app.circleci.com/pipelines/github/jvalegre/aqme)
[](https://codecov.io/gh/jvalegre/aqme)
[](https://www.pepy.tech/projects/aqme)
[](https://aqme.readthedocs.io/)
[](https://pypi.org/project/aqme/)

## Documentation  
Full documentation with installation instructions, technical details and examples can be found in [Read the Docs](https://aqme.readthedocs.io).  

Don't miss out the latest hands-on tutorials from our [YouTube channel](https://www.youtube.com/channel/UCHRqI8N61bYxWV9BjbUI4Xw)!  

## Recommended installation
1. (Only once) Create new conda environment: `conda create -n aqme python=3.12`  
2. Activate conda environment: `conda activate aqme`  
3. Install AQME using pip: `pip install aqme`  
4. Install Open Babel: `conda install -y -c conda-forge openbabel=3.1.1`  

* Inexperienced users should visit the *Users with no Python experience* section in our [Read the Docs](https://aqme.readthedocs.io).

## Update the program
1. Update to the latest version: `pip install aqme --upgrade`  

## Developers and help desk
List of main developers and contact emails:  
  - [ ] [Juan V. Alegre-Requena](https://orcid.org/0000-0002-0769-7168), main developer of the CSEARCH, QCORR, QPREP and QDESCP modules. Contact: [jv.alegre@csic.es](mailto:jv.alegre@csic.es)  
  - [ ] [Shree Sowndarya S. V.](https://orcid.org/0000-0002-4568-5854), main developer of the CSEARCH, CMIN and QDESCP modules. Contact: [svss@colostate.edu](mailto:svss@colostate.edu)  
  - [ ] [Brenda Manzanilla](https://orcid.org/0000-0001-5955-6079), developer of the QDESCP module. Contact: [iqmanzanilla@gmail.com](mailto:iqmanzanilla@gmail.com)
  - [ ] [David Dalmau](https://orcid.org/0000-0002-2506-6546), developer of the QDESCP module. Contact: [ddalmau@unizar.es](mailto:ddalmau@unizar.es)  
  - [ ] [Turki Alturaifi](https://www.chem.pitt.edu/person/turki-alturaifi), worked in benchmarking the parameters for RDKit-based conformer generation. Contact: [tma53@pitt.edu](mailto:tma53@pitt.edu)  
  - [ ] [Raúl Pérez-Soto](https://orcid.org/0000-0002-6237-2155), worked in refactoring the code and creating the documentation. Contact: [Raul.Perez_Soto@colostate.edu](mailto:Raul.Perez_Soto@colostate.edu)  
  - [ ] [Robert S. Paton](https://orcid.org/0000-0002-0104-4166), code advisor and feedback. Contact: [robert.paton@colostate.edu](mailto:robert.paton@colostate.edu)  

For suggestions and improvements of the code (greatly appreciated!), please reach out through the issues and pull requests options of Github.  

## License
AQME is freely available under an [MIT](https://opensource.org/licenses/MIT) License  

## Reference
If you use any of the AQME modules, please include this citation:  
Alegre-Requena, J. V.; Sowndarya, S.; Pérez-Soto, R.; Alturaifi, T.; Paton, R. AQME: Automated Quantum Mechanical Environments for Researchers and Educators. *Wiley Interdiscip. Rev. Comput. Mol. Sci.* **2023**, *13*, e1663. (DOI: 10.1002/wcms.1663).  
  
Additionally, please include the corresponding references for the following programs:  
  * If you used CSEARCH with RDKit methods or from SMILES: [RDKit](https://www.rdkit.org)  
  * If you used CSEARCH with CREST methods: [CREST](https://crest-lab.github.io/crest-docs)  
  * If you used CMIN with xTB: [xTB](https://xtb-docs.readthedocs.io/en/latest/contents.html)  
  * If you used CMIN with ANI: [ANI](https://github.com/isayev/ASE_ANI)  
  * If you used QCORR: [cclib](https://cclib.github.io/)  
  * If you used QDESCP with xTB: [xTB](https://xtb-docs.readthedocs.io/en/latest/contents.html)

## aqme/docs/Quickstart/defaults.rst

===============================
Default and Required Parameters
===============================

This documents details the default parameters used in the AQME program.

.. contents::
   :local:

CSEARCH 
-------

.. automodule:: aqme.csearch.base
   :noindex:

CMIN
----

.. automodule:: aqme.cmin
   :noindex:

QPREP
-----

.. automodule:: aqme.qprep
   :noindex:

QCORR
-----

.. automodule:: aqme.qcorr
   :noindex:

QDESCP
------

.. automodule:: aqme.qdescp
   :noindex:

## aqme/docs/Modules/qcorr.rst

QCORR (analysis and correction of QM output files)
==================================================

Overview
--------

.. |QCORR_scheme| image:: images/QCORR_scheme.png
   :width: 600

The QCORR module focuses on the analysis and correction of the output files of 
QM calculations. Here we refer to correction as: 

*  Generate new inputs for calculations that have an error termination 
*  Generate new inputs for calculations containing a wrong number of imaginary frequencies
*  Generate new inputs for calculations with other issues (i.e., SCF convergence issues, no stationary points in FREQ calculations, etc.)
*  Remove duplicated calculations
*  Remove calculations that have isomerized (if the initial input files are provided)
*  Ensure that all provided files have the same level of theory, grid size, 
   program, version, etc.

The following scheme shows how QCORR works and how it sorts the calculations.

.. centered:: |QCORR_scheme|

## aqme/docs/Modules/qdescp.rst

QDESCP (descriptor generation)
==============================

Overview
--------

The QDESCP module implemented in AQME enables the automated calculation of molecular 
and atom-centered descriptors from either SMILES strings or three-dimensional structures. 
In the current implementation, descriptor generation is performed through MORFEUS, which 
acts as a unified interface to obtain electronic and steric descriptors.

Electronic descriptors are extracted from xTB calculations, preferentially using the PTB 
method when available and GFN2-xTB for descriptors not supported at the PTB level. In parallel, 
steric descriptors are computed directly from the GFN2-xTB-optimized geometries.

The overall workflow is summarized in this figure:

.. |QDESCP_scheme| image:: images/QDESCP_scheme.png
   :width: 600

.. centered:: |QDESCP_scheme|

Workflow Description
--------------------

**1. Conformational search (if starting from SMILES)**

When the starting point is a CSV file containing SMILES strings, conformational sampling is first 
performed using the CSEARCH workflow in AQME, typically employing RDKit (default) and optionally CREST.

The generated conformers are filtered using:

- An energy window (ΔE ≤ 5 kcal mol⁻¹)
- RMSD-based filtering
- Butina clustering

This process retains a structurally diverse subset of low-energy conformers (up to five conformers per 
molecule), which are stored as SDF files.

If three-dimensional structures are provided directly (e.g., XYZ or SDF files), the conformational 
search step is skipped, and the structures are used directly for descriptor generation.

**2. Geometry optimization with GFN2-xTB**

The resulting conformers are subsequently optimized at the GFN2-xTB level. This option can be skipped using :code:`xtb_opt=False` (or :code:`--xtb_opt False` in command line).

**3. Descriptor generation**

Through MORFEUS, both molecular and atom-centered descriptors are obtained from 
the optimized geometries. Descriptors are first computed for each conformer and subsequently 
Boltzmann-weighted to obtain a single descriptor set per molecule.

Applicability
-------------

The workflow is applicable to both organic and organometallic systems, provided that the underlying 
xTB calculations converge reliably.

.. warning::

   As with other semiempirical approaches, the quality of the resulting descriptors depends on the robustness of the electronic structure calculations. Systems involving:

    - Multireference character
    - Excited states (i.e., S₁, S₂, T₁...)
    - Aggregates or noncovalent complexes

   should be interpreted with caution.

Output
------

The workflow produces CSV files containing Boltzmann-weighted descriptors corresponding to 
different descriptor subsets:

- interpret *(default)*
- denovo *(reduced set)*
- full *(extended set including RDKit features)*

Descriptor Table
----------------

.. note:: 
    All citations for the descriptors and formulae can be found in our publication describing the descriptor‑generation workflow.

The final descriptor set combines 21 molecular descriptors and 18 atomic descriptors, including:

* xTB-based electronic descriptors *(PTB method when available, if not GFN2-xTB)*
* MORFEUS steric descriptors

.. list-table::
   :widths: 15 20 15 25 10 15
   :header-rows: 1

   * - Type
     - Full name
     - Descriptor
     - Definition / equation
     - Units
     - Method

   * - Molecular
     - Highest occupied molecular orbital energy
     - HOMO
     - :math:`E_{\mathrm{HOMO}}`
     - eV
     - PTB

   * - Molecular
     - Lowest unoccupied molecular orbital energy
     - LUMO
     - :math:`E_{\mathrm{LUMO}}`
     - eV
     - PTB

   * - Molecular
     - HOMO–LUMO gap
     - HOMO–LUMO gap
     - :math:`E_{\text{gap}} = E_{\mathrm{LUMO}} - E_{\mathrm{HOMO}}`
     - eV
     - PTB

   * - Molecular
     - Ionization potential
     - IP
     - :math:`\mathrm{IP} = E(N-1) - E(N)`
     - eV
     - GFN2

   * - Molecular
     - Electron affinity
     - EA
     - :math:`\mathrm{EA} = E(N) - E(N+1)`
     - eV
     - GFN2

   * - Molecular
     - Molecular dipole moment magnitude
     - Dipole module
     - :math:`\text{-}`
     - debye
     - PTB

   * - Molecular
     - Solvent-accessible surface area
     - SASA
     - :math:`\mathrm{SASA} = \sum_i A_i`
     - Å²
     - MORFEUS

   * - Molecular
     - Dispersion surface area
     - Dispersion area
     - :math:`\text{-}`
     - Å²
     - MORFEUS

   * - Molecular
     - Dispersion volume
     - Dispersion volume
     - :math:`\text{-}`
     - Å³
     - MORFEUS

   * - Molecular
     - Solvation free energy in water
     - G solv. in H₂O
     - :math:`\Delta G_{\text{solv}}`
     - kcal/mol
     - GFN2

   * - Molecular
     - Hydrogen-bond contribution to solvation
     - G of H-bonds H₂O
     - :math:`\Delta G_{\text{HB}}`
     - kcal/mol
     - GFN2

   * - Molecular
     - Fermi level
     - Fermi-level
     - :math:`E_F = \dfrac{E_{\mathrm{HOMO}} + E_{\mathrm{LUMO}}}{2}`
     - eV
     - GFN2

   * - Molecular
     - Molecular polarizability
     - Polarizability
     - :math:`\text{-}`
     - a₀³
     - GFN2

   * - Molecular
     - Chemical hardness
     - Hardness
     - :math:`\eta = \mathrm{IP} - \mathrm{EA}`
     - eV
     - GFN2

   * - Molecular
     - Chemical softness
     - Softness
     - :math:`S = \dfrac{1}{\eta}`
     - eV⁻¹
     - GFN2

   * - Molecular
     - Chemical potential
     - Chem. potential
     - :math:`\mu = -\dfrac{\mathrm{IP} + \mathrm{EA}}{2}`
     - eV
     - GFN2

   * - Molecular
     - Electrophilicity index
     - Electrophilicity
     - :math:`\omega = \dfrac{(\mathrm{IP}+\mathrm{EA})^2}{8(\mathrm{IP}-\mathrm{EA})} = \dfrac{\mu^2}{2\eta}`
     - eV
     - GFN2

   * - Molecular
     - Electrofugality
     - Electrofugality
     - :math:`\nu_{\text{electrofugality}} = \dfrac{(3\mathrm{IP}-\mathrm{EA})^2}{8(\mathrm{IP}-\mathrm{EA})} = \mathrm{IP} + \omega`
     - eV
     - GFN2

   * - Molecular
     - Nucleofugality
     - Nucleofugality
     - :math:`\nu_{\text{nucleofugality}} = \dfrac{(\mathrm{IP}-3\mathrm{EA})^2}{8(\mathrm{IP}-\mathrm{EA})} = -\mathrm{EA} + \omega`
     - eV
     - GFN2

   * - Molecular
     - Fractional occupation density
     - Total FOD
     - :math:`\text{-}`
     - e
     - GFN2

   * - Molecular
     - Singlet–triplet energy gap
     - S₀–T₁ gap
     - :math:`\Delta E_{S0\text{-}T1} = E_{T1} - E_{S0}`
     - kcal/mol
     - GFN2

   * - Atomic
     - Atomic hydrogen-bond contribution to solvation
     - H-bond H₂O
     - :math:`\Delta G_{\text{HB},i}`
     - kcal/mol
     - GFN2

   * - Atomic
     - Mulliken partial charge
     - Partial charge
     - :math:`q_i`
     - e
     - PTB

   * - Atomic
     - Atomic dipole moment magnitude
     - Dipole moment
     - :math:`\text{-}`
     - debye
     - PTB

   * - Atomic
     - Atom solvent accessible surface area
     - Atom SASA
     - :math:`A_i`
     - Å²
     - MORFEUS

   * - Atomic
     - Atomic dispersion descriptor
     - Atom dispersion
     - :math:`\text{-}`
     - Å²
     - MORFEUS

   * - Atomic
     - Percent buried volume
     - Buried volume
     - :math:`\text{-}`
     - %
     - MORFEUS

   * - Atomic
     - Pyramidalization parameter
     - Pyramidalization
     - :math:`P = \sin(\theta)·\cos(\alpha)`
     - :math:`\text{-}`
     - MORFEUS

   * - Atomic
     - Pyramidalization angle
     - Pyramidaliz. volume
     - :math:`P = \sqrt{360^\circ - \sum_i \theta_i}`
     - °
     - MORFEUS

   * - Atomic
     - Fukui nucleophilic index
     - Fukui+
     - :math:`f^+ = q_N - q_{N+1}`
     - :math:`\text{-}`
     - GFN2

   * - Atomic
     - Fukui electrophilic index
     - Fukui−
     - :math:`f^- = q_{N-1} - q_N`
     - :math:`\text{-}`
     - GFN2

   * - Atomic
     - Radical Fukui index
     - Fukui_rad
     - :math:`f_{\mathrm{rad}} = \dfrac{q_{N-1} - q_{N+1}}{2}`
     - :math:`\text{-}`
     - GFN2

   * - Atomic
     - Dual Fukui descriptor
     - Fukui dual
     - :math:`f^{(2)} = f^+ - f^-`
     - :math:`\text{-}`
     - GFN2

   * - Atomic
     - Local electrophilicity
     - Electrophil.
     - :math:`l_\omega = -\dfrac{\mu}{\eta} f + \tfrac{1}{2}\dfrac{\mu}{\eta^2} f^{(2)}`
     - :math:`\text{-}`
     - GFN2

   * - Atomic
     - Normalized electrophilicity
     - Normaliz. electrophil.
     - :math:`\omega_i = \omega\ · f_i^+`
     - eV
     - GFN2

   * - Atomic
     - Normalized nucleophilicity
     - Normaliz. nucleophil.
     - :math:`N_i = -\mathrm{IP}\ · f_i^-`
     - eV
     - GFN2

   * - Atomic
     - Atomic polarizability
     - Atom Polarizability
     - :math:`\text{-}`
     - a₀³
     - GFN2

   * - Atomic
     - Atomic FOD population
     - Atom FOD
     - :math:`\text{-}`
     - e
     - GFN2

   * - Atomic
     - Coordination number
     - Coord. numbers
     - :math:`\text{-}`
     - :math:`\text{-}`
     - GFN2

## aqme/docs/Examples/examples_commandline/QM_input_generation/benchmark.rst

.. |QPREP_scheme| image:: ../../images/QPREP_scheme.png
   :width: 500

Benchmarking methods 
====================

In this example we provide the steps needed to use AQME to generate the input 
for different levels of theory and softwares which is a common occurrence in 
method benchmarking.

.. centered:: |QPREP_scheme|

For this example we are going to asume that we have a folder named 'log_files' 
with the .log files shown in the scheme corresponding to gaussian output files 
of optimization and frequency calculations. Our aim is to generate the input 
files on the right hand side of the scheme to run SP calculations. 

First we are going to generate the SP inputs for the wb97xd functional using 
gaussian: 

.. code:: shell

    python -m aqme --qprep --mem 4GB --nprocs 2 --program gaussian --suffix wb97xd --files "log_files/*.log" --qm_input "wb97xd/def2qzvpp scrf=(smd,solvent=acetonitrile)"

Then we proceed to generate the SP inputs for the m062x functional:

.. code:: shell

    python -m aqme --qprep --mem 4GB --nprocs 2 --program gaussian --suffix m062x --files "log_files/*.log" --qm_input "m062x/def2qzvpp emp=gd3 scrf=(smd,solvent=acetonitrile)"

Then we move to the b3lyp functional. 

.. code:: shell

    python -m aqme --qprep --mem 4GB --nprocs 2 --program gaussian --suffix b3lyp --files "log_files/*.log" --qm_input "b3lyp/6-31G*"

And finally we proceed to generate the SP inputs for orca. 

.. code:: shell

   python -m aqme --qprep --mem 4GB --nprocs 2 --program orca --suffix DLPNO --files "log_files/*.log" --qm_input "Extrapolate(2/3,cc) def2/J cc-pVTZ/C DLPNO-CCSD(T) NormalPNO TightSCF RIJCOSX GridX7
   %cpcm
   smd true
   SMDsolvent \"CH2Cl2\"
   end
   %method
   Grid 3
   FinalGrid 5
   end
   %scf maxiter 500
   end
   % mdci
   Density None
   end
   % elprop
   Dipole False
   end"

.. note:: 

   See how to generate the four different inputs we only need to 
   change the :code:`program`, :code:`qm_input` and the :code:`suffix` but most 
   of the command line can be re-used.

## aqme/docs/Examples/examples_commandline/QM_input_generation/gaussian.rst

.. |mol_3d| image:: ../../images/Et_rdkit.png
   :width: 300

Generate Gaussian Inputs
========================

For these examples we are going to assume that we have a folder named 'sdf_files'
that contains a single file 'ethane.sdf' with a single conformer in .sdf format 
whose gaussian input file we want to generate. As you might have guessed in this 
specific example we will be working with Ethane. 

|mol_3d|

The sdf file contents are as follows: 

.. highlight:: none

.. literalinclude:: ../../chemfiles/ethane.sdf

.. highlight:: default

.. note:: 
   
   The following code will also work for multiple conformers and/or molecules. 

.. note:: 

   AQME supports various formats for providing the geometries of the conformers.
   If we want to use a format to specify the molecule that does not contain 
   3D coordinates we will need to generate them beforehand, please see the 
   :doc:`Conformer Search <../conformer_search>` section.

We will be using the QPREP module :code:`--qprep`

We indicate the files whose gaussian input we want :code:`--files "sdf_files/*.sdf"` 

.. warning:: 

   Please notice that shell wildcard arguments need to be provided as strings.
   :code:`--files "sdf_files/*.sdf"` should be provided instead of 
   :code:`--files sdf_files/*.sdf`. This feature might change in future to 
   follow the usual conventions. 

We include the suffix that will be appended to the base name of the files 
:code:`--suffix "wb97xd-basic"`

We indicate the details of the gaussian calculation 
:code:`--qm_input "wb97xd/def2qzvpp scrf=(smd,solvent=acetonitrile)"`

And the number of processors :code:`--nprocs 8` and memory :code:`--mem 16GB` for
the gaussian calculations. 

Our final command will now look like this: 

.. code:: shell

   python -m aqme --qprep --files "sdf_files/*.sdf" --qm_input "wb97xd/def2qzvpp scrf=(smd,solvent=acetonitrile)" --suffix wb97xd-basic --program gaussian --mem 16GB --nprocs 8

With this we have generated a new folder named QCALC that contains the file 
'ethane_conf_1_wb97xd-basic.com' with the following contents:

.. highlight:: none 

.. literalinclude:: ../../chemfiles/ethane_basic.com

.. highlight:: default
   

Enforce Charge and Multiplicity
-------------------------------

If we had wanted to specify the charge and multiplicity we just need to add the 
appropriate keywords :code:`--charge 0 --mult 3`. 

Leading to the full command line (note that we have changed the suffix so the 
file name that we will generate will be different)

.. code:: shell

   python -m aqme --qprep --suffix wb97xd-triplet --charge 0 --mult 3 --files "sdf_files/*.sdf" --qm_input "wb97xd/def2qzvpp scrf=(smd,solvent=acetonitrile)" --program gaussian --mem 16GB --nprocs 8

Which will create the file 'ethane_conf_1_wb97xd-triplet.com' with the
following contents: 

.. highlight:: none

.. literalinclude:: ../../chemfiles/ethane_ch_mult.com

.. highlight:: default

Include the gen or genecp section
---------------------------------

If we want to include a genecp with automatic detection of the atoms in the 
molecule we have to add some extra keywords:

We need to specify the atoms whose ECP we are setting :code:`--gen_atoms "['C']"`

As well as the ECP :code:`--bs_gen def2svp`

The basis set for the atoms that will not use the ECP :code:`--bs_nogen "6-31G*"`

Finally we need to also substitute the basis set by ``genecp`` in the qm_input 
parameter :code:`--qm_input "wb97xd/genecp scrf=(smd,solvent=acetonitrile)"`

And we end up with the following command line: 

.. code:: shell

   python -m aqme --qprep --suffix "wb97xd-genecp" --gen_atoms "['C']" --bs_gen def2svp --bs_nogen "6-31G*" --files "sdf_files/*.sdf" --qm_input "wb97xd/genecp scrf=(smd,solvent=acetonitrile)" --program gaussian --mem 16GB --nprocs 8

Which will lead to the creation of the file 'ethane_conf_1_wb97xd-genecp.com' with the
following contents: 

.. highlight:: none

.. literalinclude:: ../../chemfiles/ethane_genecp.com

.. highlight:: default

If we instead do not want to include the ECP section, or in other words we want 
to use the ``gen`` instead of ``genecp`` we only need to substitute it in the 
``qm_input`` parameter. AQME will automatically recognize it and write 
the input file accordingly: 

.. code:: shell

   python -m aqme --qprep --suffix "wb97xd-gen" --gen_atoms "['C']" --bs_gen def2svp --bs_nogen "6-31G*" --files "sdf_files/*.sdf" --qm_input "wb97xd/gen scrf=(smd,solvent=acetonitrile)" --program gaussian --mem 16GB --nprocs 8

Which will lead to the creation of the file 'ethane_conf_1_wb97xd-gen.com' with the
following contents: 

.. highlight:: none

.. literalinclude:: ../../chemfiles/ethane_gen.com

.. highlight:: default

Include instructions after the geometry section
-----------------------------------------------

Finally if we want to specify some extra instructions after the geometry which 
are required for some commands such as the modredundant optimization option or 
for nbo6 calculations. Here we use the NBO as an example. 

We will only need to add a single extra command to include such instructions 
:code:`--qm_end "$nbo bndidx $end"` 

.. warning:: 

   In linux-based systems the :code:`$` needs to be escaped so the previous 
   option would need to be typed as :code:`--qm_end "\$nbo bndidx \$end"` 
   instead.  

But as we are using an NBO calculation as example we also need to use a gaussian
command line that is appropriate for the calculation 
:code:`--qm_input "pop=(nbo6read,savenbos) wb97xd/def2svp"`

Our final command line will look like: 

.. code:: shell

   python -m aqme --qprep --suffix wb97xd-nbo --qm_end "$nbo bndidx $end" --qm_input "pop=(nbo6read,savenbos) wb97xd/def2svp" --files "sdf_files/*.sdf"  --program gaussian --mem 16GB --nprocs 8

Which will lead to the creation of the file 'ethane_conf_1_wb97xd-nbo.com' with the
following contents: 

.. highlight:: none

.. literalinclude:: ../../chemfiles/ethane_nbo.com

.. highlight:: default

## aqme/docs/Examples/examples_commandline/QM_input_generation/orca.rst

.. |mol_3d| image:: ../../images/Et_rdkit.png
   :width: 300

Generate ORCA Inputs
====================

For these examples we are going to assume that we have a folder named 'sdf_files'
that contains a single file 'ethane.sdf' with a single conformer in .sdf format 
whose ORCA input file we want to generate. As you might have guessed in this 
specific example we will be working with Ethane. 

|mol_3d|

The sdf file contents are as follows: 

.. highlight:: none

.. literalinclude:: ../../chemfiles/ethane.sdf

.. highlight:: default

.. note:: 
   
   The following code will also work for multiple conformers and/or molecules. 

.. note:: 

   AQME supports various formats for providing the geometries of the conformers.
   If we want to use a format to specify the molecule that does not contain 
   3D coordinates we will need to generate them beforehand, please see the 
   :doc:`Conformer Search <../conformer_search>` section.

As we will be generating qm inputs we will use the :code:`--qprep` module. 

We include the suffix that we want to append to the base name of the generated
files :code:`--suffix m06-basic`

We specify the files whose ORCA input we want :code:`--files "sdf_files/*.sdf"`

We include the number of processors :code:`--nprocs 8` and memory 
:code:`--mem 16GB` for the calculations 

And we specify the command line of the ORCA calculation: 

.. code:: shell 

   --qm_input "m06 def2qzvpp
    %cpcm
    smd true
    SMDsolvent \"CH2Cl2\"
    end"

.. note:: 

   the \"CH2Cl2\" in this case will ensure that the generated file contains :code:`"CH2Cl2"`

Our final command line will look like: 

.. code:: shell 

   python -m aqme --qprep --program orca --suffix "m06-basic" --files "sdf_files/*.sdf" --nprocs 8 --mem 16GB --qm_input "m06 def2qzvpp
   %cpcm
   smd true
   SMDsolvent \"CH2Cl2\"
   end"

With this we have generated a new folder named QCALC that contains the file 
'ethane_conf_1_m06-basic.inp' with the following contents:

.. highlight:: none

.. literalinclude:: ../../chemfiles/ethane_basic.inp

.. highlight:: default

Enforce Charge and Multiplicity
-------------------------------

If we had wanted to specify the charge and multiplicity we just need to add the 
appropriate keywords. 

.. code:: shell 

   python -m aqme --qprep --program orca --charge 0 --mult 3 --suffix "m06-triplet" --files "sdf_files/*.sdf" --nprocs 8 --mem 16GB --qm_input "m06 def2qzvpp
   %cpcm
   smd true
   SMDsolvent \"CH2Cl2\"
   end"

Will lead to the creation of the file 'ethane_conf_1_wb97xd-triplet.com' with the
following contents: 

.. highlight:: none

.. literalinclude:: ../../chemfiles/ethane_triplet.inp

.. highlight:: default

## aqme/docs/Examples/examples_commandline/conformer_search.rst

====================
Conformer Generation
====================

.. toctree::
    :maxdepth: 1

    conformer_search/organic_molecule
    conformer_search/noncovalent_minima
    conformer_search/noncovalent_TS
    conformer_search/metal_complex

## aqme/docs/Examples/examples_commandline/conformer_search/metal_complex.rst

.. |metal_comp_chemdraw| image:: ../../images/metal_comp_chemdraw.png
   :width: 300

.. |metal_comp_3D| image:: ../../images/metal_comp_3D.png
   :width: 400

Metal complex from SMILES input
===============================

In the following example we will generate various conformers of a 
Pd complex using RDKit using a template for square planar complexes.

+-----------------------------------------------+
| .. centered:: **SMILES**                      |
+-----------------------------------------------+
| .. centered:: I[Pd]([PH3+])(F)Cl              |
+--------------------------+--------------------+
|  |metal_comp_chemdraw|   |  |metal_comp_3D|   |
+--------------------------+--------------------+

We can also specify multiplicity :code:`--mult 1` and charge :code:`--charge -1`

We also need to specify which template geometry to use for the complex 
:code:`--complex_type squareplanar`

We specify the output directory where the sdf with conformations will be 
generated :code:`--destination Pd_sdf_files` and the base name of the file
:code:`--name Pd_complex`

We provide the smiles string of the molecule :code:`--smi "I[Pd]([PH3+])(F)Cl"`

And we need to specify that we will be using the CSEARCH module with rdkit to 
generate the conformers :code:`--csearch --program rdkit`

The full command that we will execute will look as follows:

.. code:: shell

   python -m aqme --csearch --smi "I[Pd]([PH3+])(F)Cl" --destination Pd_sdf_files --name Pd_complex --program rdkit --charge -1 --mult 1 --complex_type squareplanar

## aqme/docs/Examples/examples_commandline/conformer_search/noncovalent_TS.rst

.. |nocov_ts_chemdraw| image:: ../../images/nocov_ts_chem.png
   :width: 400

.. |nocov_ts_3D| image:: ../../images/nocov_ts_3D.png
   :width: 400

.. |mapping| image:: ../../images/nocov_ts_map.png
   :width: 400

SN2 TS generated from SMILES
============================

In the following example we will generate conformers of the SN2 transition state 
involving a cloride ion and fluoromethane in water. 

+-----------------------------------------------+
| .. centered:: **SMILES**                      |
+-----------------------------------------------+
| .. centered::   FC.[Cl-]                      |
+--------------------------+--------------------+
|  |nocov_ts_chemdraw|     |  |nocov_ts_3D|     |
+--------------------------+--------------------+

In the following example we need a mapped SMILES to set up the constraints. We 
can either use rdkit for it in python, in a jupyter notebook (see 
:doc:`python example <../../examples_python/conformer_search/noncovalent_TS>` )
or we can write the SMILES by ourselves (not recommended). 

The mapped smiles that we will be using is the following one: 

|mapping|

:: 

   [Cl-:3].[F:1][C:2]([H:4])([H:5])[H:6]

Now that we have the mapping, we can easily proceed to set up the constraints.
In this case we want the C-F and the Cl-C bond distances to be constrained and 
equal to 1.8 angstroms and we want the angle Cl-C-F to be of 180º. 

As a consequence the distance constraints will be :code:`"[[1,2,1.8],[2,3,1.8]]"`
and the angle constrains :code:`"[[1,2,3,180]]"`

Finally we proceed to the conformer generation using CREST

.. code:: shell

   python -m aqme --csearch --name "TS-example" --nprocs 12 --program crest --cregen --crest_keywords "--alpb h2o" --xtb_keywords "--alpb h2o" --constraints_dist "[[1,2,1.8],[2,3,1.8]]" --constraints_angle "[[1,2,3,180]]" --smi "[Cl-:3].[F:1][C:2]([H:4])([H:5])[H:6]"

## aqme/docs/Examples/examples_commandline/conformer_search/noncovalent_minima.rst

.. |nocov_bimol_chemdraw| image:: ../../images/nocov_bimol_chem.png
   :width: 400

.. |nocov_bimol_3D| image:: ../../images/nocov_bimol_3D.png
   :width: 400

Noncovalent bimolecular complex generated from SMILES
=====================================================

In the following example we will generate conformers of the 
isopentane-water complex using CREST

+-----------------------------------------------+
| .. centered:: **SMILES**                      |
+-----------------------------------------------+
| .. centered:: CCC(C)C.O                       |
+--------------------------+--------------------+
|  |nocov_bimol_chemdraw|  |  |nocov_bimol_3D|  |
+--------------------------+--------------------+

Compared with the :doc:`organic molecule example <organic_molecule>` this time 
we are going to use the default location for the output file. As a consequence
we can now proceed to run the conformer search from the smiles string:

.. code:: shell

   python -m aqme --csearch --smi "CCC(C)C.O" --name "isopent-water-complex" --program crest --crest_keywords "--nci" --cregen --cregen_keywords "--ewin 3" --nprocs 12

## aqme/docs/Examples/examples_commandline/conformer_search/organic_molecule.rst

.. |quinine_chemdraw| image:: ../../images/Quinine_chemdraw.png
   :width: 400

.. |quinine_3D| image:: ../../images/Quinine-3D-balls.png
   :width: 400

Organic Molecule generated from SMILES
======================================

In the following examples we will be generating conformations of the 
quinine molecule. 

+------------------------------------------------------------------------------+
|                         .. centered:: **SMILES**                             |
+------------------------------------------------------------------------------+
| .. centered:: COC1=CC2=C(C=CN=C2C=C1)[C@H]([C@@H]3C[C@@H]4CCN3C[C@@H]4C=C)O  |
+----------------------------------------+-------------------------------------+
|          |quinine_chemdraw|            |              |quinine_3D|           |
+----------------------------------------+-------------------------------------+

Conformer Generation
--------------------

.. code :: shell

    python -m aqme --csearch --smi "COC1=CC2=C(C=CN=C2C=C1)[C@H]([C@@H]3C[C@@H]4CCN3C[C@@H]4C=C)O" --destination quinine_folder --name quinine --program rdkit

Here we are specifying that we want to use rdkit for the conformer generation 
when we specify program='rdkit' and we are specifying the base name of the output 
files to be 'quinine'. 

At this point we will have a new folder already created named 'quinine_folder' 
that contains a file named quinine_rdkit.sdf that contains all the conformers
generated. 

Minimizing the conformations
----------------------------

Back to our conformers generated using rdkit we might be interested in running 
an energy minization using XTB or ANI. To do so we will need the CMIN module. 

.. code:: shell

   python -m aqme --cmin --files "quinine_folder/*.sdf" --program ani --destination quinine_ani

Here 'destination' is the folder where the new optimized geometries will be 
generated, 'files' is a list of files that we want to minimize and 'program'
is specifying that we want to run the minimizations using 'ani'. 

.. warning:: 

   Please notice that shell wildcard arguments need to be provided as strings.
   :code:`--files "quinine_folder/*.sdf"` should be provided instead of 
   :code:`--files quinine_folder/*.sdf`. This feature might change in future to 
   follow the usual conventions. 

Using csv files as input
------------------------

Another way of providing the molecule to the program is by writing it into a csv
file. Lets asume we have in our working directory the file 'ML_test.csv' with the 
following contents: 

.. highlight:: none

::

   code_name,SMILES
   quinine,COC1=CC2=C(C=CN=C2C=C1)[C@H]([C@@H]3C[C@@H]4CCN3C[C@@H]4C=C)O

.. highlight:: default

With this file we can run the same conformer search that we run at the beggining
with the following code: 

.. code:: shell

   python -m aqme --csearch --input ML_test.csv --program rdkit --destination quinine_folder

Using csv files allows specifying multiple molecules by their SMILES string in a
single file and facilitates the reusability of the code. If we change the 
contents of 'ML_test.csv' to: 

.. highlight:: none

:: 

   code_name,SMILES
   methane,C
   ethane,CC
   propane,CCC
   butane,CCCC
   pentane,CCCCC

.. highlight:: default

We can re-run the exact same code, and we will end with the conformers of each 
one of these molecules in the same directory. If we want to have them in a 
different folder we can simply change the destination: 

.. code:: shell

   python -m aqme --csearch --input ML_test.csv --program rdkit --destination alkanes_folder

## aqme/docs/Examples/examples_commandline/correction_qm_output.rst

=======================
Correction of QM Output
=======================

Analyzing the output files
--------------------------

For these tasks we will be using the QCORR module :code:`--qcorr`

Then we list the files that we want to analyze. In this case we are going to 
analyze Gaussian16 output files. We are going to assume that we have our 
files in the folder 'calculations' therefore :code:`--files "calculations/*.log"`

.. warning:: 

   Please notice that shell wildcard arguments need to be provided as strings.
   :code:`--files "calculations/*.sdf"` should be provided instead of 
   :code:`--files calculations/*.sdf`. This feature might change in future to 
   follow the usual conventions. 

We can specify the :code:`--freq_conv "opt=(calcfc,maxstep=5)"` which will 
attempt to fix calculations whose optimization ended normally but whose 
frequency calculation did not. 

Finally we run the analysis of the files.

.. code:: shell 

   python -m aqme --qcorr --files "calculations/*.log"

Optionally we may indicate the extension of the initial input files 
:code:`--isom_type com` as well as the folder where those files are 
:code:`--isom_inputs folder`. 

.. code:: shell 

   python -m aqme --qcorr --files "calculations/*.log" --isom_type com --isom_inputs folder 

If we instead wanted to skip the checks and generate the .json files containing 
information about our calculations we can use the :code:`--fullcheck False` keyword.

.. code:: shell 

   python -m aqme --qcorr --fullcheck False --files "calculations/*.log"

## aqme/docs/Examples/examples_commandline/descriptor_generation.rst

=====================
Descriptor Generation
=====================

.. tabs::

   .. tab:: 1. Organics

      .. tabs::

         .. tab:: 1.1. Basic

            **Input CSV:**

            +---------+-----------+
            | SMILES  | code_name |
            +=========+===========+
            | C       | mol_1     |
            +---------+-----------+
            | CC      | mol_2     |
            +---------+-----------+
            | CCC     | mol_3     |
            +---------+-----------+
            | CCCC    | mol_4     |
            +---------+-----------+

            **Command line:**

            .. code:: console

               python -m aqme --qdescp --input FILENAME.csv

            **Outputs:**

            - CSV files with descriptors (standard: ``AQME-ROBERT_interpret_FILENAME.csv``)
            - No common substructure → only molecular descriptors generated

         .. tab:: 1.2. Auto detection of common substructure

            **Input CSV:**

            +---------+-----------+
            | SMILES  | code_name |
            +=========+===========+
            | P       | mol_1     |
            +---------+-----------+
            | PC      | mol_2     |
            +---------+-----------+
            | P(C)C   | mol_3     |
            +---------+-----------+
            | P(C)(C)C| mol_4     |
            +---------+-----------+

            **Command line:**

            .. code:: console

               python -m aqme --qdescp --input FILENAME.csv

            **Outputs:**

            - CSV files with descriptors
            - Common substructure detected (P atom)
            - Molecular and atomic descriptors generated

         .. tab:: 1.3. Custom SMARTS for atomic descriptors

            **Input CSV:**

            +-----------+-----------+
            | SMILES    | code_name |
            +===========+===========+
            | C(O)N     | mol_1     |
            +-----------+-----------+
            | CC(O)N    | mol_2     |
            +-----------+-----------+
            | CCC(O)N   | mol_3     |
            +-----------+-----------+
            | CCCC(O)N  | mol_4     |
            +-----------+-----------+

            **Command line:**

            .. code:: console

               python -m aqme --qdescp --input FILENAME.csv --qdescp_atoms "['O']"

            **Outputs:**

            - Only O atoms used for atomic descriptors
            - Molecular descriptors always included

            .. note::

               Other SMARTS patterns can be used (e.g., ``C=O``, ``C#N``). The pattern must appear once in all molecules.

         .. tab:: 1.4. Atom indices for atomic descriptors

            **Input CSV:**

            +--------------------------------+-----------+
            | SMILES                         | code_name |
            +================================+===========+
            | [P:1]([H])([H])([H])           | mol_1     |
            +--------------------------------+-----------+
            | [P:1]([H])([H])C               | mol_2     |
            +--------------------------------+-----------+
            | [P:1]([H])(C)C                 | mol_3     |
            +--------------------------------+-----------+
            | [P:1](C)(C)C                   | mol_4     |
            +--------------------------------+-----------+

            **Command line:**

            .. code:: console

               python -m aqme --qdescp --input FILENAME.csv --qdescp_atoms "['1']"

            **Outputs:**

            - Descriptors only for atoms labeled with index ``1``
            - Molecular descriptors always included

         .. tab:: 1.5. Combining sets of two molecules

            **Input CSV:**

            +-----------+------------------+-----------------+
            | code_name | SMILES_phosph    | SMILES_alk      |
            +===========+==================+=================+
            | mol_1     | P                | C               |
            +-----------+------------------+-----------------+
            | mol_2     | PC               | CC              |
            +-----------+------------------+-----------------+
            | mol_3     | P(C)C            | CCC             |
            +-----------+------------------+-----------------+
            | mol_4     | P(C)(C)C         | CCCC            |
            +-----------+------------------+-----------------+

            **Command line:**

            .. code:: console

               python -m aqme --qdescp --input FILENAME.csv

            **Outputs:**

            - Descriptors generated independently for each component and combined into a single descriptor array

   .. tab:: 2. Metal complexes

      .. tabs::

         .. tab:: 2.1. Basic

            **Input CSV:**

            +-----------+------------------------------------------------------+--------+------+
            | code_name | SMILES                                               | charge | mult |
            +===========+======================================================+========+======+
            | mol_1     | [H][N+]1([H])[Cu][N+]([H])([H])CC1                   | 2      | 2    |
            +-----------+------------------------------------------------------+--------+------+
            | mol_2     | [H][N+]1([H])[Cu]N([H])CC1                           | 1      | 2    |
            +-----------+------------------------------------------------------+--------+------+
            | mol_3     | [H]N1[Cu]N([H])CC1                                   | 0      | 2    |
            +-----------+------------------------------------------------------+--------+------+
            | mol_4     | C[N+]1(C)[Cu][N+](C)(C)C=C1                          | 2      | 2    |
            +-----------+------------------------------------------------------+--------+------+

            **Command line:**

            .. code:: console

               python -m aqme --qdescp --input FILENAME.csv

            **Outputs:**

            - Atomic descriptors for Cu automatically generated
            - Molecular descriptors always included
            - Charges and multiplicity required

         .. tab:: 2.2. Forcing squareplanar geometry

            **Input CSV:**

            +-----------+------------------------------------------------+--------+------+----------------+--------------------------------------+
            | code_name | SMILES                                         | charge | mult | complex_type   | geom                                 |
            +===========+================================================+========+======+================+======================================+
            | mol_1     | Cl[Pd]([PH3+])(Cl)[NH3+]                       | 0      | 1    | squareplanar   | "['[Cl][Pd][Cl]',180]"               |
            +-----------+------------------------------------------------+--------+------+----------------+--------------------------------------+
            | mol_2     | Cl[Pd](Cl)([P+](C)(C)C)[NH3+]                  | 0      | 1    | squareplanar   | "['[Cl][Pd][Cl]',180]"               |
            +-----------+------------------------------------------------+--------+------+----------------+--------------------------------------+
            | mol_3     | Cl[Pd]([PH3+])(Cl)[N+](C)(C)C                  | 0      | 1    | squareplanar   | "['[Cl][Pd][Cl]',180]"               |
            +-----------+------------------------------------------------+--------+------+----------------+--------------------------------------+
            | mol_4     | Cl[Pd](Cl)([P+](C)(C)C)[N+](C)(C)C             | 0      | 1    | squareplanar   | "['[Cl][Pd][Cl]',180]"               |
            +-----------+------------------------------------------------+--------+------+----------------+--------------------------------------+

            **Command line:**

            .. code:: console

               python -m aqme --qdescp --input FILENAME.csv

            **Outputs:**

            - Atomic descriptors for Pd, N and P (detected automatically)
            - Molecular descriptors always included
            - Charges and multiplicity required
            - Squareplanar geometry enforced via the ``complex_type`` column
            - Two chloride ligands in trans (Cl-Pd-Cl angle at 180 degrees) enforced via the ``geom`` column

         .. tab:: 2.3. Custom SMARTS for atomic descriptors

            **Input CSV:**

            +-----------+---------------------------------------------+--------+------+
            | code_name | SMILES                                      | charge | mult |
            +===========+=============================================+========+======+
            | mol_1     | O=CC1=CN(C)[Cu]N1C                          | 0      | 2    |
            +-----------+---------------------------------------------+--------+------+
            | mol_2     | O=CC1=C(C)N(C)[Cu]N1C                       | 0      | 2    |
            +-----------+---------------------------------------------+--------+------+
            | mol_3     | O=CC1=C(N([Cu]N1C(C)(C)C)C)C                | 0      | 2    |
            +-----------+---------------------------------------------+--------+------+
            | mol_4     | O=C(C)C1=C(C)N([Cu]N1C)C                    | 0      | 2    |
            +-----------+---------------------------------------------+--------+------+

            **Command line:**

            .. code:: console

               python -m aqme --qdescp --input FILENAME.csv --qdescp_atoms "['C=O']"

            **Outputs:**

            - Atomic descriptors only for C and O atoms from carbonyl groups
            - Molecular descriptors always included

         .. tab:: 2.4. Atom indices for atomic descriptors

            **Input CSV:**

            +-----------+--------------------------------------------------------------+--------+------+
            | code_name | SMILES                                                       | charge | mult |
            +===========+==============================================================+========+======+
            | mol_1     | [H][N+]1([Cu][N:1](C=C1)[H])[H]                              | 1      | 2    |
            +-----------+--------------------------------------------------------------+--------+------+
            | mol_2     | [H][N+]1([H])[Cu][N:1]([H])CC1                               | 1      | 2    |
            +-----------+--------------------------------------------------------------+--------+------+
            | mol_3     | [H][N+]1([Cu][N:1](C(C)=C1)[H])[H]                           | 1      | 2    |
            +-----------+--------------------------------------------------------------+--------+------+
            | mol_4     | [H][N+]1([Cu][N:1](C(C)=C1C)[H])[H]                          | 1      | 2    |
            +-----------+--------------------------------------------------------------+--------+------+

            **Command line:**

            .. code:: console

               python -m aqme --qdescp --input FILENAME.csv --qdescp_atoms "['1']"

            **Outputs:**

            - Atomic descriptors only for indexed atoms
            - Molecular descriptors always included

   .. tab:: 3. From SDF/XYZ

      **Command line:**

      .. code:: console

         python -m aqme --qdescp --files "*.sdf"

      **Outputs:**

      - CSV descriptor files generated from 3D structures

      .. note::

         Useful when SMILES are not suitable (e.g., axial chirality or noncovalent complexes).

## aqme/docs/Examples/examples_commandline/end_to_end/example_1.rst

.. |Strychnine| image:: ../../images/strychnine_chemdraw.png
   :width: 400

Strychnine
==========

Along the steps of this example workflow we will show how to: 

i)   Generate different conformers of the molecule using CSEARCH
ii)  Generate the inputs for the QM geometry optimization
iii) Fix error terminations and imaginary frequencies of the output files
iv)  Calculation and analyze the NMR chemical shifts for the conformers
     generated.
v)   Use GoodVibes to calculate the Boltzmann distributions using Gibbs free
     energies at 298.15 K

Specifically, in this example we will calculate the NMR chemical shifts of the strychnine
starting from the smiles representation of said molecule that we can see below. 

+---------------------------------------------------------------------------------------+
|                         .. centered:: **SMILES**                                      |
+---------------------------------------------------------------------------------------+
| .. centered:: C1CN2CC3=CCO[C@H]4CC(=O)N5[C@H]6[C@H]4[C@H]3C[C@H]2[C@@]61C7=CC=CC=C75  |
+---------------------------------------------------------------------------------------+
|                      .. centered::  |Strychnine|                                      |
+---------------------------------------------------------------------------------------+

.. note::

   A jupyter notebook containing all the steps shown in this example can be found 
   in the AQME repository in `Github  <https://github.com/jvalegre/aqme>`__ or in 
   `Figshare <https://figshare.com/articles/dataset/AQME_paper_examples/20043665>`__

.. note:: 

   A video tutorial illustrating this example can be found 
   in our `youtube channel <https://www.youtube.com/watch?v=d4mQoE8gPJw>`__

.. contents:: Steps
   :local:

Step 1: CSEARCH conformational sampling
---------------------------------------

.. code:: shell

   python -m aqme --csearch --program rdkit --destination Strychnine_sdf_files --name Strychnine --smi "C1CN2CC3=CCO[C@H]4CC(=O)N5[C@H]6[C@H]4[C@H]3C[C@H]2[C@@]61C7=CC=CC=C75"

Step 2: Creating Gaussian input files for optimization and frequency with QPREP
-------------------------------------------------------------------------------

.. code:: shell

   python -m aqme --qprep --destination Strychnine_com_files --files "Strychnine_sdf_files/*.sdf" --program gaussian --qm_input "B3LYP/6-31+G(d,p) opt freq" --mem 24GB --nprocs 12

Step 3: Running Gaussian inputs for optimization and frequency calcs externally
-------------------------------------------------------------------------------

Now that we have generated our gaussian input files (in the com_path location 
of Step 2) we need to run the gaussian calculations. If you do not know how to 
run the Gaussian calculations in your HPC please refer to your HPC manager. 

As an example, for a single calculation in Gaussian 16 through the terminal we 
would run the following command on a Linux-based system: 

.. code:: shell

    g16 myfile.com

Step 4: QCORR analysis including isomerization filter
-----------------------------------------------------

.. code:: shell 

   python -m aqme --qcorr --files "Strychnine_com_files/*.log" --freq_conv "opt=(calcfc,maxstep=5)" --isom_type com --isom_inputs Strychnine_com_files --nprocs 12 --mem 24GB

Step 5: Resubmission of unsuccessful calculations (if any) with suggestions from AQME
-------------------------------------------------------------------------------------

Now we need to run the generated COM files (in fixed_QM_inputs) with Gaussian 
like we did in Step 3.

After the calculations finish we check again the files using QCORR

.. code:: shell

   python -m aqme --qcorr --files "Strychnine_com_files/failed/run_1/fixed_QM_inputs/*.log" --isom_type com --isom_inputs "Strychnine_com_files/failed/run_1/fixed_QM_inputs" --nprocs 12 --mem 24GB

Step 6: Creating Gaussian input files for NMR calcs with QPREP
--------------------------------------------------------------

.. code:: shell

   python -m aqme --qprep --w_dir_main "Strychnine_com_files/success" --program gaussian --mem 24GB --nprocs 12 --suffix SP --destination Strychnine_sp_files --files "Strychnine_com_files/success/*.log" --qm_input "B3LYP/6-311+G(2d,p) scrf=(solvent=chloroform,smd) nmr=giao" 

Step 7: Running Gaussian NMR calcs
----------------------------------

Now we need to run the generated COM files (in sp_path) with Gaussian 
like we did in Step 3

After the calculations end, we create JSON files with QCORR to store the 
information from the resulting LOG files

.. code:: shell

   python -m aqme --qcorr --files "Strychnine_sp_files/*.log"

Step 8: Obtaining Boltzmann weighted NMR shifts with QDESCP
-----------------------------------------------------------

.. code:: shell 

   python -m aqme --qdescp --program nmr --destination Strychnine_nmr_files --nmr_slope "[-1.0537, -1.0784]" --nmr_intercept "[181.7815,31.8723]" --nmr_experim Experimental_NMR_shifts.csv --files "Strychnine_sp_files/success/SP_calcs/json_files/*.json"

Step 9: Calculating conformer populations with GoodVibes
--------------------------------------------------------

.. code:: shell 

   mkdir -p Strychine_GoodVibes-analysis
   cp Strychnine_com_files/success/*.log Strychine_GoodVibes-analysis/
   cp Strychnine_sp_files/success/SP_calcs/*.log Strychine_GoodVibes-analysis/
   cd Strychine_GoodVibes-analysis
   python -m goodvibes --xyz -c 1 *.log --boltz --spc SP
   cd ..

## aqme/docs/Examples/examples_commandline/end_to_end/example_2.rst

.. |pair_1| image:: ../../images/diels_alder_1.png
   :width: 300

.. |pair_1_map| image:: ../../images/diels_alder_1_map.png
   :width: 300

.. |pair_2| image:: ../../images/diels_alder_2.png
   :width: 300

.. |pair_2_map| image:: ../../images/diels_alder_2_map.png
   :width: 300

.. |pair_3| image:: ../../images/diels_alder_3.png
   :width: 300

.. |pair_3_map| image:: ../../images/diels_alder_3_map.png
   :width: 300

.. |profile| image:: ../../images/diels_alder_profile.png
   :width: 500

Diels-Alder reactions
=====================

Along the steps of this example workflow we will show how to: 

i)   Generate different conformers of molecules and noncovalent complexes using CREST
ii)  Generate the inputs for Gaussian geometry optimizations and frequency calcs
     (B3LYP/def2TZVP)
iii) Fixing errors and imaginary frequencies of the output LOG files
iv)  Generate ORCA inputs for single-point energy corrections (SPC) using
     DLPNO-CCSD(T)/def2TZVPP
v)   Calculate the Boltzmann weighted thermochemistry using with GoodVibes at
     298.15 K

Specifially in this workflow we will calculate the free energy profile 
for the Diels-Alder reaction for three pairs of reactants shown below:

+--------------------------------+---------------------------------+----------------------------------+
| .. centered:: **Reactants 1**  | .. centered:: **Reactants 2**   | .. centered:: **Reactants 3**    |
+--------------------------------+---------------------------------+----------------------------------+
| .. centered:: C1=CC=CC1.C1=CC1 | .. centered:: C1=CC=CC1.C1=CCC1 | .. centered:: C1=CC=CC1.C1=CCCC1 |
+--------------------------------+---------------------------------+----------------------------------+
| .. centered::  |pair_1|        | .. centered::  |pair_2|         | .. centered::  |pair_3|          |
+--------------------------------+---------------------------------+----------------------------------+

.. note::

   A jupyter notebook containing all the steps shown in this example can be found 
   in the AQME repository in `Github  <https://github.com/jvalegre/aqme>`__ or in 
   `Figshare <https://figshare.com/articles/dataset/AQME_paper_examples/20043665>`__

.. contents:: Steps
   :local:

Step 1: Determining distance and angle constraints for TSs
----------------------------------------------------------

In the following examples we need the mapped SMILES to set up the constraints. We 
can either use rdkit for it in python, in a jupyter notebook (see 
:doc:`python example <../../examples_python/end_to_end/example_2>` )
or we can write the SMILES by ourselves (not recommended). 

We visualize the first pair of reactants to be able to set up the constraints.

.. centered::  |pair_1_map|

:: 

   C1([H:8])=[C:1]([H:9])[C:2]([H:10])=[C:3]([H:11])[C:4]1([H:12])[H:13].[C:5]1([H:14])=[C:6]([H:15])[C:7]1([H:16])[H:17]

According to the image we will add the following constraints to the CSV, in the 
constraints_dist column we will include :code:`[[3,5,2.35],[0,6,2.35]]`

We visualize the second pair of reactants to be able to set up the constraints. 

.. centered::  |pair_2_map|

:: 

   C1([H:9])=[C:1]([H:10])[C:2]([H:11])=[C:3]([H:12])[C:4]1([H:13])[H:14].[C:5]1([H:15])=[C:6]([H:16])[C:7]([H:17])([H:18])[C:8]1([H:19])[H:20]

According to the image we will add the following constraints to the CSV, in the 
constraints_dist column we will include :code:`[[3,6,2.35],[0,5,2.35]]`

.. warning:: 

   Although the atoms 5 and 6 are equivalent, we have observed that if we use 
   the same ordering as in the previous reaction for the constraints the TS 
   won't be found (i.e. with :code:`[[3,5,2.35],[0,6,2.35]]`) whereas when we 
   use the constraints as shown in the example the TS is found. 

We visualize the third pair of reactants to be able to set up the constraints. 

.. centered:: |pair_3_map|

:: 

   C1([H:10])=[C:1]([H:11])[C:2]([H:12])=[C:3]([H:13])[C:4]1([H:14])[H:15].[C:5]1([H:16])=[C:6]([H:17])[C:7]([H:18])([H:19])[C:8]([H:20])([H:21])[C:9]1([H:22])[H:23]

According to the image we will add the following constraints to the CSV, in the 
constraints_dist column we will include :code:`[[3,5,2.35],[0,6,2.35]]`

Step 2: CSEARCH conformational sampling
---------------------------------------

With the previous step we can now create a csv file containing all the molecules
and noncovalent complexes to calculate, which will have the following contents: 

.. highlight:: none

.. literalinclude:: ../../chemfiles/end_to_end_2_inp.csv

.. highlight:: default

Now we can proceed to the conformer generation:

.. code:: shell 

   python -m aqme --csearch --input example2.csv --program crest --cregen --cregen_keywords "--ethr 0.1 --rthr 0.2 --bthr 0.3 --ewin 1" --nprocs 12

Step 3: Creating Gaussian input files for optimization and frequency with QPREP
-------------------------------------------------------------------------------

We first create the input files of the transition states

.. code:: shell 

   python -m aqme --qprep --program gaussian --mem 32GB --nprocs 16 --files "CSEARCH/TS*crest.sdf" --qm_input "B3LYP/def2tzvp opt=(ts,calcfc,noeigen,maxstep=5) freq=noraman"

Now we create the input files of the minima (intermediates, reagents and products) 

.. code:: shell 

   python -m aqme --qprep --program gaussian --mem 32GB --nprocs 16 --files "CSEARCH/D*.sdf" --qm_input "B3LYP/def2tzvp opt freq=noraman"
   python -m aqme --qprep --program gaussian --mem 32GB --nprocs 16 --files "CSEARCH/P*.sdf" --qm_input "B3LYP/def2tzvp opt freq=noraman"

Step 4: Running Gaussian inputs for optimization and frequency calcs externally
-------------------------------------------------------------------------------

Now that we have generated our gaussian input files (in the QCALC location 
of Step 3) we need to run the gaussian calculations. If you do not know how to 
run the Gaussian calculations in your HPC please refer to your HPC manager. 

As an example, for a single calculation in Gaussian 16 through the terminal we 
would run the following command on a Linux-based system: 

.. code:: shell

    g16 myfile.com

Step 5: QCORR analysis
----------------------

.. code:: shell

   python -m aqme --qcorr --files "QCALC/*.log" --freq_conv "opt=(calcfc,maxstep=5)" --mem 32GB --nprocs 16

Step 6: Resubmission of unsuccessful calculations (if any) with suggestions from AQME
-------------------------------------------------------------------------------------

Now we need to run the generated COM files (in fixed_QM_inputs) with Gaussian 
like we did in Step 4

After the calculations finish we check again the files using QCORR

.. code:: shell

   python -m aqme --qcorr --files "QCALC/failed/run_1/fixed_QM_inputs/*.log" --isom_type com --isom_inputs "QCALC/failed/run_1/fixed_QM_inputs" --nprocs 16 --mem 32GB

Step 7: Creating DLPNO input files for ORCA single-point energy calculations
----------------------------------------------------------------------------

.. code:: shell

   python -m aqme --qprep --program orca --mem 16GB --nprocs 8 --files "QCALC/success/*.log" --suffix DLPNO --destination SP --qm_input "DLPNO-CCSD(T) def2-tzvpp def2-tzvpp/C
   %scf maxiter 500
   end
   % mdci
   Density None
   end
   % elprop
   Dipole False
   end"

Step 8: Running ORCA inputs for single point energy calcs externally
--------------------------------------------------------------------

Now we need to run the generated inp files (in sp_path) with ORCA 
(similarly to how we did in Step 4)

Step 9: Calculating PES with goodvibes
---------------------------------------

for this step we will need to have a yaml file to use as input for goodvibes. 
The contents of the yaml file are: 

.. code:: yaml
   
   --- # PES
   # Double S addition
      Reaction1: [Diene+Do1, TS1, P1] 
      Reaction2: [Diene+Do2, TS2, P2] 
      Reaction3: [Diene+Do3, TS3, P3] 
      
   
   --- # SPECIES
      Diene     : Diene*
      Do1     : Do1*
      TS1     : TS1*
      P1    : P1*
      Do2     : Do2*
      TS2     : TS2*
      P2    : P2*
      Do3    : Do3*
      TS3     : TS3*
      P3   : P3*
     
   
   --- # FORMAT
      dec : 1
      units: kcal/mol
      dpi : 300
      color : #1b8bb9,#e5783d,#386e30

With this file we can now generate the profile.

.. code:: shell 

   mkdir -p GoodVibes_analysis
   cp SP/*.out GoodVibes_analysis/
   cp QCALC/success/*.log GoodVibes_analysis/
   cd GoodVibes_analysis
   python -m goodvibes --xyz --pes ../pes.yaml --graph ../pes.yaml -c 1 --spc DLPNO *.log
   cd ..

.. centered:: |profile|

## aqme/docs/Examples/examples_commandline/end_to_end/example_3.rst

Solubility descriptors
======================

Along the steps of this example workflow we will show how to: 

i)   RDKit conformer sampling
ii)  xTB porperty calculations to determine molecular and atomic
     properties
iii) Generate a GNN model to predict solubility

Specifically in this example we will calculate descriptors of a set of molecules
represented by smiles with the aim of training a Graph Neural Network (GNN) 
capable of predicting their solubility.

The set of molecules that we will use are in a file named 'solubility.csv' 
that has the following contents:

.. highlight:: none

.. literalinclude:: ../../chemfiles/end_to_end_3_inp.csv

.. highlight:: default

.. note::

   A jupyter notebook containing all the steps shown in this example can be found 
   in the AQME repository in `Github  <https://github.com/jvalegre/aqme>`__ or in 
   `Figshare <https://figshare.com/articles/dataset/AQME_paper_examples/20043665>`__

.. contents:: Steps
   :local:
   :depth: 2

Step 1: Run CSEARCH (RDKit) on the CSV
--------------------------------------

.. code:: shell

   python -m aqme --csearch --program rdkit --input solubility.csv --ewin_csearch 1

Step 2 : Run xTB calculations using QDESCP
------------------------------------------

.. code:: shell

   python -m aqme --qdescp --files "CSEARCH/*.sdf" --program xtb

Step 3 : Create the CSV file with descriptors for the GNN model
---------------------------------------------------------------

This step can be run in bash, python or manually using a spreadsheet editor.
The aim is to generate a file named 'solubility_xtb.csv' containing an extra 
column with the filepaths to the QDESCP generated .json files.

Here we include the python commands to do the step.

.. code:: python

   import pandas as pd 

   data =  pd.read_csv(file)
   code_to_filepath = 'QDESCP/boltz/{}_rdkit_boltz.json'.format
   data['xtbjson'] = data['code_name'].apply(code_to_filepath)
   data.to_csv('solubility_xtb.csv',index=False)

Step 4: Run the gnn.py to get results
-------------------------------------

This step requires other files that do not use aqme itself. The other files 
are available at 
`Figshare <https://figshare.com/articles/dataset/AQME_paper_examples/20043665>`__ .
Specifically the files gnn.py and gnn_functions.py require to be on the same 
directory as the file 'solubility.csv' and these two files depend on packages 
that aqme does not depend on. So before continuing please make sure that you 
have all the packages required installed as well as the specified files.

We can execute directly the gnn.py script to obtain the results

.. code:: shell

    python gnn.py

For more details on the contents of the gnn.py script please go to 
:doc:`python example <../../examples_python/end_to_end/example_3>` ) steps 5a, 
5b and 5c.

## aqme/docs/Examples/examples_commandline/examples_commandline.rst

=====================
Examples Command line
=====================

In this section you will find the same examples as shown in the python examples
section but with their corresponding commandline instructions when possible. 

.. toctree::
    :maxdepth: 2

    descriptor_generation
    conformer_search
    qm_input_generation
    correction_qm_output
    end_to_end

## AQME 2.1 parameters (csearch/base.py, from the installed package)

Parameters
----------

General
++++++

   input : str, default=''
      (If smi is None) Optionally, file containing the SMILES strings and
      names of the molecules. Current file extensions: .smi, .sdf, .cdx,
      .csv, .com, .gjf, .mol, .mol2, .xyz, .txt, .yaml, .yml, .rtf
      For .csv files (i.e. FILENAME.csv), two columns are required,
      'code_name' with the names and 'SMILES' for the SMILES string
   program : str, default='rdkit'
      Program required in the conformational sampling.
      Current options: 'rdkit', 'crest'
   smi : str, default=None
      Optionally, define a SMILES string as input
   name : str, default=None
      (If smi is defined) optionally, define a name for the system
   w_dir_main : str, default=os.getcwd()
      Working directory
   destination : str, default=None,
     Directory to create the output file(s)
   varfile : str, default=None
      Option to parse the variables using a yaml file (specify the filename)
   charge : int, default=None
      Charge of the calculations used in the following input files.
      If charge isn't defined, it automatically reads the charge of the
      SMILES string
   mult : int, default=None
      Multiplicity of the calculations used in the following input files. If
      mult isn't defined, it automatically reads the multiplicity of the mol
      object created with the SMILES string. Be careful with the automated
      calculation of mult from mol objects when using metals!
   freeze : list, default=[]
      Freeze atom indices for the RacerTS workflow. For SDF input these are
      interpreted as atom-map numbers. For XYZ input these are interpreted in
      file order, with 1 as the first atom.
   prefix : str, default=''
      Prefix added to all the names
   suffix : str, default=''
      Suffix added to all the names
   stacksize : str, default='1G'
      Controls the stack size used (especially relevant for xTB/CREST
      calculations of large systems, where high stack sizes are needed)

General RDKit-based
+++++++++++++++++++

   sample : int, default=25
      Number of conformers to keep after the initial RDKit sampling. They are selected using a
      combination of RDKit energies and Butina clustering
   auto_sample : str, default=mid in CSEARCH, low in QDESCP
      Apply automatic calculation of the number of conformers generated initially with RDKit. This number
      of conformers is initially generated and then reduced to the number specified in --sample with
      different filters. There is a sampling factor, which is multiplied by the number of rotatable bonds,
      and a maximum number of conformers allowed to pass to the filters. Options:
      1. Low: good for descriptor generation in machine learning. Base multiplier = 5, max number of confs = 100
      2. Mid: standard, good compromise between number of conformers and computing time. Base multiplier = 10, max number of confs = 250
      3. High: demanding method, more conformers and time. Base multiplier = 20, max number of confs = 500
      4. False: use the number of conformers specified in --sample
   ff : str, default='MMFF'
      Force field used in RDKit optimizations and energy calculations. Current 
      options: MMFF, UFF (if MMFF fails, AQME tries to use UFF automatically), and NO FF (works well with metals
      when UFF doesn't work)
   ewin_csearch : float, default=5.0
      Energy window in kcal/mol to discard conformers (i.e. if a conformer is 
      more than the E window compared to the most stable conformer)
   initial_energy_threshold : float, default=0.0001
      Energy difference in kcal/mol between unique conformers for the first 
      filter of only E
   energy_threshold : float, default=0.25
      Energy difference in kcal/mol between unique conformers for the second 
      filter of E + RMS
   rms_threshold : float, default=0.25
      RMS difference between unique conformers for the second filter of E + RMS
   opt_steps_rdkit : int, default=1000
      Max cycles used in RDKit optimizations
   heavyonly : bool, default=True
      Only consider heavy atoms during RMS calculations for filtering (in the 
      Chem.rdMolAlign.GetBestRMS() RDKit function)
   max_matches_rmsd : int, default=1000
      Max matches during RMS calculations for filtering (maxMatches option in 
      the Chem.rdMolAlign.GetBestRMS() RDKit function)
   max_mol_wt : int, default=0
      Discard systems with molecular weights higher than this parameter 
      (in g/mol). If 0 is set, this filter is off
   max_torsions : int, default=0
      Discard systems with more than this many torsions (relevant to avoid 
      molecules with many rotatable bonds). If 0 is set, this filter is off
   seed : int, default=62609
      Random seed used during RDKit embedding (in the 
      Chem.rdDistGeom.EmbedMultipleConfs() RDKit function)
   geom : list, default=[]
      Geometry rule to pass for the systems. Format: [SMARTS,VALUE]. Geometry rules
      might be atoms, bonds, angles and dihedral. For example, a rule to keep only
      molecules with C-Pd-C atoms at 180 degrees: ['[C][Pd][C]',180]. Multiple rules
      can be used at the same time (['C[Pd]C',180,'C[Pd]N',90]).
      Special rules (--geom ['RULE_NAME']):
         1. ['Ir_squareplanar']
   bond_thres : float, default=0.2
      Threshold used to discard bonds in the geom option (+-0.2 A) 
   angle_thres : float, default=30
      Threshold used to discard angles in the geom option (+-30 degrees) 
   dihedral_thres : float, default=30
      Threshold used to discard dihedral angles in the geom option (+-30 degrees) 

Only organometallic molecules
.............................

   auto_metal_atoms : bool, default=True
     Automatically detect metal atoms for the RDKit conformer generation. Charge 
     and mult should be specified as well since the automatic charge and mult 
     detection might not be precise.
   complex_type : str, default=''
      Forces the metal complexes to adopt a predefined geometry. This option is 
      especially relevant when RDKit predicts wrong complex geometries or gives 
      a mixture of geometries. Current options: squareplanar, squarepyramidal, 
      linear, trigonalplanar
   single_system : bool, default=False
      When using complex_type templates in CSEARCH, keep only one system of all the options. 
      This option is useful to avoid repetition when the complex has two identical
      ligands (i.e. two Cl substituents).

CREST and RDKit(only constraints)
++++++++++

   nprocs : int, default=8
      Number of processors used in CREST optimizations
   constraints_atoms : list, default=[]
      Specify constrained atoms as [AT1,AT2,AT3]. An example of multiple constraints with
      atoms 1, 2 and 5 frozen: [1,2,5]
   constraints_dist : list of lists, default=[]
      Specify distance constraints as [AT1,AT2,DIST]. An example of multiple constraints with
      atoms 1 and 2 frozen at a distance of 1.8 Å, and atoms 4 and 5 with distance of 2.0 Å:
      [[1,2,1.8],[4,5,2.0]]
   constraints_angle : list of lists, default=[]
      Specify angle constraints as [AT1,AT2,AT3,ANGLE]. An example of multiple constraints with
      atoms 1, 2 and 3 frozen at an angle of 180 degrees, and atoms 4, 5 and 6 with an angle of 120:
      [[1,2,3,180],[4,5,6,120]]
   constraints_dihedral : list of lists, default=[]
      Specify dihedral constraints as [AT1,AT2,AT3,AT4,DIHEDRAL]. An example of multiple constraints
      with atoms 1, 2, 3 and 4 frozen at a dihedral angle of 180 degrees, and atoms 4, 5, 6 and 7
      with a dihedral angle of 120: [[1,2,3,4,180],[4,5,6,7,120]]
   crest_force : float, default=0.5
      Force constant for constraints in the .xcontrol.sample file for CREST jobs
   crest_keywords : str, default=None
      Define additional keywords to use in CREST that are not included in --chrg, 
      --uhf, -T and -cinp. For example: '--alpb ch2cl2 --nci --cbonds 0.5'
   cregen : bool, default=True
      If True, perform a CREGEN analysis after CREST (filtering options below)
   cregen_keywords : str, default=None
      Additional keywords for CREGEN (i.e. cregen_keywords='--ethr 0.02')
   xtb_keywords : str, default=None
      Define additional keywords to use in the xTB pre-optimization that are not 
      included in -c, --uhf, -P and --input. For example: '--alpb ch2cl2 --gfn 1'
   crest_runs : int, default=1
      Specify as number of runs if multiple starting points from RDKit starting points is required.

## AQME 2.1 parameters (cmin.py, from the installed package)

Parameters
----------

General
+++++++

   files : str or list of str, default=None
     Input files. Formats accepted: SDF. Also, lists can be used
     (i.e. [FILE1.sdf, FILE2.sdf] or \*.sdf).
   program : str, default=xtb
     FAMEX backend used for geometry optimization. xTB uses the tblite backend.
     Current options: 'xtb', 'aimnet2', 'mace', 'orb', 'so3lr', 'uma'
   w_dir_main : str, default=os.getcwd()
     Working directory
   destination : str, default=None
     Directory to create the output file(s)
   varfile : str, default=None
     Option to parse the variables using a yaml file (specify the filename)
   charge : int, default=None
     Charge for FAMEX calculations. If not set, read from SDF 'Real charge'
     property; if missing, defaults to 0.
   mult : int, default=None
     Multiplicity for FAMEX calculations. If not set, read from SDF 'Mult'
     property; if missing, defaults to 1.
   ewin_cmin : float, default=5.0
     Energy window in kcal/mol to discard conformers after optimization.
   initial_energy_threshold : float, default=0.0001
     Energy difference in kcal/mol between unique conformers (first filter).
   energy_threshold : float, default=0.25
     Energy difference in kcal/mol between unique conformers (second filter).
   rms_threshold : float, default=0.25
     RMS difference threshold for the second filter.
   opt_fmax : float, default=0.05
     Convergence criterion (max force, eV/Å) for the BFGS optimizer in FAMEX.
   opt_steps : int, default=1000
     Maximum number of BFGS steps.
   constraints_dist : list of lists, default=[]
     Distance constraints for FAMEX FixInternals as [[AT1,AT2,DIST], ...].
   constraints_angle : list of lists, default=[]
     Angle constraints for FAMEX FixInternals as [[AT1,AT2,AT3,ANGLE], ...].
     Angles are specified in degrees.
   constraints_dihedral : list of lists, default=[]
     Dihedral constraints for FAMEX FixInternals as [[AT1,AT2,AT3,AT4,DIHEDRAL], ...].
     Dihedrals are specified in degrees.
   target : str, default='minima'
     Optimization target for FAMEX. Accepted values: 'minima' and 'ts'.
   freq : bool, default=False
     If True, calculates vibrational frequencies for conformers surviving filters.
   prefix : str, default=''
     Prefix added to all output names.
   suffix : str, default=''
     Suffix added to all output names.

## AQME 2.1 parameters (qdescp.py, from the installed package)

Parameters
----------

General
+++++++

   w_dir_main : str, default=os.getcwd()
      Working directory
   destination : str, default=None,
      Directory to create the JSON file(s)
   program : str, default=xtb
      Program used to create the new descriptors. Current options: 'xtb', 'nmr'
   nprocs : int, default=None
      Number of xTB jobs run in parallel with 1 proc each (1 proc for reproducibility 
      in the results). Also, nprocs used in CSEARCH
   qdescp_atoms : list of str, default=[]
      Type of atom or group to calculate atomic properties. This option admits atoms 
      (i.e., qdescp_atoms=['P']) and SMART patterns (i.e., qdescp_atoms=['C=O']) 
   robert : bool, default=True
      Creates a database ready to use in an AQME-ROBERT machine learning workflow,
      combining the input CSV with SMILES/code_name and the calculated xTB/DBSTEP descriptors

xTB and MORFEUS descriptors
+++++++++++++++++++++++++++

   files or input (both options are valid) : list of str, default=''
      Filenames of SDF/PDB/XYZ/CSV files to calculate xTB descriptors. If CSV is selected, a CSV
      with two columns is required (code_name and SMILES), since AQME will generate conformers
      from SMILES with CSEARCH before QDESCP generates descriptors.
   charge : int, default=None
      Charge of the calculations used in the following input files (charges from
      SDF files generated in CSEARCH are read automatically).
   mult : int, default=None
      Multiplicity of the calculations used in the following input files 
      (multiplicities from SDF files generated in CSEARCH are read automatically).
   qdescp_solvent : str, default=None
      Solvent used in the xTB property calculations (ALPB model). Not supported in
      this version of AQME: descriptors are calculated with PTB, which has no
      implicit solvation model, so setting it (or passing xTB solvation keywords
      such as --alpb or --gbsa) stops the run.
   boltz : bool, default=True
      Calculation of Boltzmann averaged xTB properties and addition of RDKit 
      molecular descriptors
   geom_opt : bool, default=True
      Performs an initial xTB geometry optimization before calculating descriptors
   method : str, default=xtb
      Backend used for the geometry optimization. If omitted, QDESCP uses the
      default xTB/tblite backend. Accepted values match the CMIN backend options
   vbur_radius : float, default=3.5
      Adjusts the radius in the buried volume calculations of MORFEUS

NMR simulation
++++++++++++++

   files : list of str, default=''
      Filenames of LOG files to retrieve NMR shifts from Gaussian calculations 
      (\*.log can be used to include all the log files in the working directory)
   boltz : bool, default=True
      Calculation of Boltzmann averaged NMR shifts
   nmr_atoms : list of str, default=[6, 1]
      List containing the atom types (as atomic numbers) to consider. For 
      example, if the user wants to retrieve NMR shifts from C and H atoms 
      nmr_atoms=[6, 1]
   nmr_slope : list of float, default=[-1.0537, -1.0784]
      List containing the slope to apply for the raw NMR shifts calculated with 
      Gaussian. A slope needs to be provided for each atom type in the analysis 
      (i.e., for C and H atoms, the nmr_slope=[-1.0537, -1.0784]). These values 
      can be adjusted using the CHESHIRE repository.
   nmr_intercept : list of float, default=[181.7815, 31.8723]
      List containing the intercept to apply for the raw NMR shifts calculated 
      with Gaussian. An intercept needs to be provided for each atom type in the
      analysis (i.e., for C and H atoms, the nmr_intercept=[-1.0537, -1.0784]). 
      These values can be adjusted using the CHESHIRE repository.
   nmr_experim : str, default=None
      Filename of a CSV containing the experimental NMR shifts. Two columnds are
      needed: A) 'atom_idx' should contain the indexes of the atoms to study as 
      seen in GaussView or other molecular visualizers (i.e., the first atom of 
      the coordinates has index 1); B) 'experimental_ppm' should contain the 
      experimental NMR shifts in ppm observed for the atoms.
