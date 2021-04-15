import sys,os,glob
import cftime
import numpy as np
import xarray as xr

from .sysfunc import _checkdir
from .ncl import vinth2p_ecmwf


def _getfnames(config, comp, var, hfile):
    fnames_all = []
    for key, item in config["runs"].items():
        if config["history"]["ts"]:
            fnames = glob.glob(f"{config['runs'][key]['folder']}/{key}/{comp}/proc/tseries/{config['history'][comp][hfile]['tstype']}/*.{hfile}.{var}.*.nc")
        elif not(config["history"]["ts"]):
            fnames = glob.glob(f"{config['runs'][key]['folder']}/{key}/{comp}/hist/*.{hfile}.*.nc")
        fnames_all.append(fnames)
    fnames_all = [item for sublist in fnames_all for item in sublist]
    return fnames_all


def _removeSameTime(fnames_all, comp, bndname, time_already):
    for fname in fnames_all.copy():
        f = xr.open_dataset(fname, decode_times=False)
        if comp!="glc":
            timestamp = (f[bndname].values[0,0]+f[bndname].values[0,1])/2
            timestamp = cftime.num2date(timestamp, f.time.units, calendar=f.time.calendar)
        else:
            timestamp = f["time"].values[0] - 1
        if timestamp in time_already:
            fnames_all.remove(fname)
        f.close()
        del(f, timestamp)
    return fnames_all


def _removeOCNnday(fnames_all):
    for fname in fnames_all.copy():
        if "nday1" in fname:
            fnames_all.remove(fname)
        elif "once" in fname:
            fnames_all.remove(fname)
    return fnames_all


def mergehist(config, comp, var, hfile, htype):
    outfolder = f"{config['run']['folder']}/{config['run']['name']}/{comp}/hist/{htype}"
    _checkdir(outfolder)

    fnames_all = _getfnames(config, comp, var, hfile)

    os.system(f"mkdir -p {outfolder[:-12]}/temp")

    fnames_all.sort()
    if comp=="ocn" and not(config["history"]["ts"]) and hfile=="h":
        fnames_all = _removeOCNnday(fnames_all)

    if comp!="glc":
        bndname = config["compset"][comp]["bnds"]
    else:
        bndname = None

    prevDataExists = False
    if os.path.exists(f"{outfolder}/{var}.nc"):
        f_already = xr.open_dataset(f"{outfolder}/{var}.nc")
        fnames_all = _removeSameTime(fnames_all, comp, bndname, f.time.values)
        prevDataExists = True

    nfiles = math.floor(len(fnames_all)/100)
    if len(fnames_all)>0:
        for i in range(nfiles+1):
            fstring = " ".join(fnames_all[i*100:(i+1)*100])
            if comp=="atm":
              varsget = f"{var},hyam,hybm"
            else:
                varsget = f"{var}"
            if i==0:
                os.system(f"ncrcat -v {varsget} {fstring} {outfolder[:-12]}/temp/{var}.nc > nco_output.txt 2>&1")
            else:
                os.system(f"ncrcat -O -v {var} {fstring} {outfolder[:-12]}/temp/{var}.nc {outfolder[:-12]}/temp/{var}.nc > nco_output.txt 2>&1")
        del(varsget)
        
        if comp=="glc":
            f = xr.open_dataset(f"{outfolder[:-12]}/temp/{var}.nc", decode_times=False)
        else:
            f = xr.open_dataset(f"{outfolder[:-12]}/temp/{var}.nc")

        if comp!="glc":
            bnds = cftime.date2num(f[config["compset"][comp]["bnds"]].values, 
                                   f[config["compset"][comp]["bnds"]].encoding["units"], 
                                   calendar=f[config["compset"][comp]["bnds"]].encoding["calendar"])
            bnds = (bnds[:,0]+bnds[:,1])/2
            bnds = cftime.num2date(bnds, f.time.encoding["units"], calendar=f.time.encoding["calendar"])
            bnds = xr.DataArray(bnds, name="time", dims=("time"))
            bnds.attrs["long_name"] = f.time.long_name
            f["time"] = bnds.copy()
            del(bnds)
        else:
            f["time"] = f.time-1

        if comp=="ocn" and var=="MOC":
            data = f[var][:,1,0,:,:]
        elif comp=="ocn" and var!="MOC":
            data = f[var][:,config["compset"]["ocn"]["nlev"],:,:]
        else:
            data = f[var]
        data = data.sortby("time")


        if htype=="dayavg":
            keep_time = []
            for r in range(len(data["time"].values)):
                if data["time"].values[r].hour!=12:
                    keep_time.append(False)
                else:
                    keep_time.append(True)
            data = data.isel(time=keep_time)
            del(keep_time)

        _, index = np.unique(data["time"], return_index=True)
        data = data.isel(time=index)
        del(_, index)


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
            try:
                PHIS = f.PHIS
            except AttributeError:
                fPHIS = xr.open_dataset(f"{outfolder}/PHIS.nc")
                tmin = data.time.min()
                tmax = data.time.max()
                PHIS = fPHIS.PHIS.sel(time=slice(tmin,tmax))
            try:
                TBOT = f.TBOT
            except AttributeError:
                try:
                    fTBOT = xr.open_dataset(f"{outfolder}/TBOT.nc")
                    tmin = data.time.min()
                    tmax = data.time.max()
                    TBOT = fTBOT.TBOT.sel(time=slice(tmin,tmax))
                except FileNotFoundError:
                    fTBOT = xr.open_dataset(f"{outfolder}/TREFHT.nc")
                    tmin = data.time.min()
                    tmax = data.time.max()
                    TBOT = fTBOT.TREFHT.sel(time=slice(tmin,tmax))
            for t in range(nt):
                data_new[t,:,:,:] = vinth2p_ecmwf(data.values[t,:,:,:], f.hyam.values, f.hybm.values, 1000., plev, 1, PS.values[t,:,:], 1e+36, False, TBOT.values[t,:,:], PHIS.values[t,:,:])
            data_new[data_new==1e+36] = np.nan
            data = xr.DataArray(data_new, name=var, dims=("time","lev","lat","lon"), coords=[data.time, plev, data.lat, data.lon])

        data = data.to_dataset()

        if prevDataExists:
            data = xr.concat([f_already, data], dim="time")
            _, index = np.unique(data["time"], return_index=True)
            data = data.isel(time=index)
            del(_, index)
            data = data.sortby("time")

        data.encoding["unlimited_dims"] = "time"
        data.to_netcdf(f"{outfolder}/{var}.nc", encoding={"time": {"dtype":"float"}})

        data.close()
        f.close()
        f_already.close()
        del(data, f_already, f)
        os.system(f"rm {outfolder[:-12]}/temp/{var}.nc")
    elif len(fnames_all)==0 and prevDataExists:
        f_already.close()
        del(f_already)
