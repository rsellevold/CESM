import sys
import xarray as xr
from scipy.stats import linregress
import numpy as np
from cdo import Cdo

from .preproc import _checkdir

cdo = Cdo()


def trend_calc(data, tt):
  if data.ndim == 3:
    ny = data.shape[1]
    nx = data.shape[2]
    tren = np.empty(shape=(ny,nx))
    r = np.empty(shape=(ny,nx))
    p = np.empty(shape=(ny,nx))
    for y in range(ny):
      for x in range(nx):
        tren[y,x], _, r[y,x], p[y,x], _ = linregress(np.arange(0,tt,1), data[:,y,x])

  elif data.ndim == 4:
    nk = data.shape[1]
    ny = data.shape[2]
    nx = data.shape[3]
    tren = np.empty(shape=(nk,ny,nx))
    r = np.empty(shape=(nk,ny,nx))
    p = np.empty(shape=(nk,ny,nx))
    for k in range(nk):
      for y in range(ny):
        for x in range(nx):
          tren[k,y,x], _, r[k,y,x], p[k,y,x], _ = linregress(np.arange(0,tt,1),data[:,k,y,x])

  return (tren, r, p)


def trend(fdir, var, seas, nyears):
  outdir = f"{fdir[:-12]}/trend/{seas}"
  _checkdir(outdir)

  f = xr.open_dataset(f"{fdir}/{var}")
  keys = list(f.keys())
  if "time_bnds" in keys: keys.remove("time_bnds")
  key = keys[0]
  tt = len(f.time.values)

  if type(nyears)==str and nyears=="all":
    tren, r, p = trend_calc(f[key].values, tt)
  elif type(nyears)==int:
    tren, r, p = trend_calc(f[key].values[-nyears:,...], nyears)
  elif type(nyears)==tuple:
    syr = str(nyears[0]).zfill(4)
    eyr = str(nyears[1]).zfill(4)
    tren, r, p = trend_calc(f[key].sel(time=slice(syr,eyr)).values, nyears[1]-nyears[0]+1)

  if tren.ndim==2:
    tren = xr.DataArray(tren, name="trend", dims=("lat","lon"), coords=[f.lat,f.lon])
    r = xr.DataArray(r, name="r", dims=("lat","lon"), coords=[f.lat,f.lon])
    p = xr.DataArray(p, name="p", dims=("lat","lon"), coords=[f.lat,f.lon])
  elif tren.ndim==3:
    dims = list(f.dims)
    if "lat" in dims: dims.remove("lat")
    if "lon" in dims: dims.remove("lon")
    if "time" in dims: dims.remove("time")
    if "bnds" in dims: dims.remove("bnds")
    dims = dims[0]
    tren = xr.DataArray(tren, name="trend", dims=(dims,"lat","lon"), coords=[f[dims],f.lat,f.lon])
    r = xr.DataArray(r, name="r", dims=(dims,"lat","lon"), coords=[f[dims],f.lat,f.lon])
    p = xr.DataArray(p, name="p", dims=(dims,"lat","lon"), coords=[f[dims],f.lat,f.lon])

  fout = xr.Dataset({"trend": tren, "r":r, "p":p})
  fout.attrs["nyears"] = nyears
  fout.to_netcdf(f"{outdir}/{var}")
  fout.close()
  f.close()


def areastat(data, weights, arith):
  equal = False
  skip = False
  if data.ndim==3 and weights.ndim==2:
    weights[np.isnan(data[1,:,:])] = np.nan
    weights = weights[np.newaxis,...]
  elif data.ndim==4 and weights.ndim==2:
    weights[np.isnan(data[0, 0, :, :])] = np.nan
    weights = weights[np.newaxis,np.newaxis,...]
  elif data.ndim==weights.ndim:
    equal = True
    weights[np.isnan(data)] = np.nan
  else:
    print(f"Statistics not supported for data with {data.ndim} dimensions")

  if arith=="mean" and not(equal):
    data = np.nansum(data * weights, axis=(-2,-1)) / np.nansum(weights)
  elif arith=="mean" and equal:
    data = np.nansum(data * weights, axis=(-2,-1)) / np.nansum(weights, axis=(-2,-1))
  elif arith=="sum":
    data = np.nansum(data * weights, axis=(-2,-1))

  return data


def ts(fdir, var, seas, region):
  outdir = f"{fdir[:-12]}/timeseries/{region}/{seas}"
  _checkdir(outdir)

  f = xr.open_dataset(f"{fdir}/{var}")
  keys = list(f.keys())
  if "time_bnds" in keys: keys.remove("time_bnds")
  key = keys[0]
  farea = cdo.gridarea(input=f, returnXDataset=True)

  if key=="ICEFRAC":
    arith="sum"
  else:
    arith="mean"

  if region=="global":
    data = areastat(f[key].values, farea.cell_area.values, arith=arith)
  elif region=="NH":
    data = areastat(f[key].sel(lat=slice(0,90)).values, farea.sel(lat=slice(0,90)).cell_area.values, arith=arith)
  elif region=="SH":
    data = areastat(f[key].sel(lat=slice(-90,0)).values, farea.sel(lat=slice(-90,0)).cell_area.values, arith=arith)
  elif region=="tropical":
    data = areastat(f[key].sel(lat=slice(-30,30)).values, farea.sel(lat=slice(-30,30)).cell_area.values, arith=arith)
  elif region=="arctic":
    data = areastat(f[key].sel(lat=slice(60,90)).values, farea.sel(lat=slice(60,90)).cell_area.values, arith=arith)
  else:
    sys.exit("Undefined region")

  if data.ndim==1:
    data = xr.DataArray(data, name=key, dims=("time"), coords=[f.time])
  elif data.ndim==2:
    dims = list(f.dims)
    if "lat" in dims: dims.remove("lat")
    if "lon" in dims: dims.remove("lon")
    if "time" in dims: dims.remove("time")
    if "bnds" in dims: dims.remove("bnds")
    dims = dims[0]
    data = xr.DataArray(data, name=key, dims=("time",dims), coords=[f.time,f[dims]])

  data = data.to_dataset()
  data.encoding["unlimited_dims"] = "time"
  data.to_netcdf(f"{outdir}/{var}")

  data.close()
  farea.close()
  f.close()


def ts_masks(fdir, var, seas, mask):
  outdir = f"{fdir[:-12]}/timeseries_masks/{mask.name}/{seas}"
  _checkdir(outdir)

  f = xr.open_dataset(f"{fdir}/{var}")
  keys = list(f.keys())
  if "time_bnds" in keys: keys.remove("time_bnds")
  key = keys[0]

  if var!="PCT_LANDUNIT.nc":
    data = areastat(f[key].values, mask.values, "mean")

    if data.ndim==1:
      data = xr.DataArray(data, name=key, dims=("time"), coords=[f.time])
    elif data.ndim==2:
      dims = list(f.dims)
      if "lat" in dims: dims.remove("lat")
      if "lon" in dims: dims.remove("lon")
      if "time" in dims: dims.remove("time")
      if "bnds" in dims: dims.remove("bnds")
      dims = dims[0]
      data = xr.DataArray(data, name=key, dims=("time",dims), coords=[f.time,f[dims]])

    data = data.to_dataset()
    data.encoding["unlimited_dims"] = "time"
    data.to_netcdf(f"{outdir}/{var}")

    data.close()
  f.close()
