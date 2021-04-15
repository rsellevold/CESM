import sys, os
from .sysfunc import _checkdir


def monavg(fdir, var):
    # Computes monthly means
    outdir = f"{fdir[:-7]}/monavg"
    _checkdir(outdir)
    os.system(f"cdo monavg {fdir}/{var} {outdir}/{var}")


def annavg(fdir, var):
    # Computes the annual means
    outdir = f"{fdir[:-7]}/annavg"
    _checkdir(outdir)
    os.system(f"cdo yearavg {fdir}/{var} {outdir}/{var}")


def seasavg(fdir, var):
    tmpdir = f"{fdir[:-7]}/temp"
    _checkdir(tmpdir)
    infile = f"{fdir}/{var}"
    tmpfile = f"{tmpdir}/{var}.seasavg.nc"
    os.system(f"cdo seasavg {infile} {tmpfile}")
    os.system(f"cdo splitseas {tmpfile} {tmpdir}/{var}.seasavg.")
    for seas in ["DJF","MAM","JJA","SON"]:
        outdir = f"{fdir[:-7]}/{seas}avg"
        _checkdir(outdir)
        os.system(f"mv {tmpdir}/{var}.seasavg.{seas}.nc {outdir}/{var}")
    os.system(f"rm {tmpdir}/{var}.seasavg.*")
