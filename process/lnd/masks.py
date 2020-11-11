import yaml
with open("config.yml","r") as f:
    config = yaml.safe_load(f)
import os,sys
sys.path.append(f"{config['machine']['codepath']}")

from mpi4py import MPI
import xarray as xr
import lib


def masks(fdir, var):
    if var=="GrIS":
        #try:
        ds = xr.open_mfdataset([f"{fdir[:-12]}/input.nc", f"{fdir}/ICE_MODEL_FRACTION.nc", f"{fdir}/PCT_LANDUNIT.nc"], combine="nested")
        GrIS = ds.ICE_MODEL_FRACTION.values * ds.PCT_LANDUNIT.values[:,3,:,:]/100.0 * ds.area.values * ds.landfrac.values
        GrIS = xr.DataArray(GrIS, name="GrIS", dims=("time","lat","lon"), coords=[ds.time, ds.lat, ds.lon])
        GrIS = GrIS.fillna(0.)
        GrIS = GrIS.to_dataset()
        GrIS.encoding["unlimited_dims"] = "time"
        checkfile = f"{fdir[:-12]}/masks.nc"
            #if os.path.exists(checkfile):
            #    GrIS.to_netcdf(checkfile, mode="a")
            #else:
        GrIS.to_netcdf(checkfile)
        GrIS.close()
        ds.close()
        #except:
        #    None

    if var=="GrIS_pct":
        try:
            ds = xr.open_mfdataset([f"{fdir[:-12]}/input.nc", f"{fdir}/ICE_MODEL_FRACTION.nc", f"{fdir}/PCT_LANDUNIT.nc"], combine="nested")
            GrIS = ds.ICE_MODEL_FRACTION.values * ds.PCT_LANDUNIT.values[:,3,:,:]/100.0 * ds.landfrac.values
            GrIS = xr.DataArray(GrIS, name="GrIS_pct", dims=("time","lat","lon"), coords=[ds.time, ds.lat, ds.lon])
            GrIS = GrIS.fillna(0.)
            GrIS = GrIS.to_dataset()
            GrIS.encoding["unlimited_dims"] = "time"
            checkfile = f"{fdir[:-12]}/masks.nc"
            if os.path.exists(checkfile):
                GrIS.to_netcdf(checkfile, mode="a")
            else:
                GrIS.to_netcdf(checkfile)
            GrIS.close()
            ds.close()
        except:
            None


def main():
    # Initialize MPI
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    fdir = f"{config['run']['folder']}/{config['run']['name']}/lnd/hist/monavg"
    varlist = ["GrIS", "GrIS_pct"]
    varlist = lib.mpimods.check_varlist(varlist, size)

    for i in range(int(len(varlist)/size)):
        if rank==0:
            data = [(i*size)+k for k in range(size)]
        else:
            data = None
        data = comm.scatter(data, root=0)
        var = varlist[data]
        print(var)
        if var is not None: masks(fdir, var)

main()
