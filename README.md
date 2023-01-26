# EuXFEL Data Acquisition module



# Bmad-X

Author: Christian Grech (christian.grech@desy.de), Farzad Jafarinia (farzad.jafarinia@desy.de), Vladimir Rybnikov (vladimir.rybnikov@desy.de)

A Software module to automatically acquire data in one of the SASE beamlines and to convert raw DAQ files to hdf5.

Installation
============

Installation is restricted to Linux PCs connected the DESY network.
```shell
git clone https://github.com/cgre23/XFEL-DAQ.git
conda env create -f environment.yml
conda activate python37
pip install --no-dependencies -e .
```
