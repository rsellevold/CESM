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

    f = misc.sellatlon(f, lats=(15,75))
    f = ncl.lonFlip(f, ["U925","U850","U775","U700"])

