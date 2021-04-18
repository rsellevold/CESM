import os

modules = ["nclf","icesheetf"]
for m in modules:
    os.system(f"f2py -c lib/{m}.F90 -m {m} --f90flags='-fopenmp -O3'")

objects = os.popen("ls *.so").read().split("\n")[:-1]
for obj in objects:
    os.system(f"mv {obj} lib/{obj}")
