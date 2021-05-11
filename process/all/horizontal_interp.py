import multiprocessing as mpi
import yaml
with open("config.yml","r") as f:
    config = yaml.safe_load(f)
import os,sys
sys.path.append(f"{config['machine']['codepath']}")

import lib


def interpolate(fdir, var, gridfile):
    fname = f"{fdir}/{var}"
    os.system(f"cdo remapbil,{gridfile} {fname} {fname[:-3]}2.nc")
    os.system(f"mv {fname[:-3]}2.nc {fname}")


def make_varlist(fdir):
    varlist = []
    for i in fdir:
        vlist = os.popen(f"ls {i}").read().split("\n")[:-1]
        for v in vlist:
            varlist.append([i,v])
    return varlist


def main():
    comp = sys.argv[1]
    comp = comp.split(",")
    times = sys.argv[2]
    times = times.split(",")
    gridfile = sys.argv[3]

    fdir = []
    for c in comp:
        for seas in times:
            fdir.append(f"{config['run']['folder']}/{config['run']['name']}/{c}/hist/{seas}")

    varlist = make_varlist(fdir)

    jobs = []
    for i in range(len(varlist)):
        arg = varlist[i]
        p = mpi.Process(target=interpolate, args=(arg[0],arg[1],gridfile,))
        jobs.append(p)
        p.start()


if __name__ == "__main__":
    main()
