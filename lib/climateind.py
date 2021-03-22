import os,sys
import numpy as np
import xarray as xr
from cdo import Cdo
from eofs.standard import Eof

from .misc import *
from .ncl import *

def NAO(config, season):

    for seas in season:
        fname = f"{config['run']['folder']}/{config['run']['name']}/atm/hist/{seas}/PSL.nc"

        f = xr.open_dataset(fname)

        f = lonFlip(f, ["PSL"])
        f = sellatlon(f, lats=(20,80), lons=(-90,40))

        coslat = np.cos(np.deg2rad(f.lat.values)).clip(0.,1.)
        wgts = np.sqrt(coslat)[...,np.newaxis]
        solver = Eof(f.PSL.values, weights=wgts)
        psl_filtered = np.copy(f.PSL.values).astype(np.float64)
        for y in range(psl_filtered.shape[1]):
            for x in range(psl_filtered.shape[2]):
                psl_filtered[:,y,x] = lanczos_filter(psl_filtered[:,y,x], 21, 1, 1./100., -999, 1, 1, 1e+36)
        solver_filt = Eof(psl_filtered, weights=wgts)

        eofs = solver.eofsAsCovariance(neofs=5)
        pcs = solver.pcs(npcs=5)
        vari = solver.varianceFraction(neigs=5)

        eofs_filt = solver_filt.eofsAsCovariance(neofs=5)
        pcs_filt = solver_filt.pcs(npcs=5)
        vari_filt = solver_filt.varianceFraction(neigs=5)

        eofs = xr.DataArray(eofs, name="eofs", dims=("neof","lat","lon"), coords=[np.arange(1,6,1), f.lat, f.lon])
        pcs = xr.DataArray(pcs, name="pcs", dims=("time","neof"), coords=[f.time,np.arange(1,6,1)], attrs={"variance": vari})
        
        eofs_filt = xr.DataArray(eofs_filt, name="eofs_filtered", dims=("neof","lat","lon"), coords=[np.arange(1,6,1), f.lat, f.lon])
        pcs_filt = xr.DataArray(pcs_filt, name="pcs_filtered", dims=("time","neof"), coords=[f.time,np.arange(1,6,1)], attrs={"variance": vari_filt})

        fout = xr.merge([eofs,pcs,eofs_filt,pcs_filt])
        fout.encoding["unlimited_dims"] = "time"

        outdir = f"{config['run']['folder']}/{config['run']['name']}/atm/climateind/{seas}"
        if not(os.path.exists(outdir)):
            os.system(f"mkdir -p {outdir}")

        fout.to_netcdf(f"{outdir}/NAO.nc")
        fout.close()
        f.close()

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
    fname1 = f"{config['run']['folder']}/{config['run']['name']}/ocn/hist/annavg/TEMP.nc"
    fname2 = f"{config['run']['folder']}/{config['run']['name']}/atm/hist/annavg/SST.nc"
    if os.path.exists(fname1):
        f = xr.open_dataset(fname)
        vname = "TEMP"
    elif os.path.exists(fname2):
        f = xr.open_dataset(fname)
        vname = "SST"
    else:
        sys.exit("Cannot find file to calculate AMO")
    
    f = lonFlip(f, [vname])

    SST = np.copy(f[vname].values)
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
        data = np.squeeze(f.sel(lev=[500])["Z3"].values)
    else:
        data = f["Z3"].values

    cdo = Cdo()
    area = cdo.gridarea(input=f, returnXDataset=True)
    gridarea = np.copy(area.cell_area.values)

    gridarea = np.broadcast_to(gridarea, data.shape).copy()
    gridarea[np.isnan(data)] = np.nan

    lat1, lat2 = findnearest((60,80), f.lat.values)
    lon1, lon2 = findnearest((280,340), f.lon.values)

    GBI1 = np.nansum(data[:,lat1:lat2,lon1:lon2]*gridarea[:,lat1:lat2,lon1:lon2], axis=(1,2))/np.nansum(gridarea[:,lat1:lat2,lon1:lon2], axis=(1,2))
    GBI2 = GBI1 - (np.nansum(data[:,lat1:lat2,:]*gridarea[:,lat1:lat2,:], axis=(1,2))/np.nansum(gridarea[:,lat1:lat2,:], axis=(1,2)))

    GBI1 = xr.DataArray(GBI1, name="GBI1", dims=("time"), coords=[f.time])
    GBI2 = xr.DataArray(GBI2, name="GBI2", dims=("time"), coords=[f.time])

    GBI = xr.merge([GBI1,GBI2])
    GBI.encoding["unlimited_dims"] = "time"

    outdir = f"{config['run']['folder']}/{config['run']['name']}/atm/climateind/JJAavg"
    if not(os.path.exists(outdir)):
        os.system(f"mkdir -p {outdir}")

    GBI.to_netcdf(f"{outdir}/GBI.nc")
    area.close()


def seaice_index(config):
    fname = f"{config['run']['folder']}/{config['run']['name']}/atm/hist/monavg/ICEFRAC.nc"
    f = xr.open_dataset(fname)

    data = f["ICEFRAC"].values
    data[data<0.15] = np.nan

    cdo = Cdo()
    area = cdo.gridarea(input=f, returnXDataset=True)
    gridarea = np.copy(area.cell_area.values)
    area.close()
    gridarea[np.isnan(data)] = np.nan

    lat1, lat2 = findnearest((-90,0), f.lat.values)
    antarctic = np.nansum(data[:,lat1:lat2,:]*gridarea[np.newaxis,lat1:lat2,:], axis=(1,2))/np.nansum(gridarea[lat1:lat2,:])

    lat1, lat2 = findnearest((0,90), f.lat.values)
    arctic = np.nansum(data[:,lat1:lat2,:]*gridarea[np.newaxis,lat1:lat2,:], axis=(1,2))/np.nansum(gridarea[lat1:lat2,:])

    antarctic = xr.DataArray(antarctic, name="antarctic", dims=("time"), coords=[f.time])
    arctic = xr.DataArray(arctic, name="arctic", dims=("time"), coords=[f.time])

    seaice_index = xr.merge([antarctic,arctic])
    seaice_index.encoding["unlimited_dims"] = "time"

    outdir = f"{config['run']['folder']}/{config['run']['name']}/atm/climateind/monavg"
    if not(os.path.exists(outdir)):
        os.system(f"mkdir -p {outdir}")

    seaice_index.to_netcdf(f"{outdir}/seaice_index.nc")
