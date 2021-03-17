import numpy as np
import xarray as xr

from .nclf import *

####################
# contributed.ncl
####################

def lonFlip(f, keys):
    mlon = int(f.lon.values.shape[0])
    if mlon%2 != 0:
        sys.exit(f"lib.ncl.lonFlip: Number of longitudes not even number ({mlon})")
    mlon2 = int(mlon/2)

    lon = np.copy(f.lon.values)
    lon[0:mlon2] = f.lon.values[mlon2:]
    lon[mlon2:] = f.lon.values[0:mlon2]
    lon[lon>=180] -= 360
    lon = xr.DataArray(lon, name="lon", dims=("lon"), attrs=f.lon.attrs)

    data = []
    for key in keys:
        var = np.copy(f[key].values)
        var[...,0:mlon2] = np.copy(f[key].values[...,mlon2:])
        var[...,mlon2:] = np.copy(f[key].values[...,0:mlon2])
        if var.ndim==3:
            data.append(xr.DataArray(var, name=key, dims=("time","lat","lon"), coords=[f.time,f.lat,lon], attrs=f[key].attrs))
        elif var.ndim==4:
            data.append(xr.DataArray(var, name=key, dims=("time","lev","lat","lon"), coords=[f.time,f.lev,f.lat,lon], attrs=f[key].attrs))
        else:
            sys.exit("Cannot understand dimensions")

    fnew = xr.merge(data)
    return fnew


#####################
# NCL fortran routines
####################

# Lanczos filtering
def lanczos_filter(data, nwt, ihp, fca, fcb, nsigma, kopt, fillval):
    data_new = np.copy(data)

    fillval = float(fillval)
    data_new[np.isnan(data_new)] = fillval

    wgt, resp, freq = dfiltrq(nwt, ihp, fca, fcb, nsigma)

    lwork = int(len(data_new) + 2*(len(wgt)/2))

    ier = dwgtrunave(data_new, wgt, kopt, fillval, lwork)
    if ier != 0:
        sys.exit("ncl:lanczos filter: error")
    data_new[data_new==fillval] = np.nan

    return data_new
