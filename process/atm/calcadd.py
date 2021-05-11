import yaml
with open("config.yml","r") as f:
    config = yaml.safe_load(f)
import os,sys
sys.path.append(f"{config['machine']['codepath']}")

import xarray as xr
import lib


def calcadd(fdir, var):
    if var=="ALBEDO":
        try:
            FSNS = xr.open_dataset(f"{fdir}/FSNS.nc")
            FSDS = xr.open_dataset(f"{fdir}/FSDS.nc")
            ALBEDO = 1 - (FSNS["FSNS"]/FSDS["FSDS"])
            ALBEDO.name = "ALBEDO"
            ALBEDO.to_dataset()
            ALBEDO.encoding["unlimited_dims"] = "time"
            ALBEDO.to_netcdf(f"{fdir}/ALBEDO.nc")
            ALBEDO.close()
        except:
            None

    elif var=="PRECT":
        try:
            PRECC = xr.open_dataset(f"{fdir}/PRECC.nc")
            PRECL = xr.open_dataset(f"{fdir}/PRECL.nc")
            PRECT = PRECC["PRECC"] + PRECL["PRECL"]
            PRECT.name = "PRECT"
            PRECT.to_dataset()
            PRECT.encoding["unlimited_dims"] = "time"
            PRECT.to_netcdf(f"{fdir}/PRECT.nc")
            PRECT.close()
        except:
            None

    elif var=="SNOW":
        try:
            PRECSC = xr.open_dataset(f"{fdir}/PRECSC.nc")
            PRECSL = xr.open_dataset(f"{fdir}/PRECSL.nc")
            SNOW = PRECSC["PRECSC"] + PRECSL["PRECSL"]
            SNOW.name = "SNOW"
            SNOW.to_dataset()
            SNOW.encoding["unlimited_dims"] = "time"
            SNOW.to_netcdf(f"{fdir}/SNOW.nc")
            SNOW.close()
        except:
            None

    elif var=="RAIN":
        try:
            PRECT = xr.open_dataset(f"{fdir}/PRECT.nc")
            SNOW = xr.open_dataset(f"{fdir}/SNOW.nc")
            RAIN = PRECT["PRECT"] - SNOW["SNOW"]
            RAIN.name = "RAIN"
            RAIN.to_dataset()
            RAIN.encoding["unlimited_dims"] = "time"
            RAIN.to_netcdf(f"{fdir}/RAIN.nc")
            RAIN.close()
        except:
            None

    elif var=="RADTOA":
        try:
            FSNT = xr.open_dataset(f"{fdir}/FSNT.nc")
            FLNT = xr.open_dataset(f"{fdir}/FLNT.nc")
            RADTOA = FSNT["FSNT"] - FLNT["FLNT"]
            RADTOA.name = "RADTOA"
            RADTOA.to_dataset()
            RADTOA.encoding["unlimited_dims"] = "time"
            RADTOA.to_netcdf(f"{fdir}/RADTOA.nc")
            RADTOA.close()
        except:
            None

    elif var=="FSCF":
        try:
            FSDS = xr.open_dataset(f"{fdir}/FSDS.nc")
            FSDSC = xr.open_dataset(f"{fdir}/FSDSC.nc")
            FSCF = FSDS["FSDS"] - FSDSC["FSDSC"]
            FSCF.name = "FSCF"
            FSCF.to_dataset()
            FSCF.encoding["unlimited_dims"] = "time"
            FSCF.to_netcdf(f"{fdir}/FSCF.nc")
            FSCF.close()
        except:
            None

    elif var=="FLCF":
        try:
            FLDS = xr.open_dataset(f"{fdir}/FLDS.nc")
            FLDSC = xr.open_dataset(f"{fdir}/FLDSC.nc")
            FLCF = FLDS["FSDS"] - FLDSC["FLDSC"]
            FLCF.name = "FLCF"
            FLCF.to_dataset()
            FLCF.encoding["unlimited_dims"] = "time"
            FLCF.to_netcdf(f"{fdir}/FLCF.nc")
            FLCF.close()
        except:
            None

    elif var=="FSDTOA":
        try:
            FSNTOA = xr.open_dataset(f"{fdir}/FSNTOA.nc")
            FSUTOA = xr.open_dataset(f"{fdir}/FSUTOA.nc")
            FSDTOA = FSNTOA["FSNTOA"] + FSUTOA["FSUTOA"]
            FSDTOA.name = "FSDTOA"
            FSDTOA.to_dataset()
            FSDTOA.encoding["unlimited_dims"] = "time"
            FSDTOA.to_netcdf(f"{fdir}/FSDTOA.nc")
            FSDTOA.close()
        except:
            None

    elif var=="SWtra":
        try:
            FSDS = xr.open_dataset(f"{fdir}/FSDS.nc")
            FSDSC = xr.open_dataset(f"{fdir}/FSDSC.nc")
            SWtra = FSDS["FSDS"] / FSDSC["FSDSC"]
            SWtra.name = "SWtra"
            SWtra.to_dataset()
            SWtra.encoding["unlimited_dims"] = "time"
            SWtra.to_netcdf(f"{fdir}/SWtra.nc")
            SWtra.close()
        except:
            None

    elif var=="LWtra":
        try:
            FLDS = xr.open_dataset(f"{fdir}/FLDS.nc")
            FLDSC = xr.open_dataset(f"{fdir}/FLDSC.nc")
            LWtra = FLDSC["FLDSC"] / FLDS["FLDS"]
            LWtra.name = "LWtra"
            LWtra.to_dataset()
            LWtra.encoding["unlimited_dims"] = "time"
            LWtra.to_netcdf(f"{fdir}/LWtra.nc")
            LWtra.close()
        except:
            None

    elif var=="SST2":
        try:
            TS = xr.open_dataset(f"{fdir}/TS.nc")
            OCNFRAC = xr.open_dataset(f"{fdir}/OCNFRAC.nc")
            SST2 = TS["TS"] * OCNFRAC["OCNFRAC"].where(OCNFRAC["OCNFRAC"]>0.5)
            SST2.name = "SST2"
            SST2.to_dataset()
            SST2.encoding["unlimited_dims"] = "time"
            SST2.to_netcdf(f"{fdir}/SST2.nc")
            SST2.close()
        except:
            None



def main():
    time = sys.argv[1]

    fdir = f"{config['run']['folder']}/{config['run']['name']}/atm/hist/{time}"
    varlist = ["ALBEDO", "PRECT", "SNOW", "RAIN", "RADTOA", "FSCF", "FLCF", "FSDTOA", "SWtra", "LWtra", "SST2"]

    for i in range(len(varlist)):
        var = varlist[i]
        print(var)
        if var is not None: calcadd(fdir, var)

main()
