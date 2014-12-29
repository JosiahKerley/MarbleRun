import os
import time
import socket
import random
from marblerun import Monitor
from marblerun import Communicator



queue = "queue_%s"%(socket.gethostname())



## Adds info to queue
os.system("clear")
mon = Monitor()
comm = Communicator()
print("Creating items in queue...")
for i in range(0,15):
	item = random.randint(0,100)
	print("Adding '%s'..."%(str(item)))
	comm.push(queue,item)
time.sleep(1)

## Processes the queue
while True:
	mon = Monitor()
	comm = Communicator()
	os.system("clear")
	print("Starting...")
	#comm.push(queue,random.randint(0,100))
	data = mon.checkout(queue)
	if data == None:
		mon.finish()
	else:
		print data
		for i in range(0,15):
			#print("Bump-bump...")
			mon.heartbeat()
			#time.sleep(1)
			#time.sleep(0.1)
		error = random.randint(0,2)
		if not error == 0:
			mon.finish()
		else:
			print("Faking error...")
		for i in comm.dump("foo",True):
			#print i
			pass
	print("...done")
	time.sleep(0.5)