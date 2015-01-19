import os
import time
from marblerun import Marble

marble = Marble()
#marble.verbose = True
marble.monitored = False

marble.connect(bustype=None,server=None,port=None,password=None,channel=1)

print("Starting...")


##- unmonitored job


## Process data
while True:
	data = marble.wait("test-monitored")
	print data