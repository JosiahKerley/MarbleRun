import os
import time
from marblerun import Marble

marble = Marble()
marble.verbose = True
marble.monitored = False

print("Starting...")


##- unmonitored job


## Enqueue data
for i in range(1,5):
	marble.send("test-unmonitored","Test Data: %s"%(str(i)))

## Process data
while True:
	data = marble.wait("test-unmonitored")
	print data