import yaml
with open("config.yml","r") as f:
    config = yaml.safe_load(f)
import os,sys
sys.path.append(f"{config['machine']['codepath']}")

from mpi4py import MPI
import lib


def main():
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    tasks = sys.argv[1]
    tasks = tasks.split(",")

    tasks = lib.mpimods.check_varlist(tasks, size)

    for i in range(int(len(tasks)/size)):
        if rank==0:
            data = [(i*size)+k for k in range(size)]
        else:
            data = None
        data = comm.scatter(data, root=0)
        var = tasks[data]

        if var=="na_jet":
            lib.climateind.northatlantic_jet(config)
        if var=="amo":
            lib.climateind.amo(config)
        if var=="GBI":
            lib.climateind.GBI(config)
        else:
            None

main()
