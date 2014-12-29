import os
import time
import base64
import socket
import random
import hashlib
from marblerun import Monitor
from marblerun import Communicator



## Processes the queue
queue = "queue_%s"%(socket.gethostname())
while True:
	mon = Monitor()
	comm = Communicator()
	mon.verbose = True
	os.system("clear")
	print("Starting...")
	#comm.push(queue,random.randint(0,100))
	data = mon.checkout(queue)
	if data:
		tmp = 0
		for i in range(0,15):
			mon.heartbeat()
			print(str(base64.b64encode(hashlib.sha256(str(int(data)+i)).digest()))) ## Doing some "work"
			time.sleep(0.3)
		error = random.randint(0,2)
		if not error == 0:
			mon.finish()
		else:
			print("\t[W] Faking error...")
	print("...done")
	time.sleep(0.5)