import sys,os,glob,math

import xarray as xr
import cftime
from cdo import Cdo
import Ngl
import numpy as np
from netCDF4 import Dataset

cdo = Cdo()


def _checkdir(folder):
    check = os.path.exists(folder)
    if not(check):
        os.system(f"mkdir -p {folder}")


def _getfnames(config, comp, var, hfile):
    if config["history"]["ts"]:
        fnames_all = []
        for key,item in config["runs"].items():
            fnames = glob.glob(f"{config['runs'][key]['folder']}/{key}/{comp}/proc/tseries/{config['history'][comp][hfile]['tstype']}/*.{hfile}.{var}.*.nc")
            fnames_all.append(fnames)
        fnames_all = [item for sublist in fnames_all for item in sublist]
    if not(config["history"]["ts"]):
        fnames_all = []
        for key,item in config["runs"].items():
            fnames = glob.glob(f"{config['runs'][key]['folder']}/{key}/{comp}/hist/*.{hfile}.*.nc")
            fnames_all.append(fnames)
        fnames_all = [item for sublist in fnames_all for item in sublist]
  return fnames_all


def _removeSameTime(fnames_all, bndname, starttime):
    for fname in fnames_all:
        f = Dataset(fname, "r")
        if comp!="glc":
            timestamp = np.array((f.variables[bndname][-1,0]+f.variables[bndname][-1,1])/2)
        else:
            timestamp = np.array(f.variables["time"][-1]) - 1
        if starttime <= timestamp:
            fnames_all.remove(fname)
    return fnames_all



def monavg(fdir, var):
    # Computes monthly means
    outdir = f"{fdir[:-7]}/monavg"
    _checkdir(outdir)
    cdo.monmean(input=f"{fdir}/{var}", output=f"{outdir}/{var}")


def annavg(fdir, var):
    # Computes the annual means
    outdir = f"{fdir[:-7]}/annavg"
    _checkdir(outdir)
    cdo.yearmean(input=f"{fdir}/{var}", output=f"{outdir}/{var}")


def seasavg(fdir, var):
    tmpdir = f"{fdir[:-7]}/temp"
    _checkdir(tmpdir)
    infile = f"{fdir}/{var}"
    tmpfile = f"{tmpdir}/{var}.seasavg.nc"
    cdo.seasmean(input=infile, output=tmpfile)
    cdo.splitseas(input=tmpfile, output=f"{tmpdir}/{var}.seasavg.")
    for seas in ["DJF","MAM","JJA","SON"]:
        outdir = f"{fdir[:-7]}/{seas}avg"
        _checkdir(outdir)
        os.system(f"mv {tmpdir}/{var}.seasavg.{seas}.nc {outdir}/{var}")
    os.system(f"rm {tmpdir}/{var}.seasavg.*")


def mergehist(config, comp, var, hfile, htype):
    outfolder = f"{config['run']['folder']}/{config['run']['name']}/{comp}/hist/{htype}"
    _checkdir(outfolder)

    fnames_all = _getfnames(config, comp, var, hfile)

    os.system(f"mkdir -p {outfolder[:-12]}/temp")

    fnames_all.sort()
    if comp=="ocn" and not(config["history"]["ts"]):
        fnames_all = fnames_all[:-1]

    # Open earlier file (if it exists), to remove files with same timestamp
    try:
        data_already = xr.open_dataset(f"{outfolder}/{var}.nc", decode_times=False)
        starttime = data_already.time.min().values
        prevDataExists = True
    except FileNotFoundError:
        None

    bndname = config["compset"][comp]["bnds"]
    fnames_all = _removeSameTime(fnames_all, bndname, endtime)

    nfiles = math.floor(len(fnames_all)/100)

    for i in range(nfiles+1):
        fstring = " ".join(fnames_all[i*100:(i+1)*100])
        if comp=="atm":
            varsget = f"{var},hyam,hybm"
        else:
            varsget = f"{var}"
        if i==0:
            os.system(f"ncrcat -v {varsget} {fstring} {outfolder[:-12]}/temp/{var}.nc")
        else:
            os.system(f"ncrcat -O -v {var} {fstring} {outfolder[:-12]}/temp/{var}.nc {outfolder[:-12]}/temp/{var}.nc")

    if comp=="glc":
        f = xr.open_dataset(f"{outfolder[:-12]}/temp/{var}.nc", decode_times=False)
        timeunit = f.time.units.replace("common_year","years")
    else:
        f = xr.open_dataset(f"{outfolder[:-12]}/temp/{var}.nc")
        timeunit = Dataset(f"{outfolder[:-12]}/temp/{var}.nc","r").variables["time"].units
    f = f.sortby("time")

    if comp!="glc":
        try:
            bnds = cftime.date2num(f[config["compset"][comp]["bnds"]].values, timeunit, calendar="noleap")
        except:
            sys.exit("Provided time bounds does not exsist, update config.yml: compset/[component]/bnds")

        bnds = (bnds[:,0]+bnds[:,1])/2
        bnds = cftime.num2date(bnds, timeunit, calendar="noleap")
        bnds = xr.DataArray(bnds, name="time", dims=("time"))
        bnds.attrs["long_name"] = f.time.long_name
        f["time"] = bnds
    else:
        f["time"] = cftime.num2date(f.time.values-1, timeunit, calendar="noleap")

    if comp=="ocn" and var=="MOC":
        data = f[var][:,1,0,:,:]
    else:
        data = f[var]

    if comp=="atm" and data.ndim==4:
        nt = len(data.time.values)
        plev = config["compset"]["atm"]["plev"]
        data_new = np.empty(shape=(nt, len(plev), data.shape[-2], data.shape[-1]))
        try:
            PS = f.PS
        except AttributeError:
            fPS = xr.open_dataset(f"{outfolder}/PS.nc")
            tmin = data.time.min()
            tmax = data.time.max()
            PS = fPS.PS.sel(time=slice(tmin,tmax))
        for t in range(nt):
            print(t)
            data_new[t,:,:,:] = Ngl.vinth2p(data.values[t,:,:,:], f.hyam.values, f.hybm.values, plev, PS.values[t,:,:], 1, 1000., 1, True)
        data = xr.DataArray(data_new, name=var, dims=("time","lev","lat","lon"), coords=[data.time, plev, data.lat, data.lon])

    data = data.to_dataset()

    if prevDataExists:
        data = xr.concat([data_already, data], dim="time")
        data = data.sortby("time")
        data_already.close()

    data.encoding["unlimited_dims"] = "time"
    data.to_netcdf(f"{outfolder}/{var}.nc")

    data.close()
    f.close()
    os.system(f"rm {outfolder[:-12]}/temp/{var}.nc")
