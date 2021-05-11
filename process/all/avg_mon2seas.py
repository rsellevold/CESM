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

    fdir = []
    for c in comp:
        fdir.append(f"{config['run']['folder']}/{config['run']['name']}/{c}/hist/monavg")
    varlist = lib.mpimods.make_varlist2(fdir)

    jobs = []
    for i in range(len(varlist)):
        arg = varlist[i]
        p = mpi.Process(target=lib.averages.seasavg, args=(arg[0],arg[1],))
        jobs.append(p)
        p.start()

if __name__ == "__main__":
    main()
