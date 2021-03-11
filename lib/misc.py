import numpy as np


def findnearest(points, vector):
    idx = []
    for i in points:
        mini = np.argmin(np.abs(vector-i))
        idx.append(mini)
    idx = tuple(idx)
    return idx


def sellatlon(f,lats=None,lons=None):
    if lats is not None:
        lat1,lat2 = findnearest(lats,f.lat.values)
    if lons is not None:
        lon1,lon2 = findnearest(lons,f.lon.values)
    if lats and lons is not None:
        f = f.isel(lat=slice(lat1,lat2), lon=slice(lon1,lon2))
    elif lats is None:
        f = f.isel(lon=slice(lon1,lon2))
    elif lons is None:
        f = f.isel(lat=slice(lat1,lat2))
    return f
