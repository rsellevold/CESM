import yaml
with open("config.yml","r") as f:
    config = yaml.safe_load(f)

scripts = ["process/atm/hist",
           "process/atm/calcadd",
           "process/atm/avg_mon2seas",
           "process/atm/avg_mon2ann",
           "process/atm/trends",
	   "process/atm/timeseries"]

nproc = config["machine"]["nproc"]

procfile = open("main_proc","w")

# Add machine directives
procfile.write("#!/bin/bash\n\n")
for i in range(len(config["machine"]["directive"])-1):
	procfile.write(f"{config['machine']['directive'][0]} {config['machine']['directive'][i+1]}\n")
procfile.write("\n")

procfile.write(f"source {config['machine']['condaact']} {config['machine']['condaenv']}\n\n")

for i in range(len(scripts)):
    if config["machine"]["mpi"]:
        if scripts[i] == "process/atm/calcadd":
            procfile.write(f"mpiexec -n 1 python {config['src']['codepath']}/{scripts[i]}.py\n")
        else:
            procfile.write(f"mpiexec -n {config['machine']['nproc']} python {config['src']['codepath']}/{scripts[i]}.py\n")

    else:
        procfile.write(f"python {config['src']['codepath']}/{scripts[i]}.py\n")
