#!/usr/bin/python
import os
import time
import uuid
import json
import socket
from threading import Thread
from marblerun import Marble
from marblerun import Communicator
marble = Marble()
comm = Communicator()


## Settings
config = {
			"group":"default",
			"path":"sync",
			"timeout":120,
			"freq":1,
			"ignore":[".cache"],
			"port":5147
}
config['group'] = 'fd_'+config['group']


## Checks for changes
change = None
running = True
def checkChanges():
	serving = []
	while running:
		changes = marble.wait('fd_%s_%s_changes'%(config['group'],socket.gethostname()))
		#try:
		if type(changes) == type({}):
			print type(changes)
			fresh = []
			if changes['remove'] in serving:
				serving.remove(changes['remove'])
			serving += changes['add']
			print "\n"
			print serving
			print "\n"
			time.sleep(1)
			memberids = comm.show('fd_member_*')
			for memberid in memberids:
				if not changes['remove'] == []:
					marble.send('fd_%s_%s_remove'%(config['group'],comm.get(memberid)),changes['remove'])
					#comm.destroy('fd_%s_%s_remove'%(config['group'],socket.gethostname()))
				print changes['add']
				print 'fd_%s_%s_add'%(config['group'],comm.get(memberid))
				if not changes['add'] == []:
					for add in changes['add']:
						try: marble.send('fd_%s_%s_add'%(config['group'],comm.get(memberid)),add)
						except: pass
					comm.set('fd_%s_%s_add'%(config['group'],socket.gethostname()),serving)
		#except: pass


#checkChanges()

## Serves the files
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
class myHandler(BaseHTTPRequestHandler):

	## List of files to serve
	servefiles = []
	
	## Handler for the GET requests
	def do_GET(self):
		updates = comm.get('fd_%s_%s_add'%(config['group'],socket.gethostname()))
		if type(updates) == type([]):
			self.servefiles += updates
		serving = list(set(self.servefiles))
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		self.wfile.write(json.dumps(serving,indent=2))
		return
try:
	server = HTTPServer(('', config['port']), myHandler)
	print('Started FD-Server on port ',config['port'])
	change = Thread(target=checkChanges)
	change.start()
	server.serve_forever()
except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	running = False
	server.socket.close()








