#!/usr/bin/python
import os
import time
import json
import uuid
import socket
from marblerun import Marble
from marblerun import Communicator
marble = Marble()
comm = Communicator()




## Settings
with open('fd-conf.json','r') as f: config = json.loads(f.read())


## Creates an identifier for a file
def fileID(filepath):
	return(os.path.getsize(filepath))

## Informs other nodes of changes
if not os.path.isdir(config['path']):
	os.makedirs(config['path'])
os.chdir(config['path'])
while True:
	changes = marble.wait('fd_%s_%s_changes'%(config['group'],socket.gethostname()))
	print json.dumps(changes,indent=2)
	for member in comm.get('fd_members_'+config['group']):
		for filepath in changes['remove']:
			marble.send('fd_remove_%s_%s'%(config['group'],member),{"member":socket.gethostname(),"filepath":filepath})
		for filepath in changes['add']:
			marble.send('fd_add_%s_%s'%(config['group'],member),{"member":socket.gethostname(),"filepath":filepath,"id":fileID(filepath)})
time.sleep(5)