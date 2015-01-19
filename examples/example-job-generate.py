import os
import time
import random
from marblerun import Marble

marble = Marble()
#marble.verbose = True

print("Starting...")


##- Monitored job


## Enqueue data
while True:
	num = random.randint(1,10)
	marble.send("test-monitored","Test Data: %s"%(str(num)))
	
	time.sleep(random.randint(1,200)/100)