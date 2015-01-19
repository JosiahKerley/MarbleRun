#!/usr/bin/python

import os
import json
import multiprocessing


## System data
cores = multiprocessing.cpu_count()


## Load MRStart config files
configfile = "/etc/marblerun/mrstart.json"
if os.path.isfile(configfile):
	with open(configfile,"r") as f:
		config = json.loads(f.read())
else:
	config = {"conf.d":"/etc/marblerun/conf.d","rewrite_config":True}
if config["rewrite_config"]:
	with open(configfile,"w") as f:
		f.write(json.dumps(config,indent = 2))


## Load startup definitions
jobs = os.listdir(config["conf.d"])
for job in jobs:
	job = json.loads(open("%s/%s"%(config["conf.d"],job)).read())
	instances = eval(job["instances"].replace('<[cores]>',str(cores)))
	cmd = "cd '%s' ; nohup python '%s' 2>&1 &"%(job["dir"],job["path"])
	for i in range(0,instances):
		os.system(cmd)
