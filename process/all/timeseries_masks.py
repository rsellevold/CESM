import yaml
with open("config.yml","r") as f:
    config = yaml.safe_load(f)
import os,sys
sys.path.append(f"{config['machine']['codepath']}")

from mpi4py import MPI
import xarray as xr
import lib


def masklist(masks):
    keylist = list(masks.keys())
    if "time_bnds" in keylist: keylist.remove("time_bnds")
    return keylist

def make_varlist(comps,times,maskList):
    fdir = f"{config['run']['folder']}/{config['run']['name']}"
    varlist = []
    for c in comps:
        for t in times:
            f = f"{fdir}/{c}/hist/{t}"
            vlist = os.popen(f"ls {f}").read().split("\n")[:-1]
            for v in vlist:
                for m in maskList:
                    varlist.append([f, v, t, m])
    return varlist


def main():
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    comp = sys.argv[1]
    comp = comp.split(",")
    times = sys.argv[2]
    times = times.split(",")
    fmask = sys.argv[3]

    masks = xr.open_dataset(fmask)
    maskList = masklist(masks)

    varlist = make_varlist(comp,times,maskList)
    varlist = lib.mpimods.check_varlist(varlist,size)

    for i in range(int(len(varlist)/size)):
        if rank==0:
            data = [(i*size)+k for k in range(size)]
        else:
            data = None
        data = comm.scatter(data, root=0)
        var = varlist[data]
        print(var)
        if var is not None: 
            try:
                lib.proc.ts_masks(var[0], var[1], var[2], masks[var[3]])
            except:
                pass

main()
