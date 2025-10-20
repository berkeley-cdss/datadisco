---
title: Software and Modules
---

## Overview
Savio provides a wide range of pre-installed software maintained by Berkeley Research Computing (BRC) system administrators and consultants. This includes compilers, interpreters, tools for data analysis, visualization, bioinformatics, computational biology, and more.

Software is accessed through Environment Modules, which dynamically set environment variables (e.g., PATH, LD_LIBRARY_PATH) so that different tools and versions can coexist.

After Savio’s Rocky Linux 8 upgrade (July 2024), modules are managed by the Lmod Environment Module system. In addition to familiar commands such as module avail, module load, and module unload, a new command—module spider—helps you find dependencies and compatible versions of software packages.

## Accessing Software Using Environment Modules
Use the `module` command to view, load, or unload available software:
- `module avail`: List all available modulefiles in your MODULEPATH.
- `module list`: Show currently loaded modules.
- `module load <modulefile>`: Load one or more modules.
- `module unload <modulefile>`: Unload one or more modules.
- `module swap <modulefile1> <modulefile2>`: Replace one loaded module with another.
- `module show <modulefile>`: Display configuration info for a module.
- `module whatis <modulefile>`: Show a summary description.
- `module keyword <key>`: Search for modules containing specific keywords.
- `module purge`: Unload all currently loaded modules.
For more details, run `man module` on Savio.

## Default Modules
If you load a module without specifying a version (e.g., `module load python`), the default version (marked `(D)`) is loaded. The loaded modules are marked `(L)` in the `module avail` output.

For reproducibility, always specify versions explicitly:

## Hierarchical Module Structure
Savio organizes modules hierarchically. Some modules (e.g., C libraries) appear only after loading their parent compiler module.
```bash
module load gcc/13.2.0
module avail
```
Use `module spider` to discover hidden modules or dependencies.

You can also search all available modules:
```bash
find /global/software/rocky-8.x86_64/modfiles -type d -exec ls -d {} \;
```
Or narrow results with `grep`:
```bash
find /global/software/rocky-8.x86_64/modfiles -type d -exec ls -d {} \; | grep hdf5
```

## Example: Loading and Managing Modules
```bash
module purge
module load gcc/13.2.0 openmpi/4.1.6
module load intel-oneapi-mkl
module list
```
To unload and switch:
```bash
module unload openmpi
module switch intel-oneapi-mkl netlib-lapack
module list
```
Use `module show` for configuration details and `module whatis` for summaries.

## Software Provided on Savio
To view the full, up-to-date list, run:
```bash
module avail
```
The current common categories are:
- **Development Tools**: Emacs, Vim, make, cmake, Ninja, Bazel, Spack
- **Version Control**: Git, Mercurial
- **Languages & Compilers**: Anaconda, GCC, Intel oneAPI, LLVM, Java, R, Python, MATLAB, Julia, Rust
- **Math & Statistics**: MKL, FFTW, LAPACK, ScaLAPACK, GSL, OpenBLAS, Eigen
- **I/O & Data**: HDF5, NetCDF, protobuf, LevelDB
- **Visualization & ML**: MATLAB, Gnuplot, TensorFlow, PyTorch, Scikit-learn
- **Bioinformatics**: ABRicate, BLAST, Bowtie, FastQC, GROMACS, RELION, Snippy
- **Utilities**: tmux, parallel, iperf3, rsync, rclone
- **Publishing**: TeX Live, Doxygen

## Installing Your Own Software
If software is unavailable on Savio, you can install it yourself.

**Requirements**
- Must run on Rocky Linux 8 (x86_64).
- Must install without root privileges.
- Must fit within your HOME (30 GB) or group directory quota.
- Should use existing compilers/libraries (GCC or Intel).
- Must comply with software license terms for cluster usage.

There are two main installation locations for your software:
- Personal Use: `/global/home/users/<username>`
- Group-wide Use: `/global/home/groups/<groupname>`


For scripting languages, install using built-in package managers:
- **Python**: `pip install --user <package>` or use Conda
- **R**: `install.packages("<package>")`
- **Perl**: `cpanm --local-lib=~/perl5 <package>`
Conda can also install non-Python software (e.g., R, Julia, Java).

## Using Specialized Software
Here are some links to introductory guides on the use of various software applications on Savio.

- [Using Python](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/software/using-software/using-python-savio/):
An introduction to using Python, a programming language widely used in scientific computing, on Savio.
- [Using R](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/software/using-software/using-r-savio/):
An introduction to using R, a language and environment for statistical computing and graphics, on Savio.
- [Using MATLAB](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/software/using-software/using-matlab-savio/):
An introduction to using MATLAB, a matrix-based, technical computing language and environment for solving engineering and scientific problems, on Savio.
- [Using Mathematica](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/software/using-software/using-mathematica-savio/):
An introduction to using Mathematica on Savio.
- [Using Apptainer (Singularity)](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/software/using-software/using-singularity-savio/):
An introduction to using Apptainer (formerly Singularity), a software tool that facilitates the movement of software applications and workflows between various computational environments, on Savio.
- [Using Julia](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/software/using-software/using-julia/)
- [Using Perl](https://docs-research-it.berkeley.edu/services/high-performance-computing/user-guide/software/using-software/using-perl-savio/)