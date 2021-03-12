import os,sys

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
