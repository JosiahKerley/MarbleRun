import os
import time
from marblerun import Marble

marble = Marble()
#marble.verbose = True

print("Starting...")


##- Monitored job


## Process data
while True:
	data = marble.wait("test-monitored-alt")
	print data
	marble.finish()
