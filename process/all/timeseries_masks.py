import multiprocessing as mpi
import yaml
with open("config.yml","r") as f:
    config = yaml.safe_load(f)
import os,sys,math
sys.path.append(f"{config['machine']['codepath']}")

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



def launch(chunk,masks):
    for arg in chunk:
        print(arg)
        lib.proc.ts_masks(arg[0], arg[1], arg[2], masks[arg[3]])



def main():
    comp = sys.argv[1]
    comp = comp.split(",")
    times = sys.argv[2]
    times = times.split(",")
    fmask = sys.argv[3]

    masks = xr.open_dataset(fmask)
    maskList = masklist(masks)

    varlist = make_varlist(comp,times,maskList)

    niter = math.floor(len(varlist)/25) + 1
    for i in range(niter):
        chunk = varlist[i*25:i*25+25]
        p = mpi.Process(target=launch, args=(chunk,masks,))
        p.start()


if __name__ == "__main__":
    main()
