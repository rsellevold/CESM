import numpy as np
import xarray as xr

####################
# contributed.ncl
####################

def lonFlip(f, keys):
    mlon = int(f.lon.values.shape[0])
    print(mlon%2)
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
        data.append(xr.DataArray(var, name=key, dims=("time","lat","lon"), coords=[f.time,f.lat,lon], attrs=f[key].attrs))

    fnew = xr.merge(data)
    return fnew
