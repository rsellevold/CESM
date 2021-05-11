import multiprocessing as mpi
import yaml
with open("config.yml","r") as f:
    config = yaml.safe_load(f)
import os, sys
sys.path.append(f"{config['machine']['codepath']}")

import lib


def main():
    comp = sys.argv[1]
    comp = comp.split(",")
    
    fdir = []
    for c in comp:
        fdir.append(f"{config['run']['folder']}/{config['run']['name']}/{c}/hist/dayavg")
    varlist = lib.mpimods.make_varlist2(fdir)

    jobs = []
    for i in range(len(varlist)):
        p = mpi.Process(target=lib.averages.monavg, args=(varlist[i][0], varlist[i][1],))
        jobs.append(p)
        p.start()


if __name__ == "__main__":
    main()
