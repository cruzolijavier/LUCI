# ThermoMLIP: upstream documentation

Source: https://github.com/chimie-paristech-CTM/ThermoMLIP

## ThermoMLIP/README.md

# ThermoMlip

<p align="center">
  
</p>

<p align="center">
  <b>Machine learning interatomic potential enhanced thermochemistry predictions across organic small compound space</b>
</p>

## Description
ThermoMLIP package can do conformer search and thermochemistry analysis.

## Requirements
- ThermoMLIP package
- PyTorch
- CUDA (optional, for GPU acceleration)

## Installation

### Step 1: Create conda environment
```bash
conda env create -f environment.yaml
conda activate thermomlip
```

### Step 2: Install FairChem
```bash
git clone https://github.com/facebookresearch/fairchem.git
pip install -e fairchem/packages/fairchem-core[dev]
```
This installs the FairChem package, a required dependency.

### Step 3: Install ThermoMLIP
```bash
pip install -e .
```
This will automatically compile the Cython extensions during installation.

## Usage
Example scripts are provided in the `script/` directory. For single-molecule
calculations, use:

```bash
python script/run_single_molecule.py
```

The old `demo.py` and `demo3.py` entry points are no longer used.

## Workflow
1. **Initialize** - Set up configuration parameters and methods
2. **Create Molecule** - Generate molecule from SMILES string or XYZ file
3. **Find Conformers** - Search for lowest energy conformer using RR and RDKit methods
4. **Optimize** - Refine molecular geometry with MLIP
5. **Calculate Thermochemistry** - Compute thermodynamic properties at 298.15K

## Output
The calculation provides:
- Electronic energy (Ha)
- Gibbs free energy (Ha)
- Enthalpy (Ha)
- Entropy (J/mol·K)
- Zero point energy (Ha)
- Enthalpy and Gibbs corrections

## Configuration
Default parameters can be modified in the script:
- `num_conformers`: 10 (number of conformers to generate)
- `initial_structure_method`: "rr" (repulsion+relaxed method)
- `n_cores`: 10 (parallel processing cores)
- `temperature`: 298.15 K
- `pressure`: 101325 Pa
- `batch_size`: 32 (active batch size for the hot-swap batch L-BFGS optimiser)
- `steps_between_swaps`: 1 (L-BFGS steps between batch refresh checks)

## Batch optimisation

When multiple molecules or conformers are optimised in one call, ThermoMLIP
keeps up to `batch_size` structures active on the GPU and automatically
replaces completed structures with pending ones. This keeps memory use tied
to the active batch while allowing the optimiser to continue processing the
remaining pool.

## Citation
If this work is used as part of a publication, please cite:
```
@article{automlip2024,
  title={Machine learning interatomic potential enhanced thermochemistry predictions across organic small compound space},
  author={Bowen Deng and Thijs Stuyver},
  journal={ChemRxiv},
  year={2024}
}
```

Since this work is inspired by autodE:
```
@article{young2021autode,
  title={autodE: Automated calculation of reaction energy profiles—application to organic and organometallic reactions},
  author={Young, Tom A and Silcock, Joseph J and Sterling, Alistair J and Duarte, Fernanda},
  journal={Angewandte Chemie},
  year={2021}
}
```
