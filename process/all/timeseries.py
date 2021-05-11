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
    times = sys.argv[2]
    times = times.split(",")

    fdir = []
    for c in comp:
        for seas in times:
            fdir.append([f"{config['run']['folder']}/{config['run']['name']}/{c}/hist/{seas}",seas])

    regions = config["timeseries"]["regions"]
    varlist = lib.mpimods.make_varlist3(fdir,regions)

    jobs = []
    for i in range(len(varlist)):
        arg = varlist[i]
        print(arg)
        p = mpi.Process(target=lib.proc.ts, args=(arg[0],arg[2],arg[1],arg[3],))
        jobs.append(p)
        p.start()


if __name__ == "__main__":
    main()
