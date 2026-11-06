# Morfeus: upstream documentation

Source: https://github.com/digital-chemistry-laboratory/morfeus (docs: https://digital-chemistry-laboratory.github.io/morfeus/)

## How LUCI runs Morfeus

- Layer LUCI-FEAT, program key `morfeus`, its own environment (Python 3.12, morfeus-ml, Open Babel and the xtb program for the xTB descriptors).
- Input: a folder of 3D structures (LUCI hands them over as SDF). Every record of every SDF gets a row, so a CSEARCH or racerTS output gives one row per conformer.
- Morfeus' own command line (Python Fire) prints one value of one file; LUCI uses the Morfeus Python API in a runner and writes one CSV table, morfeus_descriptors.csv (name changeable), with code_name, structure number, title, the SDF Energy when present, and one column per value.
- Descriptors (tick several): Sterimol (sterimol_L, sterimol_B1, sterimol_B5; atom 1 = dummy atom, atom 2 = first substituent atom; optional buried Sterimol), Buried volume (buried_volume_percent; atom 1 = centre/metal; radius 3.5 A, Bondi radii x1.17, hydrogens excluded by default), Cone angle (atom 1 = metal), Solid angle (solid_angle, solid_cone_angle, solid_G), SASA (sasa_area, sasa_volume; probe 1.4 A), Dispersion (dispersion_area, dispersion_volume, dispersion_p_int), Pyramidalization (P, P_angle; atom 1, optional neighbours), Visible volume (atom 1 = metal), Bite angle (atom 1 = metal, atoms 2 and 3 = ligand atoms), xTB electronic (xtb_energy, HOMO, LUMO, gap in Hartree from morfeus, IP, EA in eV, dipole, electrophilicity, nucleophilicity; GFN2, GFN1 or PTB, optional ALPB solvent; charge from the option, else the charge LUCI stored in the SDF).
- With an atom 1 set, SASA, dispersion and xTB also add that atom's own value (atom area, atom P_int, atom charge).
- Atom indices are 1-based (Morfeus' convention), in file order.
- CLI example: luci feat --backend morfeus --structures conformers/ -- --descriptors "[sterimol,buried_volume]" --atom_1 1 --atom_2 2


## morfeus/README.md





[](https://pypi.org/project/morfeus-ml/)
[](https://anaconda.org/conda-forge/morfeus-ml)


[](https://github.com/digital-chemistry-laboratory/morfeus/actions/workflows/test.yml)
[](https://zenodo.org/badge/latestdoi/291745112)

A Python package for calculating molecular features.

# Installation

## pip

```shell
$ pip install morfeus-ml
```

## conda

```shell
$ conda install -c conda-forge morfeus-ml
```

# Usage

ᴍᴏʀғᴇᴜs can be imported as a Python module that is easily integrated into
workflows. Here is an example for calculating the exact ligand cone angle.

```shell
>>> from morfeus import ConeAngle, read_xyz
>>> elements, coordinates = read_xyz("PdPMe3.xyz")
>>> cone_angle = ConeAngle(elements, coordinates, 1)
>>> print(cone_angle.cone_angle)
117.11012922937587
```

It can also be used from the command line.

```console
$ morfeus cone_angle PdPMe3.xyz - 1 - cone_angle
117.11012922937587
```
For further information, see the separate [documentation](https://digital-chemistry-laboratory.github.io/morfeus/).

# Features

* Bite angle
* Buried volume
* Conformer tools
* Dispersion descriptor
* Exact ligand cone angle
* Ligand solid angle
* Local force constant
* Pyramidalization
* Solvent accessible surface area
* Sterimol parameters
* XTB electronic descriptors

# Acknowledgements

ᴍᴏʀғᴇᴜs was started by Kjell Jorner as a post doc at AstraZeneca UK in
collaboration with the groups of Alán Aspuru-Guzik at the University of
Toronto, Matthew Sigman at the University of Utah and Tobias Gensch at TU
Berlin. The package was further developed and maintained in the group of Kjell Jorner at ETH Zurich.

In particular, the following people (in alphabetical order) have contributed significantly to
developing its functionality:

* Gabriel dos Passos Gomes
* Kjell Jorner
* Lauriane Jacot-Descombes
* Pascal Friedrich
* Tobias Gensch


## morfeus/docs/cli.rst

======================
Command line interface
======================

The command line interface (CLI) for ᴍᴏʀғᴇᴜs is powered by `Python Fire`__. In
this way, allmost all of the functionality of the module system is made
available also in the command line.

.. __: https://github.com/google/python-fire

************
Introduction
************

The entry point to the CLI is the command line script ``morfeus``. Running this
command in the terminal gives a help page with all the possible subcommands.

.. tab:: Input 1

  .. code-block:: shell

    $ morfeus

.. tab:: Output 1

  .. code-block:: none

    NAME
      morfeus

    SYNOPSIS
      morfeus COMMAND

    COMMANDS
      COMMAND is one of the following:

       buried_volume
         CLI for buried volume.

       cone_angle
         CLI for cone angle.

       conformer
         CLI for cone angle.

       dispersion
         CLI for dispersion descriptor.

       local_force
         CLI for local force.

       pyramidalization
         CLI for pyramidalization.

       sasa
         CLI for solvent accessible surface area.

       sterimol
         CLI for Sterimol.

       visible_volume
         CLI for visible volume.

       xtb
         CLI for XTB.

There is also a help page for each subcommand:

.. tab:: Input 2

  .. code-block:: shell

    $ morfeus sterimol -- --help

.. tab:: Output 2

  .. code-block:: none

    NAME
        morfeus sterimol - CLI for Sterimol.

    SYNOPSIS
        morfeus sterimol FILE

    DESCRIPTION
        CLI for Sterimol.

    POSITIONAL ARGUMENTS
        FILE
            Type: str
            Geometry file

    NOTES
        You can also use flags syntax for POSITIONAL ARGUMENTS

All the subcommands serve as entry points to the corresponding Python classes
used in the module system. For example, ``morfeus sterimol tBu.xyz -`` creates
a partially instantiated :py:class:`Sterimol <morfeus.sterimol.Sterimol>`
object where the ``elements`` and ``coordinates`` arguments have been set from
the geometry file. To find out what other argument can be given to this object,
we run

.. tab:: Input 3

  .. code-block:: shell

    $ morfeus sterimol tBu.xyz - -- --help

.. tab:: Output 3

  .. code-block:: none

    NAME
        morfeus sterimol tBu.xyz - partial(func, *args, **keywords) - new function with partial application of the given arguments and keywords.

    SYNOPSIS
        morfeus sterimol tBu.xyz - GROUP | COMMAND | --dummy_index=DUMMY_INDEX --attached_index=ATTACHED_INDEX <flags>

    DESCRIPTION
        partial(func, *args, **keywords) - new function with partial application of the given arguments and keywords.

    ARGUMENTS
        DUMMY_INDEX
            Type: int
        ATTACHED_INDEX
            Type: typing.Union[int, ...

    FLAGS
        --radii=RADII
            Type: Optional[typing.Union[int, float, complex, str, bytes, numpy.ge...
            Default: None
        --radii_type=RADII_TYPE
            Type: str
            Default: 'crc'
        --n_rot_vectors=N_ROT_VECTORS
            Type: int
            Default: 3600
        --excluded_atoms=EXCLUDED_ATOMS
            Type: Optional[t...
            Default: None
        --calculate=CALCULATE
            Type: bool
            Default: True

    GROUPS
        GROUP is one of the following:

         args

         keywords

    COMMANDS
        COMMAND is one of the following:

         func
           Performs and stores results of Sterimol calculation.

We learn that we need to supply the two arguments: ``dummy_index`` and
``attached_index``. Optional keyword arguments can also be given. After
supplying the additional arguments, we get back a fully instantiated object.
Getting the help from this object returns the available commands and what
values are available.

.. tab:: Input 4

  .. code-block:: shell

      $ morfeus sterimol tBu.xyz - 1 2 --radii_type=bondi - -- --help

.. tab:: Output 4

  .. code-block:: none

    NAME
        morfeus sterimol tBu.xyz 1 2 --radii_type=bondi - Performs and stores results of Sterimol calculation.

    SYNOPSIS
        morfeus sterimol tBu.xyz - 1 2 --radii_type=bondi - COMMAND | VALUE

    DESCRIPTION
        Performs and stores results of Sterimol calculation.

    COMMANDS
        COMMAND is one of the following:

         bury
           Do a Buried Sterimol calculation.

         calculate
           Calculate Sterimol parameters.

         draw_3D
           Draw a 3D representation of the molecule with the Sterimol vectors.

         print_report
           Prints the values of the Sterimol parameters.

         set_points
           Set points for calculation of Sterimol.

         surface_from_radii
           Create surface points from vdW surface.

    VALUES
        VALUE is one of the following:

         B_1

         B_1_value

         B_5

         B_5_value

         L

         L_value

         L_value_uncorrected

         bond_length

We could for example access the ``B_1_value`` attribute or run the method
``print_report`` with the ``verbose=True`` keyword argument.

.. code-block:: shell
  :caption: Example of Sterimol CLI

  $ morfeus sterimol tBu.xyz - 1 2 --radii_type=bondi - B_1_value
  2.964748534441907
  $ morfeus sterimol tBu.xyz - 1 2 --radii_type=bondi - print_report
  L         B_1       B_5
  4.31      2.96      3.37

The last command correspond to the following Python code using the module
system.

.. code-block:: python
  :caption: Example of Sterimol with module code

  from morfeus import read_geometry, Sterimol
  elements, coordinates = read_geometry("tBu.xyz)
  sterimol = Sterimol(elements, coordinates, 1, 2, radii_type="bondi")
  sterimol.print_report(verbose=True)

************
Detailed use
************

Positional arguments are passed in sequence separated by spaces, for example:

.. code-block:: shell

  $ morfeus sterimol tBu.xyz - 1 2

Keyword arguments are passed with or without an equals sign, so both of these
commands give the same result:

.. code-block:: shell

  $ morfeus sterimol tBu.xyz - 1 2 --radii_type=bondi
  $ morfeus sterimol tBu.xyz - 1 2 --radii_type bondi

A single ``-`` is used to indicate that all arguments have been provided and
the function/class should be evaluated. For example, the ``-`` before
``print_report`` in the example below tells Fire to instantiate the Sterimol
class, as we don't want to give more keyword arguments. Then the
``print_report`` method is excuted.

.. code-block:: shell

  $ morfeus sterimol tBu.xyz - 1 2 --radii_type bondi - print_report

Arguments following the ``--`` separator go directly to the Fire program. For
example, the ``--`` in the line below makes sure that ``--help`` is sent to
Python Fire instead of the ``Sterimol`` object.

.. code-block:: shell

  $ morfeus sterimol tBu.xyz - -- --help

**********************
Partial initialization
**********************

ᴍᴏʀғᴇᴜs uses Fire together with functools.partial__ to partially initialize
classes using the information in the geometry file. When running ``morfeus
sterimol tBu.xyz -``, this is what goes on behind the scenes:

.. code-block:: python
  :caption: cli function for Sterimol

  def cli(file: str) -> Any:
      elements, coordinates = read_geometry(file)
      return functools.partial(Sterimol, elements, coordinates)

The geometry file is read, and the elements and coordinates are used to
partially instantiate a Sterimol object. By specifiying the final hyphen ``-``,
we are telling Fire to evaluate the ``cli`` function and return this partially
instantiated object. We can can then supply the remaining arguments required to
fully instantiate ``Sterimol`` with ``morfeus sterimol tBu.xyz - 1 2 -``.

.. __: https://docs.python.org/3/library/functools.html#functools.partial

********
Chaining
********

A very powerful feature of Fire is chaining, which allows a series of commands
to be run on the same object. The commands (and their arguments) are separated
by hyphens, and the chain should end with a command that gives some output.
Here is one example where we create an electron density isosurface from a cube
file for a dispersion descriptor calculation.

.. code-block:: shell

  $ morfeus dispersion corannulene.xyz - --point_surface=False - surface_from_cube corannulene.cub - compute_p_int - print_report
  Surface area (Å²): 248.0
  Surface volume (Å³): 247.8
  P_int (kcal¹ᐟ² mol⁻¹ᐟ²): 25.8

This works because methods that modify
:py:class:`Dispersion <morfeus.dispersion.Dispersion>`
return the object itself:

.. code-block:: python

  def surface_from_cube(self, ...):
      ...
      return self

We can break down the chaining in detail:

``morfeus dispersion corannulene.xyz -``
  Partially instantiate the ``Dispersion`` object

``--point_surface=False -``
  Give the keyword argument ``point_surface=True`` and fully instantiate

``surface_from_cube corannulene.cub -``
  Run ``surface_from_cube`` method with cube filename as argument and return
  same object

``compute_p_int -``
  Run ``compute_p_int`` method and return same object

``print_report``
  Run print_report method and return output

****************
Interactive mode
****************

Another powerful feature of Fire is that it can send the result to an
interactive Python session, where it can be manipulated further. This is
triggered with the Fire argument ``--interactive`` and could be used to,
*e.g.*, access the 3D drawing capabilities of ᴍᴏʀғᴇᴜs.

.. code-block::

  $ morfeus sterimol tBu.xyz - 1 2 - -- --interactive

  Fire is starting a Python REPL with the following objects:
  Modules: fire
  Objects: component, main, morfeus, result, trace

  Python 3.9.2 | packaged by conda-forge | (default, Feb 21 2021, 05:02:20)
  Type 'copyright', 'credits' or 'license' for more information
  IPython 7.22.0 -- An enhanced Interactive Python. Type '?' for help.

  In [1]: result
  Out[1]: Sterimol(14 atoms)

  In [2]: result.bond_length
  Out[2]: 1.1

  In [3]: result.print_report()
  L         B_1       B_5
  4.21      2.86      3.27

  In [4]: result.draw_3D()
  ...

*********
Arguments
*********

Fire attemps to correctly guess the correct type of the arguments given in the
command line. The following style is recommended as it works across different
operating systems. Note that integers being intended as strings need double
quotes.

===== ==================
Type  Recommendation
===== ==================
str   bondi, '"1"'
int   1
float 1.0
list  '[1,2]'
dict  '{"key": "value"}'
bool  True
===== ==================

*********
Resources
*********

More detailed information on using the CLI can be found in the Fire
documentation:

- `The Python Fire guide`__
- `Using the CLI`__
- `Specifying arguments`__

.. __: https://google.github.io/python-fire/guide/
.. __: https://google.github.io/python-fire/using-cli/
.. __: https://google.github.io/python-fire/guide/#argument-parsing



## morfeus/docs/sterimol.rst

========
Sterimol
========

The Sterimol parameters L, B\ :sub:`1` and B\ :sub:`5` as described by Verloop
:footcite:`verloop_development_1976,verloop_sterimol_1983` are implemented.
Note that Sterimol parameters should be calculated with hydrogen as the dummy atom, to
be consistent with values in the literature (see `Background`_).

******
Module
******

The Sterimol class calculates and stores Sterimol parameters.

.. code-block:: python
  :caption: Example

  >>> from morfeus import Sterimol, read_xyz
  >>> elements, coordinates = read_xyz("tBu.xyz")
  >>> sterimol = Sterimol(elements, coordinates, 1, 2)
  >>> sterimol.L_value
  4.209831193078874
  >>> sterimol.B_1_value
  2.8650676183152837
  >>> sterimol.B_5_value
  3.26903261263369
  >>> sterimol.print_report()
  L         B_1       B_5
  4.21      2.87      3.27

The first given atom index argument corresponds to the index of the dummy H atom (1-indexed),
while the second one corresponds to the atom bound to the dummy H.

Radii can be changed with the argument ``radii_type=<str>`` and custom radii
can be supplied as a list with ``radii=<list>``.

The bond length between atoms 1 and 2 and the uncorrected L values (without the
historical addition of 0.40 Å) can also be obtained.

.. code-block:: python
  :caption: Uncorrected L values

  >>> sterimol.L_value_uncorrected
  3.8098311930788737
  >>> sterimol.bond_length
  1.1
  >>> sterimol.print_report(verbose=True)
  L         B_1       B_5       L_uncorr  d(a1-a2)
  4.21      2.87      3.27      3.81      1.10

Below is illustrated the Sterimol parameters of the *tert*-Butyl ligand as calculated with
the code above.

.. figure:: images/sterimol/tBu_sterimol.png
  :name: buried_volume
  :width: 70%

More information can be found with ``help(Sterimol)`` or in the API:
:py:class:`Sterimol <morfeus.sterimol.Sterimol>`.

###############
Buried Sterimol
###############

The Sterimol vectors can be "buried":

.. tab:: Delete

  .. code-block:: python

    >>> elements, coordinates = read_xyz("P_p-Tol_3.xyz")
    >>> sterimol = Sterimol(elements, coordinates, 1, 2)
    >>> sterimol.print_report()
    L         B_1       B_5
    7.44      4.94      7.44
    >>> sterimol.bury(method="delete")
    >>> sterimol.print_report()
    L         B_1       B_5
    6.92      4.27      6.04

.. tab:: Truncate

  .. code-block:: python

    >>> elements, coordinates = read_xyz("P_p-Tol_3.xyz")
    >>> sterimol = Sterimol(elements, coordinates, 1, 2)
    >>> sterimol.print_report()
    L         B_1       B_5
    7.44      4.94      7.44
    >>> sterimol.bury(method="truncate")
    >>> sterimol.print_report()
    L         B_1       B_5
    5.90      4.27      5.01

.. tab:: Slice

  .. code-block:: python

    >>> elements, coordinates = read_xyz("P_p-Tol_3.xyz")
    >>> sterimol = Sterimol(elements, coordinates, 1, 2)
    >>> sterimol.print_report()
    L         B_1       B_5
    7.44      4.94      7.44
    >>> sterimol.bury(method="slice")
    >>> sterimol.print_report()
    L         B_1       B_5
    5.82      3.77      5.24

There are three different methods for doing this:

``delete``
  Atoms outside the sphere + 0.5 vdW radius are deleted and the Sterimol
  vectors are calculated. This is the default.
``truncate``
  Sterimol vectors are calculated as usual, but truncated in length by the
  sphere.
``slice``
  A point vdW surface is constructed from the atoms and all points outside the
  sphere are removed. Then the Sterimol vectors are computed based on the
  remaining points.

A standard sphere radius of 5.5 Å is used that can be changed with
``sphere_radius=<float>``. For the ``delete`` method, the scaling factor for
the atom cutoff can be changed with ``radii_scale=<float>``. For more
information, see the API:
:py:meth:`Sterimol.bury <morfeus.sterimol.Sterimol.bury>`

*******************
Command line script
*******************

The command line script gives access to the basic functionality from the
terminal.

.. code-block:: shell
  :caption: Example

  $ morfeus sterimol tBu.xyz - 1 2 - print_report
  L         B_1       B_5
  4.21      2.86      3.27

**********
Background
**********

The Sterimol parameters were developed by Verloop to describe the steric size
of substituents. The atom attached to the substituent in the calculation (by
definition H) is called atom 1 and the first atom in the substituent is called
atom 2. L can be described as the depth of the substituent. It is defined as
the length of the vector going from atom 1, through atom 2 and ending on the
tangent of the vdW surface. For historical reasons, L is corrected by adding
0.40 Å to this length. This  was due to a shift from using C(sp\ :sup:`2`) to H
as dummy atom.

B\ :sub:`1` and B\ :sub:`5` can be described as the minimum and maximum
rotational size of the substituent. They are defined as the shortest and
longest vectors from atom 2 to a tangent plane of the vdW surface which are
perpendicular to the L vector, respectively.

ᴍᴏʀғᴇᴜs has been benchmarked against Paton's Sterimol__ package. Using exactly
the same radii (Paton's modified Bondi), almost identical results are obtained.
(Note that ᴍᴏʀғᴇᴜs normally uses 1.20 Å as the Bondi vdW radius for H). ᴍᴏʀғᴇᴜs
calculates the B\ :sub:`1` and B\ :sub:`5` parameters by a different approach
from the original code. First, atomic spheres are created with a certain
density of points. B\ :sub:`1` and B\ :sub:`5` are then obtained by projection
of atoms onto vectors spanning the whole 360 degrees in the plane perpendicular
to L. B\ :sub:`5` is obtained from the largest projection, while B\ :sub:`1` is
obtained from the smallest maximum projection for the set of vectors.

Buried Sterimol was developed by Tobias Gensch while working in the group of
Matthew Sigman at the University of Utah :footcite:`gensch_kraken_2022`. It is
intended to limit the Sterimol vectors to a volume of interest in the
philosophy of the buried volume. The original implementation uses the
``delete`` algorithm. ᴍᴏʀғᴇᴜs uses the CRC handbook radii by default instead of
the modified Bondi radii in the original article, so results with the defualt
settings might be slighly different.

.. __: https://github.com/bobbypaton/Sterimol

.. footbibliography::



## morfeus/docs/buried_volume.rst

=============
Buried volume
=============

Buried volumes are implemented as described by Cavallo and co-workers
:footcite:`falivene_sambvca_2016`.

******
Module
******

The BuriedVolume class calculates the buried volume. Steric maps can also be
plotted.

.. code-block:: python
  :caption: Example

  >>> from morfeus import BuriedVolume, read_xyz
  >>> elements, coordinates = read_xyz("1.xyz")
  >>> bv = BuriedVolume(elements, coordinates, 1, excluded_atoms=[2, 3, 4, 5, 6, 7])
  >>> print(bv.fraction_buried_volume)
  0.2962110976518822
  >>> bv.print_report()
  V_bur (%): 29.6

The mandatory atom index argument corresponds to the index of the central atom (1-indexed),
Ni in the example above.

By default, hydrogen atoms are excluded in the calculation. They can be added
by giving the keyword argument ``indclude_hs=True``. The metal atom is also
excluded, while the atoms of other ligands need to be given in the
``excluded_atoms`` list. The default sphere radius is 3.5 Å, but can be changed
with ``radius=<float>``. Default radii type is Bondi which are scaled by a
factor of 1.17. This can be changed with ``radii_type=<str>`` and
``radii_scale=<float>``. Custom radii can be supplied as a list with
``radii=<list>``.

Below is illustrated the buried volume of the phosphine ligand as calculated with
the code above, with the atoms of other ligands excluded in the ``excluded_atoms``
argument.

.. figure:: images/buried_volume/buried_volume.png
  :name: buried_volume
  :width: 50%

For more information, use ``help(BuriedVolume)`` or see the API:
:py:class:`BuriedVolume <morfeus.buried_volume.BuriedVolume>`

#####################
Quadrants and octants
#####################

The buried volume can be decomposed into contributions from quadrants and
octants using the
:py:meth:`octant_analysis <morfeus.buried_volume.BuriedVolume.octant_analysis>`
method. To get meaningful results, the system should be oriented in a
reproducible way. Orientation is acheived by specifiying the
``z_axis_atoms=<list>`` and ``xz_plane_atoms=<list>`` keyword arguments. For
more information on the orientation convention, see the original reference
:footcite:`falivene_sambvca_2016`.

z-axis orientation
  The list of atom indices from ``z_axis_atoms`` is used to define the
  direction of the z axis. The axis will be oriented from the geometric center
  of the atoms in the list to the metal atom.

xz-plane orientation
  The list of atom indices from ``xz_plane_atoms`` is used to define the
  orientation of the xz-plane. The coordinate system will be rotateed so that
  the geometric mean of the given atoms lies in the xz plane.

The results of the octant analysis is stored in the ``octants`` attribute,
giving the percent buried volume, the buried volume (in Å³) and the free volume (in Å³)
for each octant.

.. code-block:: python
  :caption: Quadrant and octant analysis

  >>> bv = BuriedVolume(elements, coordinates, 1,
  ... excluded_atoms=[2, 3, 4, 5, 6, 7],
  ... z_axis_atoms=[14],
  ... xz_plane_atoms=[11])
  >>> bv.octant_analysis()
  >>> bv.octants
  {'percent_buried_volume': {0: 0.0, ...},
   'buried_volume': {0: 0.0, ...},
   'free_volume': {0: 22.449297503777064, ...}}
  >>> bv.quadrants
  {'percent_buried_volume': {1: 27.53214685054044, ...},
   'buried_volume': {1: 12.361547111309221, ...},
   'free_volume': {1: 32.53704789624491, ...}}

The octants are numbered__ from 0–7 according to the Gray code and their signs
are given by the
:py:data:`OCTANT_SIGNS <morfeus.buried_volume.OCTANT_SIGNS>` dictionary.
The quadrants are numbered from 1–4 corresponding to the Roman numerals I–V and
the corresponding signs are given in the
:py:data:`QUADRANT_SIGNS <morfeus.buried_volume.QUADRANT_SIGNS>` dictionary.

.. __: https://en.wikipedia.org/wiki/Octant_(solid_geometry)

#############
Distal volume
#############

The **distal volume** is the volume of the ligand beyond the sphere. It can
be computed with the
:py:meth:`compute_distal_volume <morfeus.buried_volume.BuriedVolume.compute_distal_volume>`
method. Using ``method="sasa"`` is faster, while ``method="buried_volume"``
allows octant and quadrant decompositon of the distal volume. This will add
the entries ``distal_volume`` and ``molecular_volume`` to the results.

.. code-block:: python
  :caption: Distal volume

  >>> bv = BuriedVolume(elements, coordinates, 1,
  ... excluded_atoms=[2, 3, 4, 5, 6, 7],
  ... z_axis_atoms=[14],
  ... xz_plane_atoms=[11])
  >>> bv.distal_volume
  273.2150492473022
  >>> bv.octant_analysis()
  >>> bv.compute_distal_volume(method="buried_volume", octants=True)
  >>> bv.octants
  {'percent_buried_volume': {0: 0.0, ...},
   'buried_volume': {0: 0.0, ...},
   'free_volume': {0: 22.449297503777064, ...},
   'distal_volume': {0: 0.0, ...},
   'molecular_volume': {0: 0.0, ...}}

########
Plotting
########

A steric map can be plotted with
:py:meth:`plot_steric_map <morfeus.buried_volume.BuriedVolume.plot_steric_map>`
if the ``z_axis_atoms=<list>`` keyword has been given.

.. code-block:: python
  :caption: Steric map

  >>> from morfeus import BuriedVolume, read_xyz
  >>> elements, coordinates = read_xyz("1.xyz")
  >>> bv = BuriedVolume(elements, coordinates, 1, excluded_atoms=[2, 3, 4, 5, 6, 7], z_axis_atoms=[2])
  >>> bv.plot_steric_map()

.. image:: images/buried_volume/steric_map.png

Plots can be saved by passing the ``filename=<str>`` keyword argument.
:py:meth:`draw_3D <morfeus.buried_volume.BuriedVolume.draw_3D>` gives a
three-dimensional representation of the buried volume.

*******************
Command line script
*******************

The basic functionality is available through the command line script.

.. code-block:: shell
  :caption: Example

  $ morfeus buried_volume 1.xyz - 1 --excluded_atoms='[2,3,4,5,6,7]' - print_report
  V_bur (%): 29.6

**********
Background
**********

The percent of buried volume is a measure of the steric hindrance induced by a
ligand of a transition metal complex :footcite:`falivene_sambvca_2016`. A web
tool to calculate buried volumes, SambVca, was made available for scientific
purposes by Cavallo and co-workers in 2009 :footcite:`poater_sambvca_2009` with
version 2 in 2016 :footcite:`falivene_sambvca_2016`.

The approach of ᴍᴏʀғᴇᴜs differs somewhat from that in ref
:footcite:`falivene_sambvca_2016` in that points are generated uniformly in the
test sphere rather than considering voxels. The numerical results with standard
settings are the same though as shown by benchmarks on complexes 1-18 from ref
:footcite:`falivene_sambvca_2016`. Steric maps also match those in ref
:footcite:`falivene_sambvca_2016`.

.. footbibliography::


## morfeus/docs/cone_angle.rst

##########
Cone angle
##########

Exact cone angles are implemented as described by Allen and co-workers
:footcite:`bilbrey_exact_2013`.

******
Module
******

The ConeAngle class is provided to calculate and store the cone angles.

.. code-block:: python
  :caption: Example

  >>> from morfeus import ConeAngle, read_xyz
  >>> elements, coordinates = read_xyz("phosphines/PdPMe3.xyz")
  >>> cone_angle = ConeAngle(elements, coordinates, 1)
  >>> print(cone_angle.cone_angle)
  117.11012922937584
  >>> print(cone_angle.tangent_atoms)
  [5, 9, 12]
  >>> cone_angle.print_report()
  Cone angle: 117.1
  No. tangent atoms: 3
  >>> cone_angle.draw_3D()

The given atom index argument corresponds to the index of the central atom (1-indexed),
Pd in the example above.

The Bondi vdW radii are used in reference :footcite:`bilbrey_exact_2013`, but
radii from the CRC Handbook is the default here. It can be changed with
``radii_type=<str>`` with either ``crc`` or ``bondi``. Custom radii can passed
with ``radii=<list>``.

The default setting is ``method="libconeangle"``, which uses the fast
libconeangle__ package as a backend. If it is not installed, an internal
algorithm will be used (``method="internal"``), printing a warning.

.. figure:: images/cone_angle/PdPMe3_cone_angle.png
  :name: buried_volume
  :width: 30%

For more detailed information, use ``help(ConeAngle)`` or see the API:
:py:class:`ConeAngle <morfeus.cone_angle.ConeAngle>`.

.. __: https://github.com/kjelljorner/libconeangle

*******************
Command line script
*******************

The command line script provides access to the basic functionality through the
terminal.

.. code-block:: shell
  :caption: Example

  $ morfeus cone_angle PdPMe3.xyz - 1 - print_report
  Cone angle: 117.1
  No. tangent atoms: 3
  Tangent to: H6 H10 H13

**********
Background
**********

Cone angle is a method invented by Tolman for assessing the steric size of
ligands :footcite:`tolman_steric_1977`. The original Tolman cone angles for
phosphines have problems with asymmetric ligands and are not implemented in
this package. Instead, the exact cone angles :footcite:`bilbrey_exact_2013` are
used. These are also defined for multidentate ligands.

The method implemented in ᴍᴏʀғᴇᴜs is taken directly from the article by Allen
:footcite:`bilbrey_exact_2013`. The results have been benchmarked against the
original article and agree within numerical accuracy.

.. footbibliography::


## morfeus/docs/solid_angle.rst

###########
Solid angle
###########

Ligand solid angle and solid cone angles are implemented with a numerical recipe as
described by Guzei and Wendt :footcite:`guzei_2006`.

******
Module
******

The SolidAngle class is provided to calculate and store the solid angles.

.. code-block:: python
  :caption: Example

  >>> from morfeus import SolidAngle, read_xyz
  >>> elements, coordinates = read_xyz("phosphines/PdPMe3.xyz")
  >>> solid_angle = SolidAngle(elements, coordinates, 1)
  >>> print(solid_angle.cone_angle)
  112.53614024551955
  >>> print(solid_angle.solid_angle)
  2.794082404625142
  >>> print(solid_angle.G)
  22.234601305109027
  >>> solid_angle.print_report()
  Solid angle (sr): 2.794
  Cone angle (°): 112.536
  G: 22.235

The given atom index argument corresponds to the index of the central atom (1-indexed),
Pd in the example above.

The Bondi vdW radii are used in reference :footcite:`bilbrey_solid_2013`, but
radii from the CRC Handbook is the default here. It can be changed with
``radii_type=<str>``. Custom radii can be passed with ``radii=<list>``. The units
for the solid cone angle are in degrees, the solid angle is in steradians, and the
G parameter is in percent.

For more detailed information, use ``help(SolidAngle)`` or see the API:
:py:class:`SolidAngle <morfeus.solid_angle.SolidAngle>`.

*******************
Command line script
*******************

The command line script provides access to the basic functionality through the
terminal.

.. code-block:: shell
  :caption: Example

  $ morfeus solid_angle PdPMe3.xyz - 1 - print_report
  Solid angle (sr): 2.794
  Cone angle (°): 112.536
  G: 22.235

**********
Background
**********

The ligand solid angle, Ω, is the solid angle of the complete shadow cast by a
ligand when hypothetically illuminated from the metal center.
:footcite:`bilbrey_solid_2013` From Ω, a solid "cone" angle Θ can also be
calculated, which is analogous to Tolman's cone angle. The G parameter is a
measure of how much of the metal coordination sphere is shielded by the
ligands. :footcite:`guzei_2006`

ᴍᴏʀғᴇᴜs uses a numerical method, in a similar way to the Solid-G__ program, but
with different radii. The results have been benchmarked against the exact solid
angle program by Allen and co-workers, :footcite:`bilbrey_solid_2013` and agree
within numerical accuracy.

.. __: https://xray.chem.wisc.edu/solid-g/

.. footbibliography::


## morfeus/docs/sasa.rst

===============================
Solvent accessible surface area
===============================
Solvent accessible surface area (SASA), atomic SASA, and total volume inside the
SASA can be calculated.

******
Module
******

The SASA class calculates and stores the total and atomic SASA as well as the total
volume of the SASA.

.. code-block:: python
  :caption: Example

  >>> from morfeus import SASA, read_xyz
  >>> elements, coordinates = read_xyz("n-heptane.xyz")
  >>> sasa = SASA(elements, coordinates)
  >>> print(sasa.atom_areas[1])
  18.380429455791376
  >>> print(sasa.area)
  331.5607124071378
  >>> print(sasa.volume)
  475.5699458352845

The ``atom_areas`` dictionary contains the atomic SASAs indexed from 1. The type of
radii can be changed with the keyword argument ``radii=<str>``  and custom
radii can be supplied with ``radii=<list>``. The probe radius is changed with
``probe_radius=<float>``.

For more detailed information, use ``help(SASA)`` or see the API:
:py:class:`SASA <morfeus.sasa.SASA>`.

*******************
Command line script
*******************

The command-line script outputs total SASA and volume as well as SASA per atom.

.. code-block:: shell
  :caption: Example

  $ morfeus sasa PdPMe3.xyz - - print_report
  Probe radius (Å): 1.4
  Solvent accessible surface area (Å²): 288.3
  Volume inside solvent accessible surface (Å³): 410.7
  $ morfeus sasa PdPMe3.xyz - - print_report --verbose=True
  Probe radius (Å): 1.4
  Solvent accessible surface area (Å²): 288.3
  Volume inside solvent accessible surface (Å³): 410.7
  Symbol    Index     Area (Å²)
  Pd        1         91.8
  P         2         0.0
  C         3         13.4
  H         4         18.2
  H         5         15.6
  H         6         18.2
  C         7         13.5
  H         8         18.2
  H         9         15.6
  H         10        18.2
  C         11        13.5
  H         12        18.2
  H         13        18.2
  H         14        15.6

**********
Background
**********

The solvent accessible surface area (SASA) is a measure of how much of the area of a
molecule is available to the solvent. The atomic SASA can be used as a measure
of the steric availability of an atom. ᴍᴏʀғᴇᴜs uses a modified version of the
method of Shrake and Rupley :footcite:`shrake_environment_1973` where a
constant surface density of points is used instead of a fixed number of points
regardless of the atom area. The atomic SASA and volumes are computed as
described by Eisenhaber *et al.* :footcite:`eisenhaber_double_1995`. ᴍᴏʀғᴇᴜs is
not optimized for larger molecules and other programs are recommended for,
*e.g.*, proteins.

.. footbibliography::


## morfeus/docs/dispersion.rst

=====================
Dispersion descriptor
=====================

The universal quantitative dispersion descriptor
:footcite:`pollice_universal_2019` can be calculated either approximately based
on tabulated van der Waals (vdW) radii, or more accurately based on computed electron density
isosurfaces. Dispersion is modelled with the D3
:footcite:`grimme_consistent_2010` or D4 :footcite:`caldeweyher_extension_2017`
methods (the latter requires an external program).

***************
Preparing input
***************

There are two options for using surfaces based on the electron density.

####
Cube
####

Electron density in Gaussian cube format. Cube files can be generated by
various quantum-chemical programs, including Gaussian_.

########
Multiwfn
########

Exported surface from the `Multiwfn program`_ generated with the surface
analysis module (option 12 in the main menu). After generating the surface, it
should be exported to a file using the hidden option 66. This generates a file,
"vtx.pdb" that can be read by ᴍᴏʀғᴇᴜs. For more information, see Section 3.15.4
of the `Multiwfn manual`_.

******
Module
******

The Dispersion class is provided to calculate and store the dispersion
descriptors.

.. code-block:: python
  :caption: Example

  >>> from morfeus import Dispersion, read_geometry
  >>> elements, coordinates = read_geometry("corannulene.xyz")
  >>> disp = Dispersion(elements, coordinates)
  >>> disp.print_report()
  Surface area (Å²): 284.6
  Surface volume (Å³): 290.0
  P_int (kcal¹ᐟ² mol⁻¹ᐟ²): 20.8
  >>> disp.atom_p_int[1]
  30.19400992973631

By default, the molecular surface is constructed from vdW spheres and an
internal D3 code is used. The choice of vdW radii can be changed from the
default of ``rahm`` with ``radii_type=<str>``. Custom radii can be supplied
with ``radii=<list>``. Density of points on the vdW surface is controlled with
``density=<float>``. Dispersion coefficients can be read from the output of
Grimme's D3 and D4 programs with the
:py:meth:`load_coefficients <morfeus.dispersion.Dispersion.load_coefficients>`
method. To suppress the internal D3 code, set ``calculate_coefficients=False``
appropriately. To use another surface, suppress the vdW surface creation with
``point_surface=False`` and use the
:py:meth:`surface_from_cube <morfeus.dispersion.Dispersion.surface_from_cube>`
or
:py:meth:`surface_from_multiwfn <morfeus.dispersion.Dispersion.surface_from_multiwfn>` methods.

.. code-block:: python
  :caption: Example with external cube and coefficients files

  >>> elements, coordinates = read_xyz("corannulene.xyz")
  >>> disp = Dispersion(elements, coordinates, point_surface=False)
  >>> disp.load_coefficients("d4_corannulene", "d4")
  >>> disp.surface_from_cube("corannulene.cub")
  >>> disp.compute_p_int()
  >>> disp.print_report()
  Surface area (Å²): 248.0
  Surface volume (Å³): 247.8
  P_int (kcal¹ᐟ² mol⁻¹ᐟ²): 27.2
  >>> disp.atom_p_int[1]
  40.907980526799534

To exclude atoms from the calculation, the atom indices (starting at 1) should
be provided with ``excluded_atoms=<list>``. This can for example be used to
calculate substitutent P\ :sub:`int` values.

Grimme's `dftd4 program`_ can be used to calculate the dispersion coefficients
with the D4 method. The accompanying dftd4 python package must also be
installed in the same Python environment as Morfeus. An example is given below:

.. code-block:: python
  :caption: Example with Grimme's dftd4 code

  >>> elements, coordinates = read_xyz("pme3.xyz")
  >>> disp = Dispersion(elements, coordinates, compute_coefficients=False)
  >>> disp.compute_coefficients(model="gd4")
  >>> disp.compute_p_int()
  >>> disp.print_report()
  Surface area (Å²): 178.4
  Surface volume (Å³): 157.8
  P_int (kcal¹ᐟ² mol⁻¹ᐟ²): 20.1

The D4 model is available with "gd4" and the internal D3 code with "id3". The
maximum order of the dispersion coefficients can be set with the keyword
argument "order", but should be left by the non-expert user at the default
setting of 8 (*i.e.* C\ :sub:`6` and C\ :sub:`8`)

For more detailed information, use ``help(Dispersion)`` or see the API:
:py:class:`Dispersion <morfeus.dispersion.Dispersion>`

.. note::

  Use the command line flag ``--molc6`` to get the dftd4 program to print the
  dispersion coefficients.

*******************
Command line script
*******************

The command line script provides access to the basic functionality through
the terminal.

.. code-block:: shell
  :caption: Example

  $ morfeus dispersion tBu.xyz - - print_report
  Surface area (Å²): 142.6
  Surface volume (Å³): 121.2
  P_int (kcal¹ᐟ² mol⁻¹ᐟ²): 13.2

**********
Background
**********

The 🍺P\ :sub:`int` dispersion descriptor was introduced by Pollice and Chen as
a quantitative descriptor for dispersion interactions
:footcite:`pollice_universal_2019`. ᴍᴏʀғᴇᴜs can calculate P\ :sub:`int` based
on an electron density isosurface, as in the original article. In addition, we
have found that a very fast method based on surfaces constructed from vdW radii
correlates well with P\ :sub:`int` from electron densities, at a fraction of the
cost.

.. todo::
  add figure here benchmarks/local_force/benchmark.png

.. footbibliography::

.. _dftd4 program: https://github.com/grimme-lab/dftd4
.. _Gaussian: https://gaussian.com/cubegen/
.. _Multiwfn program: http://sobereva.com/multiwfn/
.. _Multiwfn manual: http://sobereva.com/multiwfn/Multiwfn_manual.html


## morfeus/docs/pyramidalization.rst

================
Pyramidalization
================

Pyramidalization can be calculated as described by Agranat and Radhakrishnan
:footcite:`radhakrishnan_measures_1991` and Gavrish
:footcite:`gavrish_approximate_2012`.

******
Module
******

The Pyramidalization class calculates and stores the pyramidalization values.

.. code-block:: python
  :caption: Example

  >>> from morfeus import read_geometry, Pyramidalization
  >>> elements, coordinates = read_geometry("pyr.xyz")
  >>> pyr = Pyramidalization(coordinates, 1)
  >>> pyr.P
  0.9382253758236183
  >>> pyr.P_angle
  7.578832545944509

The first value is the *P* value according to Agranat and Radhakrishnan while
the second one is that of Gavrish.  In the example above, the index of the
pyramidalized atom is given, together with the coordinates of the molecule.
Mᴏʀғᴇᴜs then needs to determine the neighbors of this atom in order to
calculate the appropriate angles (see `Background`_). Either the indices of the
neighbors can be given explicitly with ``neighbor_indices=<list>`` or Mᴏʀғᴇᴜs
will try to determine the neighbors automatically. The strategy is controlled
by the ``method=<str>`` keyword argument:

``method="distance"``
  This is the default method that simply selects the three atoms closest in
  space.

``method="connectivity"``
  Connectivity is determined from covalent radii. This method requires either
  that ``radii`` or ``elements`` are given. The Pyykko covalent radii are used
  by default.

For more detailed information, use ``help(Pyramidalization)`` or see the API:
:py:class:`Pyramidalization <morfeus.pyramidalization.Pyramidalization>`.

*******************
Command line script
*******************

The functionality is also available from the command line.

.. code-block:: shell
  :caption: Example

  $ morfeus pyramidalization pyr.xyz - 1 - print_report
  P: 0.938
  P_angle: 7.579

**********
Background
**********

#########################
Agranat and Radhakrishnan
#########################

Pyramidalization can be calculated for any tetracoordinate atom as described in
:footcite:`radhakrishnan_measures_1991`. Here, the pyramidalization *P* is
calculated from the two angles *ɑ* and *θ* defined in the figure

.. math::

  P = \sin{\theta} \bullet \cos{\alpha}

The angle *θ* is measured between the two vectors **a** and **b** going from
the pyramidalized atom to two of the substituent atoms A and B. The angle *ɑ*
is measured between the vector **c** going from the phosphorus atom to the
third substituent atom C, and the normal vector **u** to the plane defined by
**a** and **b**. An important alteration to the original recipe is made for
extreme cases of pyramidalization, as suggested by Tobias Gensch. When the
angle between vector **c** and the sum of vectors **a** and **b** is acute, the
*α* angle is taken as negative. If *α* is negative, the final pyramidalization
value *P* is taken as 2 − *P* and can therefore be larger than unity. There are
three possible values of *α* that can be obtained by choosing **a** and **b**
differently. The sign of *α* is taken from the average of these three angles.

.. figure:: images/pyramidalization/pyramidalization.svg
  :name: fig_pyramidalization
  :width: 100%

  Definition of α angle as negative for extreme pyramidalization.

#######
Gavrish
#######

An alternative and related measure of pyramidalization is due to Gavrish
:footcite:`gavrish_approximate_2012`:

.. math::

  P = \sqrt{360° - \sum{\theta}}

where *θ* is the bond angle in the figure and the sum is over the three
possible bond angles.

.. footbibliography::


## morfeus/docs/bite_angle.rst

==========
Bite angle
==========

The bite angle is calculated as the angle between the two chelating ligand
atoms and the metal atom of a bidentate ligand. :footcite:`durand_2019`

******
Module
******

The BiteAngle class calculates the bite angle by from the coordinates, the
index of the metal atom and the indices of the two coordinating atoms.

.. code-block:: python
  :caption: Example

  >>> from morfeus import BiteAngle, read_xyz
  >>> elements, coordinates = read_xyz("bpy.xyz")
  >>> ba = BiteAngle(coordinates, 1, 2, 3)
  >>> ba.angle
  77.29254645757716

For more detailed information, use ``help(BiteAngle)`` or see the API:
:py:class:`BiteAngle <morfeus.bite_angle.BiteAngle>`

####################
Inverted bite angles
####################

The bite angle can become 'inverted' if it goes beyond 180°. This cannot be
detected automatically, so the user has to supply a ``ref_vector`` that should
point in the 'direction' of the ligand. As a convenience, the vector can be
constructed automatically from the metal atom to the geometric mean of a set of
given ``ref_atoms``.

In the example below, the bipyridine ligand has been artificially distorted to
give an inverted bite angle. The metal atom index is 1, and the indices of the
coordinating atoms are 2 and 3. The reference vector is constructed from the
metal atom to the geometric mean of the two reference atoms, 4 and 17.

.. figure:: images/bite_angle/inverted.png
  :name: fig_inverted
  :width: 80%

.. code-block:: python
  :caption: Inverted

  >>> elements, coordinates = read_xyz("bpy_inverted.xyz")
  >>> ba = BiteAngle(coordinates, 1, 2, 3, ref_atoms=[4, 17])
  >>> ba.angle
  198.39710046622645
  >>> ba.inverted
  True

*******************
Command line script
*******************

The basic functionality is available through the command line script.

.. code-block:: shell
  :caption: Example

  $ morfeus bite_angle bpy.xyz - 1 2 3 - angle
  77.29254645757716

.. code-block:: shell
  :caption: Example inverted

  $ morfeus bite_angle bpy_inverted.xyz - 1 2 3 --ref_atoms='[4, 17]' - angle
  198.39710046622645

**********
Background
**********

The bite angle has a long history of use as a ligand descriptor.
:footcite:`durand_2019`. ᴍᴏʀғᴇᴜs extends to inverted bite angles, which
correspond to a bite angle above 180°.

.. figure:: images/bite_angle/bite_angle.png
  :name: fig_bite_angle
  :width: 80%

.. footbibliography::


## morfeus/docs/notes.rst

==============
Notes on usage
==============

************
Atom indices
************

The ᴍᴏʀғᴇᴜs API uses atom indices starting from 1, so called one-based
indexing. This means that the first atom in a molecule has index 1. In
contrast, Python generally uses zero-based indexing for lists and arrays.

.. code-block:: none
  :caption: One-based indexing from xyz file
  :emphasize-lines: 3

  14
  PdPMe3
  Pd         -0.743397 -0.000992 -1.518770                # Atom with index 1
  P           1.005896  0.002102 -0.163618                # Atom with index 2
  ...

We believe that one-based indexing is more intuitive for the user when, *e.g.*,
getting indices visually from molecular viewers. To accomodate for this
difference, atom properties in morfeus are given as dictionaries, with keys
corresponding to the atom indices. These can easily be turned into regular
lists and used with zero-indexing if needed:

.. code-block:: python
  :caption: Accessing atom properties

  >>> from morfeus import SASA, read_geometry
  >>> elements, coordinates = read_geometry("Et.gjf")
  >>> sasa = SASA(elements, coordinates)
  >>> sasa.atom_areas
  {1: 22.489947408719903,
  2: 19.180448148100027,
  3: 22.529947315182724,
  ...
  >>> list(sasa.atom_areas.values())
  [22.489947408719903,
  19.180448148100027,
  22.529947315182724,
  ...

**************
Geometry files
**************

Many features of ᴍᴏʀғᴇᴜs make use of atomic numbers/symbols and coordinates.
These can be read from geometry files, and currently the files formats ``gjf``
(Gaussian input file) and ``xyz`` (XMOL) are supported. These files can be
read with two different functions. There is also the
:py:func:`read_geometry <morfeus.io.read_geometry>`
function that will try to guess the file type based on its suffix. If the
cclib__ package is installed, it can be used to read many file formats.

====== =============================================
Format Function
====== =============================================
gjf    :py:func:`read_gjf <morfeus.io.read_gjf>`
xyz    :py:func:`read_xyz <morfeus.io.read_gjf>`
\*     :py:func:`read_cclib <morfeus.io.read_cclib>`
====== =============================================

.. __: https://github.com/cclib/cclib

*****
Radii
*****

ᴍᴏʀғᴇᴜs makes extensive use of atomic radii in calculating the different
descriptors. There are mainly two types of radii: van der Waals (vdW) and covalent.

#######
Options
#######

=============================================== =================================================
vdW                                             Covalent
=============================================== =================================================
:py:data:`alvarez <morfeus.data.radii_alvarez>` :py:data:`pyykko <morfeus.data.cov_radii_pyykko>`
:py:data:`bondi <morfeus.data.radii_bondi>`
:py:data:`crc <morfeus.data.radii_crc>`
:py:data:`rahm <morfeus.data.radii_rahm>`
:py:data:`truhlar <morfeus.data.radii_truhlar>`
=============================================== =================================================

- Default vdW radii are from the curated collection in the CRC handbook
- The only option for covalent radii at the moment is those from pyykko
- Rahm radii are a special type derived from electron density calculation. They
  are the default for dispersion descriptor calculations.

Changing the type of radii is done by specifying the ``--radii_type`` keyword
argument.

#######
Sources
#######

The data is extracted from the excellent mendeleev__ package.

.. __: https://github.com/lmmentel/mendeleev/

***************
Without display
***************

Matplotlib may cause problems on computers without displays, e.g., nodes on
computer clusters. This can be solved by changing the plotting backend to
"agg". This could be done at the top of the Python script using ᴍᴏʀғᴇᴜs:

.. code-block:: python

  import matplotlib
  matplotlib.use('Agg')

Alternatively, set the environment variable in the shell before launching the
script (Linux example):

.. code-block:: shell

  export MPLBACKEND="agg"

## morfeus/docs/xtb.rst

===
XTB
===

Electronic parameters can be calculated at the GFN1-xTB, GFN2-xTB or PTB levels
using the xtb__ package (which needs to be installed).

******
Module
******

The XTB class is used to calculate electronic properties, such as, among others, bond orders, 
atomic charges, total, HOMO and LUMO energies, dipole moments, ionization potential, electron affinity.

.. code-block:: python
  :caption: Example

  >>> from morfeus import XTB, read_xyz
  >>> elements, coordinates = read_xyz("ammonia.xyz")
  >>> xtb = XTB(elements, coordinates)
  >>> xtb.get_bond_order(1, 2)
  0.978270297857
  >>> xtb.get_charges()
  {1: -0.4344091, 2: 0.14479795, 3: 0.14480895, 4: 0.1448022}
  >>> xtb.get_energy()
  -4.42584832
  >>> xtb.get_homo()
  -0.3847857
  >>> xtb.get_dipole()
  array([ 0.38617738,  0.48077917, -0.31171428])
  >>> xtb.get_ip()
  11.6047
  >>> xtb.get_ip(corrected=False)
  16.4502
  >>> xtb.get_ea()
  -11.121

In addition, global and local descriptors from conceptual density functional
theory can also be calculated.

.. code-block:: python
  :caption: Example

  >>> xtb.get_global_descriptor("electrophilicity")
  0.0012869003485041107
  >>> xtb.get_global_descriptor("nucleophilicity")
  -11.6047
  >>> xtb.get_fukui("electrophilicity")
  {1: 0.205, 2: 0.265, 3: 0.265, 4: 0.265}
  >>> xtb.get_fukui("nucleophilicity")
  {1: 0.428, 2: 0.191, 3: 0.191, 4: 0.191}

Properties related to the solvation are also available with the XTB class.

.. code-block:: python
  :caption: Example

  >>> xtb = XTB(elements, coordinates, solvent="water")
  >>> xtb.get_solvation_energy(unit="kcal/mol")
  -4.644374184273
  >>> xtb.get_solvation_h_bond_correction(unit="kcal/mol")
  -2.808641396951

The version of GFNn-xTB or the PTB method can be set using ``method=<int>|<str>`` with versions 1 and
2 and the additional method "ptb" currently supported. The molecular charge, number of unpaired electrons 
and solvent are also set while initializing the class, with ``charge=<int>``, ``n_unpaired=<int>`` and 
``solvent=<str>`` respectively.

A empirical correction term, given by Grimme and co-workers :footcite:`neugebauer_benchmark_2020`, 
is applied for the calculation of the ionization potential and electron affinity, which also 
affects some of the global and local descriptors. It can be disabled with ``corrected=False``. 

For more information and a list of all available electronic properties, 
use ``help(XTB)`` or consult the API:
:py:class:`XTB <morfeus.xtb.XTB>`.

*******************
Command line script
*******************

The command line script gives access to the basic functionality from the
terminal.

.. tab:: Get charge

  .. code-block:: shell

    $ morfeus xtb ammonia.xyz - - get_charges - 1
    -0.4344091

.. tab:: Change version

  .. code-block:: shell

    $ morfeus xtb ammonia.xyz - --method='"1"' - get_charges - 1
    -0.57697413

**********
Background
**********

###############################
Descriptors from conceptual DFT
###############################

ᴍᴏʀғᴇᴜs can compute both simple electronic parameters such as charges, HOMO
and LUMO energies, and bond orders, as well as descriptors from conceptual
density functional theory :footcite:`domingo_applications_2016`.
The following global descriptors are available:

* Electrophilicity: :math:`\omega`
* Nucleophilicity: :math:`N`
* Electrofugality: :math:`\nu_{electrofugality}`
* Nucleofugality: :math:`\nu_{nucleofugality}`

They are calculated according to the following definitions
:footcite:`domingo_applications_2016,ayers_indices_2005`:

.. math::

  \omega &= \frac{(IP + EA)^2}{8(IP - EA)} = \frac{\mu^2}{2\eta}

  N &= -IP

  \nu_{electrofugality} &= \frac{(3IP - EA)^2}{8(IP - EA)} = IP + \omega

  \nu_{nucleofugality} &= \frac{(IP - 3EA)^2}{8(IP - EA)} = -EA + \omega

Where :math:`IP` is the ionization potential, :math:`EA` is the electron
affinity, :math:`\mu` is the chemical potential and :math:`\eta` is the
hardness given by

.. math::

  \mu &= - \frac{IP + EA}{2}

  \eta &= IP - EA

The Fukui coefficients are calculated via the finite differences
approach using the atomic charges from *xtb*. These include:

* Electron removal (nucleophilicity): :math:`f^-`
* Electron addition (electrophilicity): :math:`f^+`
* Radical attack: :math:`f`
* Dual descriptor: :math:`f^{(2)}`

which are calculated as follows:

.. math::

  f^- &= q_{N-1} - q_{N}

  f^+ &= q_{N} - q_{N+1}

  f &= (q_{N-1} - q_{N+1}) / 2

  f^{(2)} &= f^+ - f^- = 2 q_{N} - q_{N+1} - q_{N-1}

The Fukui coefficient for electron removal is also called the coefficient for
electrophilic attack and is a measure of nucleophilicity. The coefficient for
electron addition is also called the coefficient for nucleophilic attack and is
a measure of electrophilicity. The somewhat unintuitive names is due to the
notion that *another* molecule would attack as a nucleophile/electrophile. The
coefficient for radical attack is often used for radical reactivity. In
addition, the local electrophilicity (:math:`l_{\omega}`) and nucleophilicity
(:math:`l_N`) are also available and calculated as
:footcite:`oller_global_2018`:

.. math::

  l_{\omega} &= - \frac{\mu}{\eta}f + \frac{1}{2}(\frac{\mu}{\eta})^2 f^{(2)}

  l_N &= f^-

####################
Solvation properties
####################

The solvation free energy :math:`\Delta G_{solv}` is calculated with *xtb* 
using the ALPB model :footcite:`ehlert_robust_2021`. Because the solvent is 
described implicitly as a dielectric medium, the hydrogen bonding (HB) between solute 
and solvent needs to be accounted for separately. The HB correction 
is calculated with: 

.. math::

  \Delta G^{HB} = \sum_{A}^{N} \Delta G_{A}^{HB}

where :math:`\Delta G_{A}^{HB}` is the atomic contribution to the HB correction
and approximated in the ALPB model as :footcite:`ehlert_robust_2021`:

.. math::

  \Delta G_{A}^{HB} ≈ - g_{A}^{HB} q_{A}^{2} \frac{\sigma_{A}}{4\pi(R_{A}^{surf})^{2}}

where :math:`g_{A}^{HB}` is the HB strength of the atom, :math:`q_{A}` its charge, 
:math:`\sigma_{A}` its SASA, and :math:`R_{A}^{surf}` the atom vdW radius
combined with the solvent probe radius.


.. footbibliography::

.. __: https://github.com/grimme-lab/xtb
