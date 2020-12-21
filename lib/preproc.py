import sys,os,glob,math

import xarray as xr
import cftime
from cdo import Cdo
import Ngl
import numpy as np

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
  else:
    f = xr.open_dataset(f"{outfolder[:-12]}/temp/{var}.nc")
  f = f.sortby("time")

  if comp!="glc":
    try:
      bnds = cftime.date2num(f[config["compset"][comp]["bnds"]].values, "days since 0001-01-01 00:00:00", calendar="noleap")
    except:
      sys.exit("Provided time bounds does not exsist, update config.yml: compset/[component]/bnds")

    bnds = (bnds[:,0]+bnds[:,1])/2
    bnds = cftime.num2date(bnds, "days since 0001-01-01 00:00:00", calendar="noleap")
    bnds = xr.DataArray(bnds, name="time", dims=("time"))
    bnds.attrs["long_name"] = f.time.long_name
    f["time"] = bnds
  else:
    f["time"] = f.time - 1

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

  try: # Check if previous data exists
    if comp=="glc":
      data_already = xr.open_dataset(f"{outfolder}/{var}.nc", decode_times=False)
      starttime = data_already.time.min().values
      endtime = data_already.time.max().values
      endtime_new = data.time.min().values
    else:
      data_already = xr.open_dataset(f"{outfolder}/{var}.nc")
      starttime = data_already.time.dt.year.min().values
      endtime = data_already.time.dt.year.max().values
      endtime_new = data.time.dt.year.min().values
    if endtime > endtime_new:
      if comp=="glc":
        data_already = data_already.sel(time=slice(starttime,endtime_new-1))
      else:
        data_already = data_already.sel(time=slice(str(starttime).zfill(4),str(endtime_new-1).zfill(4)))
    data = xr.concat([data_already, data], dim="time")
    data = data.sortby("time")
    data_already.close()
  except FileNotFoundError:
    None

  data.encoding["unlimited_dims"] = "time"
  data.to_netcdf(f"{outfolder}/{var}.nc")

  data.close()
  f.close()
  os.system(f"rm {outfolder[:-12]}/temp/{var}.nc")
