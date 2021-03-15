import os,sys
import numpy as np
from cdo import Cdo

from .misc import *
from .ncl import *

def northatlantic_jet(config):

    # Check if data is present
    fname = f"{config['run']['folder']}/{config['run']['name']}/atm/hist/dayavg/U.nc"

    # Load data
    f = xr.open_dataset(fname)

    f = lonFlip(f, ["U"])
    f = sellatlon(f, lats=(15,75), lons=(-60,0))
    f = f.sel(lev=[925,850,775,700])

    data = np.nansum(f["U"].values, axis=1)
    data = np.nanmean(data, axis=-1)

    ny = int(data.shape[1])
    for y in range(ny):
        data[:,y] = lanczos_filter(data[:,y], 61, 0, 1./10., -999, 1, 1, 1e+36)

    speed = np.nanmax(data, axis=1)
    lats = f.lat.values[np.argmax(data, axis=1)]

    speed = xr.DataArray(speed, name="speed", dims=("time"), coords=[f.time])
    lats = xr.DataArray(lats, name="latitude", dims=("time"), coords=[f.time])

    fout = xr.merge([speed,lats])
    fout.encoding["unlimited_dims"] = "time"

    outdir = f"{config['run']['folder']}/{config['run']['name']}/atm/climateind/dayavg"
    if not(os.path.exists(outdir)):
        os.system(f"mkdir -p {outdir}")

    fout.to_netcdf(f"{outdir}/na_jet.nc")


def amo(config):
    fname = f"{config['run']['folder']}/{config['run']['name']}/atm/hist/annavg/SST.nc"
    f = xr.open_dataset(fname)
    f = lonFlip(f, ["SST"])

    SST = np.copy(f["SST"].values)
    SST[SST==0] = np.nan

    cdo = Cdo()
    area = cdo.gridarea(input=f, returnXDataset=True)
    gridarea = np.copy(area.cell_area.values)
    area.close()

    gridarea[np.isnan(SST[0,:,:])] = np.nan

    lat1, lat2 = findnearest((0,70), f.lat.values)
    lon1, lon2 = findnearest((-75,-5), f.lon.values)
    SST_NA = np.nansum(SST[:,lat1:lat2,lon1:lon2]*gridarea[np.newaxis,lat1:lat2,lon1:lon2], axis=(1,2))/np.nansum(gridarea[lat1:lat2,lon1:lon2])

    lat1, lat2 = findnearest((-60,60), f.lat.values)
    SST_global = np.nansum(SST[:,lat1:lat2,:]*gridarea[np.newaxis,lat1:lat2,:], axis=(1,2))/np.nansum(gridarea[lat1:lat2,:])

    AMO = SST_NA - SST_global
    AMO = lanczos_filter(AMO, 21, 0, 1./10., -999, 1, 1, 1e+36)
    
    AMO = xr.DataArray(AMO, name="AMO", dims=("time"), coords=[f.time])
    AMO = AMO.to_dataset()
    AMO.encoding["unlimited_dims"] = "time"

    outdir = f"{config['run']['folder']}/{config['run']['name']}/atm/climateind/annavg"
    if not(os.path.exists(outdir)):
        os.system(f"mkdir -p {outdir}")

    AMO.to_netcdf(f"{outdir}/AMO.nc")


def GBI(config):
    try:
        fname = f"{config['run']['folder']}/{config['run']['name']}/atm/hist/JJAavg/Z3.nc"
        f = xr.open_dataset(fname)
        multilevel=True
    except FileNotFoundError:
        fname = f"{config['run']['folder']}/{config['run']['name']}/atm/hist/JJAavg/Z500.nc"
        f = xr.open_dataset(fname)
        multilevel=False

    if multilevel:
        data = f.sel(lev=[500])["Z3"].values
    else:
        data = f["Z3"].values

    cdo = Cdo()
    area = cdo.gridarea(input=f, returnXDataset=True)
    gridarea = np.copy(area.cell_area.values)
    area.close()

    gridarea[np.isnan(data)] = np.nan

    lat1, lat2 = findnearest((60,80), f.lat.values)
    lon1, lon2 = findnearest((280,340), f.lon.values)

    GBI1 = np.nansum(data[:,lat1:lat2,lon1:lon2]*gridarea[np.newaxis,lat1:lat2,lon1:lon2], axis=(1,2))/np.nansum(gridarea[lat1:lat2,lon1:lon2])
    GBI2 = GBI1 - (np.nansum(data[:,lat1:lat2,:]*gridarea[np.newaxis,lat1:lat2,:], axis=(1,2))/np.nansum(gridarea[lat1:lat2,:]))

    GBI1 = xr.DataArray(GBI1, name="GBI1", dims=("time"), coords=[f.time])
    GBI2 = xr.DataArray(GBI2, name="GBI2", dims=("time"), coords=[f.time])

    GBI = xr.merge([GBI1,GBI2])
    GBI.encoding["unlimited_dims"] = "time"

    outdir = f"{config['run']['folder']}/{config['run']['name']}/atm/climateind/JJAavg"
    if not(os.path.exists(outdir)):
        os.system(f"mkdir -p {outdir}")

    GBI.to_netcdf(f"{outdir}/GBI.nc")
