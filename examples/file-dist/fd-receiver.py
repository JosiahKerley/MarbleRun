#!/usr/bin/python
import os
import time
import json
import uuid
import socket
from threading import Thread
from marblerun import Marble
from marblerun import Communicator
marble = Marble()
comm = Communicator()




## Settings
with open('fd-conf.json','r') as f: config = json.loads(f.read())
running = True


## Fetch file
def fetchFile(filepath,member,port=config['port']):
	print("Sync '%s' from '%s'"%(filepath,member))


## Creates an identifier for a file
def fileID(filepath):
	return(os.path.getsize(filepath))


## Handles removed files
def removeFiles():
	while running:
		change = marble.wait('fd_remove_%s_%s'%(config['group'],socket.gethostname()))
		print change
		if os.path.isfile(change['filepath']):
			os.remove(change['filepath'])



## Handles added files
def addFiles():
	while running:
		change = marble.wait('fd_add_%s_%s'%(config['group'],socket.gethostname()))
		print change
		if os.path.isfile(change['filepath']) and not change['id'] == fileID(change['filepath']):
			fetchFile(change['filepath'],change['member'])





## Listens for updates
if __name__ == '__main__':
	if not os.path.isdir(config['path']):
		os.makedirs(config['path'])
	os.chdir(config['path'])
	remove = Thread(target=removeFiles)
	remove.start()
	add = Thread(target=addFiles)
	add.start()
	try:
		while True:
			pass
			time.sleep(1)
	except KeyboardInterrupt:
		pass
running = False