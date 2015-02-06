import os
import time
import random
from marblerun import Marble

marble = Marble()
#marble.verbose = True

print("Starting...")


##- Monitored job

items = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','1','2','3','4','5','6','7','8','9','0']
#items = ['A']
## Enqueue data
for i in items:
	marble.send("test-monitored-alt",i)