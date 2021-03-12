import os,sys

import .misc, .ncl

def northatlantic_jet(config):

    # Check if data is present
    fdir = f"{config['run']['folder']}/{config['run']['name']}/atm/hist/dayavg"
    fnames = [f"{fdir}/U925.nc",f"{fdir}/U850.nc",f"{fdir}/U775.nc",f"{fdir}/U700.nc"]
    for fname in fnames:
        if not(os.path.exists(fname))
            sys.exit("File does not exist: {fname} - error in calculation of northatlantic jet")

    # Load data
    f = xr.open_mfdataset(fnames)

    f = ncl.lonFlip(f, ["U925","U850","U775","U700"])
    f = misc.sellatlon(f, lats=(15,75), lons=(-60,0))

    data = (f["U925"].values + f["U850"].values + f["U775"].values + f["U700"].values) / 4.0
    data = np.nanmean(data, axis=-1)

    ny = int(data.shape[1])
    for y in range(ny):
        data[:,y] = ncl.lanczos_filter(data[:,y], 61, 0, 1./10., -999, 1, 1, 1e+36)

    speed = np.nanmax(data, axis=1)
    lats = f.lat.values[np.argmax(data, axis=1)]

    speed = xr.DataArray(speed, name="speed", dims=("time"), coords=[f.time])
    lats = xr.DataArray(lats, name="latitude", dims=("time"), coords=[f.time])

    fout = xr.merge([speed,lats])
    fout.encoding["unlimited_dims"] = "time"

    outdir = f"{config['run']['folder']}/{config['run']['name']}/atm/climateind/dayavg"

    fout.to_netcdf(f"{outdir}/na_jet.nc")
