import os
import time
from marblerun import Monitor





mon = Monitor()
mon.verbose = True
while True:
	os.system("clear")
	print("Starting...")
	mon.monitorQueue()
	print("...done")
	time.sleep(1)
