import os
import time
from marblerun import Marble

marble = Marble()
#marble.verbose = True

print("Starting...")


##- Monitored job


## Enqueue data
for i in range(1,5):
	marble.send("test-monitored","Test Data: %s"%(str(i)))

## Process data
while True:
	data = marble.wait("test-monitored")
	print data
	if data == "Test Data: 3":
		marble.send("test-monitored","This data is at the back of the queue!")
		marble.expedite("test-monitored","This data is at the front of the queue!")
	#marble.finish()
