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


## Return tree list
def tree(root):
	treelist = []
	for dirname, dirnames, filenames in os.walk('.'):
		for filename in filenames:
			path = os.path.join(dirname, filename)
			path = path.replace('\\','/')
			path = path.replace('./','')
			treelist.append(path)
	for ignore in config['ignore']:
		for path in treelist:
			if ignore in path:
				treelist.remove(path)
	return(treelist)


## Run the indexer
last = []
id = uuid.uuid1
if not os.path.isdir(config['path']):
	os.makedirs(config['path'])
os.chdir(config['path'])
while True:
	current = tree(config['path'])
	if not current == last:
		add = list(set(current) - set(last))
		remove = list(set(last) - set(current))
		changes = {"add":add,"remove":remove}
		marble.send('fd_%s_%s_changes'%(config['group'],socket.gethostname()),changes)
	last = current
	try: members = list(set([socket.gethostname()] + comm.get('fd_members_'+config['group'])))
	except: members = [socket.gethostname()]
	comm.set('fd_members_'+config['group'],members,config['timeout'])
	time.sleep(config['freq'])