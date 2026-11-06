# Auto-QChem: upstream documentation

Source: https://github.com/doyle-lab-ucla/auto-qchem

## auto-qchem/README.md

<p align="center">
  
</p>

---

## Quick links

[Installation instructions](https://github.com/doyle-lab-ucla/auto-qchem/blob/master/INSTALL.md)

[Database user instructions](https://github.com/doyle-lab-ucla/auto-qchem/blob/master/DB.md)

[Code base documentation](https://doyle-lab-ucla.github.io/auto-qchem)

[What exactly are all the descriptors?](https://github.com/doyle-lab-ucla/auto-qchem/blob/master/DESCRIPTOR.md)

---
[Repo with example jupyter notebooks](https://github.com/doyle-lab-ucla/auto-qchem-notebook-examples)

[Database link](https://autoqchem.org)

[Auto-QChem paper (publisher)](https://pubs.rsc.org/en/content/articlelanding/2022/re/d2re00030j#!divCitation), [free pdf](https://drive.google.com/file/d/1M8Ydqlk5Kbc_8WoR5dAm_JIbf2IBJTlU/view?usp=share_link)

## Note to external user
Auto-QChem currently supports Slurm scheduler at Princeton via slurm_manager.py; and SGE/UGE-type scheduler at UCLA via sge_manager.py. 

If you are an external user and your computational cluster uses either slurm or sge scheduler, you just need to make some minor changes to either .py files to make sure you can log in with credentials at your institution.

If you are an external user and your computational cluster uses other schedulers, you can still modify either .py files to adapt to your cluster, but significant changes might be required and we unfortunatey won't be able to help without access to your cluster.

## auto-qchem/INSTALL.md

# auto-qchem installation instructions

### New installation instructions for auto-qchem

1. Install conda: https://www.anaconda.com. I find it easier to just download the installer and install like how you would with any software.
2. Conda allows you to create separate software development environments for different purposes. We will create an environment just for auto-qchem. Open terminal and run this, and answer "y" to the prompt:
```
conda create --name autoqchem python=3.8 ipython
```
3. With conda environments, you need to activate them before you use. Run this in terminal: 
 ```
 conda activate autoqchem 
 ```
4. We have some separate packages to install first. (OpenBabel does not work on pip). Run the following commands in terminal one by one, and answer "y": 
 ```
conda install -c conda-forge openbabel
 ```
5. Finally, we can install auto-qchem directly through pip 
 ```
pip install auto-qchem
 ```
6. That's it, you are ready to use auto-qchem. 

---

### If you want to start over...
Sometimes things don't work, and you might want to delete the autoqchem environment and start over with a clean install. To remove the conda environment and all packages associated with it, run:

**(Optional)** if you are in the autoqchem environment, deactivate first:
 ```
conda deactivate
 ```
then run this to remove autoqchem environment:
 ```
conda remove -n autoqchem --all
 ```
And you are ready to start over at step 2 in the new installation instructions. 

---

### If you haven't used auto-qchem for a while...
Chances are there have been updates for the software.

**(Optional)** if you are NOT in the autoqchem environment, activate first:
 ```
conda activate autoqchem
 ```

**(Optional)** you can check the current version of auto-qchem:
 ```
conda list auto-qchem
 ```

Run this to update to the newest version:
 ```
pip install auto-qchem --upgrade
 ```

---

---

---

### Prerequisite for Windows users only
I have not tested for Windows. 

Install openbabel binaries (comes with a GUI)
https://github.com/openbabel/openbabel/releases/download/openbabel-2-4-1/OpenBabel-2.4.1.exe

## auto-qchem/DB.md

# Auto-QChem Database User Guide

Auto-QChem stores molecular descriptors in a MongoDB type database. A small web-based user-interface has been created to
facilitate extractions of descriptors from the database into ```.xlsx``` files for further analysis.

### 1. Query available molecules

Navigate to the [autoqchem.org](https://autoqchem.org)

#### 1.1 Query TAB

##### Fields

Query form has 6 fields, first 4 are required, last 2 are optional:

* __Dataset tag__ - select dataset filter, use 'ALL' for a whole DB query. Each molecule in the DB has an associated
  datasets tag
  (or a list of tags), they are used to mark specific collections of molecules dedicated to specific analyses
* __Solvent__ - solvent filter, use 'ALL' to ignore filter
* __Functional__ - functional filter, use 'ALL' to ignore filter
* __Basis Set__ - basis set filter, use 'ALL' to ignore filter
* __SMARTS substructure__ - filters the molecules for substructre using the SMARTS query. A quick reference to the
  SMARTS query language can be looked up
  here [https://www.daylight.com/dayhtml_tutorials/languages/smarts/index.html](https://www.daylight.com/dayhtml_tutorials/languages/smarts/index.html)
* __SMILES__ - smiles filter. This can be used for searches for a specific molecule. Canonicalization is not required.

Upon successful query additional 2 tabs will appear, "Download Descriptors" and "Export Molecule List"

#### 1.2 Download Descriptor TAB

Download form has 2 fields, both are required:

* __Descriptor Presets (multiple choice)__ - the following presets are available, choose as many as needed:
    * __Global__ - molecule level descriptors, e.g. homo energy, dipole moment, molecular weight, etc.
    * __Min Max Atomic__ - atomic level descriptors minimum and maximum over the atoms within the molecule, e.g. buried
      volume, Mulliken charge, NMR shift, etc.
    * __Substructure Atomic__  - only relevant if substructure was used for the query. The atoms matching the
      substructure are extracted in consistent order and their descriptors are obtained
    * __Common Core__ - atomic level descriptors for the common core of atoms within the dataset, the common core is
      determined using the [MCS procedure](https://www.rdkit.org/docs/source/rdkit.Chem.MCS.html) from rdkit. If
      substructure has been used for filtering, the common core will include the substructure and potentially more
      atoms.
    * __Labeled Atomic__ - atomic level descriptors for labeled molecules. The labels must be consistent, i.e. each
      molecule must have exactly the same labels, for example 1,2,3,4, the labelled elements can be different, only the
      numbering scheme shall be consistent.
    * __Transitions__ - top 10 excited state transitions ordered by their oscillation strength
* __Conformer option (single choice)__ - choose one of the following options:
    * __Boltzmann__ - Boltzmann average
    * __Max__ - lowest energy conformer (maximum weight conformer)
    * __Min__ - highest energy conformer (minimum weight conformer)
    * __Mean__ - arithmetic average
    * __Std__ - standard deviation over the conformers
    * __Any__ - randomily chosen conformer The result of the query is downloaded into an ```.xlsx``` sheet.

#### 1.3 Export Molecules List TAB

Export button downloads the queried list of molecules into an ```.xlsx``` sheet.

Result of an example query on a specific tag containing primary sulfonamides, and with SMARTS query for anhydrides,
resulting in 75 matches.

### 2 Descriptors Lookup

For each entry in the table a link to a descriptors lookup is available in the rightmost column. It displays an
interactive 3D visualization of the molecule conformers as well as the descriptors of the molecule. If the molecule
contains multiple conformations, the descriptors are Boltzman averages over the conformer ensemble.

## auto-qchem/DESCRIPTOR.md

This document contains detailed explanations of all descriptor names in Auto-QChem with their units. All calculations are done in Gaussian with Gaussian terminologies. If not specified for excited state, all values represent ground state. 

## Molecular features

E: Sum of electronic and thermal Energies (Hartree)

ES_root_dipole: Dipole moment for the first excited state (Debye)

ES_root_electronic_spatial_extent: Electronic spatial extent for the first excited state (a.u.)

ES_root_molar_volume: Molar volume for the first excited state (Bohr^3/mole)

E_scf: 	Energy from Self-Consistent Field method (Hartree)

E_thermal_correction: Thermal correction to Energy (Hartree)

E_zpe: Sum of electronic and zero-point Energies (Hartree)

G: Sum of electronic and thermal Free Energies (Hartree)

G_thermal_correction: Thermal correction to Gibbs Free Energy (Hartree)

H: Sum of electronic and thermal Enthalpies (Hartree)

H_thermal_correction: Thermal correction to Enthalpy (Hartree)

Dipole: Dipole moment (field-independent basis, Debye)

electronegativity: –0.5*(lumo_energy + homo_energy) (Hartree)

electronic_spatial_extent: Electronic spatial extent (a.u.)

hardness: 0.5*(lumo_energy – homo_energy) (Hartree)

homo_energy: HOMO energy (Hartree)

lumo_energy: LUMO energy (Hartree)

molar_mass: Molar Mass (grams/mole)

molar_volume: Molar volume (Bohr^3/mole)

zero_point_correction: Zero-point correction (Hartree)

ES_<S\**2>[number]: Total spin operator for excited state [number], which corresponds to the same excited state in ES_osc_strength_[number] (unitless)

ES_osc_strength_[number]: The oscillator strength for excited state [number], ranked from highest to lowest. E.g., ES_osc_strength_0 represent the excited state with the highest oscillator strength out of all excited state calculated (unitless)

ES_transition_[number]: The wavelength for the excited state transition from ground state to excited state [number], which corresponds to the same excited in ES_osc_strength_<number> (nanometer).

## Atomic features

<atom>_APT_charge: Atomic Polar Tensor charge (a.u.)

<atom>_ES_root_Mulliken_charge: Mulliken charge in the first excited state (a.u.)

<atom>_ES_root_NPA_Rydberg: Rydberg orbital charges from NPA for the first excited state (a.u.)

<atom>_ES_root_NPA_charge: natural charge from NPA for the first excited state (a.u.)

<atom>_ES_root_NPA_core: core orbital charges from NPA for the first excited state (a.u.)

<atom>_ES_root_NPA_total: <atom>_ES_root_NPA_core + <atom>_ES_root_NPA_valence + <atom>_ES_root_NPA_Rydberg

<atom>_ES_root_NPA_valence: valence orbital charges from NPA (a.u.)

<atom>_Mulliken_charge: Mulliken charge (a.u.)

<atom>_NMR_anisotropy: NMR shielding anisotropy 

<atom>_NMR_shift: isotropic NMR shielding/chemical shift (ppm)

<atom>_NPA_Rydberg: Rydberg orbital charges from NPA (a.u.)

<atom>_NPA_charge: natural charge from NPA (a.u.)

<atom>_NPA_core: core orbital charges from NPA (a.u.)

<atom>_NPA_total: <atom>_NPA_core + <atom>_NPA_valence + <atom>_NPA_Rydberg

<atom>_NPA_valence: valence orbital charges from NPA (a.u.)	

<atom>_VBur: for a given atom, within a 3Å radius, the fraction of the volume that is occupied by other atoms in the molecule (represented by their Van der Waals radii).
