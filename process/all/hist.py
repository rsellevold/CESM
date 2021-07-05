import multiprocessing as mpi
import yaml
with open("config.yml","r") as f:
    config = yaml.safe_load(f)
import os,sys
sys.path.append(f"{config['machine']['codepath']}")

import lib



def main():
    comp = sys.argv[1]
    comp = comp.split(",")
    varlist = lib.mpimods.make_varlist(config,comp)

    jobs = []
    for i in range(len(varlist)):
        arg = varlist[i]
        p = mpi.Process(target=lib.history.mergehist, args=(config,arg[0],arg[2],arg[1],arg[3],))
        jobs.append(p)
        p.start()

if __name__ == "__main__":
    main()
