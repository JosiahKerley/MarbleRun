import os
import time
import socket
import random
from marblerun import Monitor
from marblerun import Communicator



## Adds info to queue
queue = "queue_%s"%(socket.gethostname())
os.system("clear")
mon = Monitor()
comm = Communicator()
print("Creating items in queue...")
for i in range(0,15):
	#item = random.randint(0,100)
	item = random.randint(0,100000000000)
	print("Adding '%s'..."%(str(item)))
	comm.push(queue,item)
time.sleep(1)
