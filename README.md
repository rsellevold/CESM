# CESMpy

This repository contains useful code for processing and plotting output from the Community Earth System Model.


## Set up python environment
The easiest way to get started is by using conda (e.g. [miniconda](https://docs.conda.io/en/latest/miniconda.html)). Create a new environment with

**conda env create -f pythonenv.yml**

You may want to edit the name and prefix in _pythonenv.yml_.


## Create analysis directory
To analyze a case, start by using

```python
python new_case.py <full path to analysis directory>
```

In this new directory you should start by editing _config.yml_. After, run

```python
python main_proc.py
```

The file main_proc is a bash file that can either be submitted to batch (to use MPI), or run with bash.
