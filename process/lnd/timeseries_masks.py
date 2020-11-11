import yaml
with open("config.yml","r") as f:
    config = yaml.safe_load(f)
import os,sys
sys.path.append(f"{config['machine']['codepath']}")

from mpi4py import MPI
import xarray as xr
import lib


def main():
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Get config
    with open("config.yml","r") as f:
        config = yaml.safe_load(f)

    masks = xr.open_dataset(f"{config['run']['folder']}/{config['run']['name']}/lnd/masks_annavg.nc")
    keylist = list(masks.keys())
    if "time_bnds" in keylist: keylist.remove("time_bnds")
    print(keylist)
    for k in keylist:
        print(k)
        for seas in ["annavg"]:
            if rank==0:
                print(seas)
            fdir = f"{config['run']['folder']}/{config['run']['name']}/lnd/hist/{seas}"
            varlist = os.popen(f"ls {fdir}").read().split("\n")[:-1]
            varlist = lib.mpimods.check_varlist(varlist,size)

            for i in range(int(len(varlist)/size)):
                if rank==0:
                    data = [(i*size)+k for k in range(size)]
                else:
                    data = None
                data = comm.scatter(data, root=0)
                var = varlist[data]
                print(var)
                if var is not None or var!="TLAKE.nc": lib.proc.ts_masks(fdir, var, seas, masks[k])

main()
