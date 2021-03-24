modules = ["nclf"]
for m in modules:
    os.system("f2py -c lib/{m}.F90 -m {m}")
