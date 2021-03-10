import os

def check_varlist(varlist,nproc):
    nv = int(len(varlist)/nproc)
    create_new = False
    if not(nv==len(varlist)/nproc):
        nv += 1
        create_new = True
    if create_new:
        rest = nv*nproc - len(varlist)
        for j in range(rest):
            varlist.append(None)
    return varlist


def make_varlist(config,comps):
    varlist = []
    for comp in comps:
        for hfile in config["history"][comp].keys():
            for key in config["history"][comp][hfile]["varlist"]:
                varlist.append([comp,hfile,key,config["history"][comp][hfile]["htype"]])

    return varlist

def make_varlist2(fdir):
    varlist = []
    for i in fdir:
        vlist = os.popen(f"ls {i}").read().split("\n")[:-1]
        for v in vlist:
            varlist.append([i,v])
    return varlist
