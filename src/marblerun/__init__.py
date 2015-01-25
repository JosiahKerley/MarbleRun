#!/usr/bin/python

## Import Classes
import os
import sys
import json
import uuid
import time
import redis
import base64
import socket
import difflib
import platform
import multiprocessing
import cPickle as pickle

## Subclasses
from threading import Thread


## Globals
version = "0.1"


## Facilitates communitcation on the bus.
class Communicator:
	bustype		= "redis"
	server		= "localhost"
	password	= None
	port		= 6379
	channel		= 0
	ttl			= 1
	verbose		= False


	def serialize(self,data):
		try:
			retval = pickle.dumps(data)
		except:
			retval = False
		return(retval)


	def deserialize(self,data):
		try:
			retval = pickle.loads(data)
		except:
			retval = False
		return(retval)

	
	def __init__(self):
		if self.bustype == "redis":
			self.bus = redis.StrictRedis(host = self.server, port = self.port, db = self.channel, password = self.password)


	def push(self,queue,data,reverse=False,ttl=False):
		if self.bustype == "redis":
			if reverse:
				retval = self.bus.rpush(queue,self.serialize(data))
			else:
				retval = self.bus.lpush(queue,self.serialize(data))
			if ttl: self.bus.expire(queue,ttl)
			return(retval)

	def pop(self,queue,reverse=False):
		if self.bustype == "redis":
			if reverse:
				return(self.deserialize(self.bus.rpop(queue)))
			else:
				return(self.bus.lpop(queue))

	def transfer(self,output,input):
		if self.bustype == "redis":
			return(self.deserialize(self.bus.rpoplpush(output,input)))


	def dump(self,queue,pop=False):
		if self.bustype == "redis":
			items = []
			for i in range(0,self.bus.llen(queue)):
				if pop:
					items.append(self.deserialize(self.bus.rpop(queue)))
				else:
					items.append(self.deserialize(self.bus.lindex(queue,i)))
			return(items)

	def destroy(self,key):
		if self.bustype == "redis":
			try:
				return(self.bus.delete(key))
			except:
				return(False)

	def set(self,key,value,ttl=False):
		if self.bustype == "redis":
			val = self.bus.set(key,self.serialize(value))
			if ttl: self.bus.expire(key,ttl)
			return(val)

	def get(self,key,ttl=False):
		if self.bustype == "redis":
			if ttl: self.bus.expire(key,ttl)
			return(self.deserialize(self.bus.get(key)))

	def show(self,pattern):
		if self.bustype == "redis":
			return(self.bus.keys(pattern))


## Gives information
class Informant:

	## Info Model
	comm = Communicator()
	instanceid = str(uuid.uuid4())
	instancehost = socket.gethostname()
	instancename = os.path.basename(sys.argv[0])
	instancestart = time.time()
	instanceclass = None
	message = None
	lastmessage = None
	ops = 0


	## Sets status
	def status(self,message):
		self.comm.set("status_%s"%(self.instanceid),message,60)
		return(True)


	## Sets status message
	def message(self,message):
		if not self.lastmessage == self.message: self.lastmessage = self.message
		self.message = message
		return(True)

	## Increment the operation counter
	def opInc(self):
		self.ops +=1
		return(True)


	## Updates status
	def updateStatus(self):
		message = {
					"message":self.message,
					"lastmessage":self.lastmessage,
					"class":self.instanceclass,
					"id":self.instanceid,
					"host":self.instancehost,
					"name":self.instancename,
					"starttime":self.instancestart,
					"timestamp":time.time(),
					"ops":self.ops
		}
		return(self.status(message))


## Sends marbles to higher runs
class Elevator:
	
	## Instances
	comm = Communicator()
	info = Informant()
	info.instanceclass = "elevator"

	## Options
	upstream = None
	bustype = comm.bustype
	server = comm.server
	password = comm.password
	port = comm.port
	channel = comm.channel
	verbose = False
	pendqueue = "elevate_"
	ops = 0



	## Init
	def __init__(self):
		self.upstream = Communicator()
		self.upstream.bustype = self.bustype
		self.upstream.server = self.server
		self.upstream.password = self.password
		self.upstream.port = self.port
		self.upstream.channel = self.channel
		self.upstream.__init__()


	## Picks up
	def lift(self,queue,data):
		elevqueue = "%s%s"%(self.pendqueue,queue)
		return(self.comm.push(elevqueue,data))


	## Lists pending marbles
	def pending(self):
		if self.verbose: print("\t[I] Checking for pending marbles...")
		query = "%s*"%(self.pendqueue)
		return(self.comm.show(query))


	## Elevates	pending marbles
	def send(self):
		self.__init__()
		pending = self.pending()
		if not pending == None:
			for queue in pending:
				dataset = self.comm.dump(queue,True)
				try:
					if self.verbose: print("\t[I] Sending data to upstream server...")
					for data in dataset:
						self.upstream.push(queue.replace(self.pendqueue,''),data)
				except:
					if self.verbose: print("\t[E] Cannot communicate with upstream server!  Returning values to original queue")
					for data in dataset:
						self.comm.push(queue,data)
		self.ops += 1


	## Elevator Daemon
	def daemon(self):
		while True:
			self.send()
			time.sleep(1)




## Provides assured execution and failure handling
class Monitor:

	## State
	comm = Communicator()
	info = Informant()
	info.instanceclass = "monitor"
	id = "0"
	queue = "monitor"
	private = "_private"
	lock = "_lock"
	ttl = comm.ttl
	verbose = False


	## Init
	def __init__(self):
		self.id			= str(uuid.uuid4())
		self.private	= "%s_private"%(self.id)
		self.lock		= "%s_lock"%(self.id)


	## Inform the monitor of what queue to watch and transfer the data
	def checkout(self,public=None,private=None,lock=None):
		if public	== None: public		= self.public
		if private	== None: private	= self.private
		if lock		== None: lock		= self.lock
		try:
			data = self.comm.transfer(public,private)
			if data == None:
				if self.verbose: print("\t[M] No work in queue '%s'"%(public))
				return(False)
			else:
				if self.verbose: print("\t[M] Found '%s' in queue '%s'"%(data,public))
				message	=	{
								"id":self.id,"node":socket.gethostname(),
								"public":public,
								"private":private,
								"lock":lock,
								"timestamp":int(time.time())
							}
				self.comm.push(self.queue,message)
				return(data)
		except:
			return(False)


	## Close out the session
	def finish(self,private=None,lock=None):
		if private	== None: private	= self.private
		if lock		== None: lock		= self.lock
		for i in [lock,private]:
			self.comm.destroy(i)


	## Heartbeat
	def heartbeat(self,lock=None):
		if self.verbose: print("\t[M] Sending heartbeat")
		if lock == None: lock = self.lock
		try:
			self.comm.set(lock,True,self.ttl)
			if self.verbose: print("\t\t[M] Heartbeat success")
			return(True)
		except:
			if self.verbose: print("\t\t[M] Heartbeat failed")
			return(False)


	## Process monitored queue
	def monitorQueue(self):
		self.info.updateStatus()
		message = self.comm.pop(self.queue,True)
		if message:
			if self.verbose: print("\t[M] Message from worker received")
			if self.verbose: print("\t\t[M] Message details:")
			if self.verbose: print(json.dumps(message,indent=2)+"\n\n\n")
			c = 0
			self.comm.set(message["lock"],True,self.ttl)
			#self.comm.set(message["lock"],True,1)
			while self.comm.get(message["lock"]):
				self.info.message = "Monitoring %s"%(message["lock"])
				self.info.updateStatus()
				if self.verbose: print("\t[M] Locked for %ss"%(str(c)))
				c += 1
				time.sleep(1)
			self.info.opInc()
			if self.comm.dump(message["private"]):
				if self.verbose: print("\t[M] Looks like it died, adding it back to the original queue...")
				self.comm.push(message["public"],self.comm.pop(message["private"]))
			else:
				if self.verbose: print("\t[M] Job completed on its own volition")
		else:
			self.info.message = "waiting"
			self.info.updateStatus()
			if self.verbose: print("\t[M] No messages from workers found")


	## Monitor Daemon
	def daemon(self):
		self.info.message = "Started"
		self.info.updateStatus()
		while True:
			self.monitorQueue()
			time.sleep(0.1)






## The in-script handler
class Marble:

	## Instances
	mon = Monitor()
	elev = Elevator()
	info = Informant()
	comm = Communicator()
	info.instanceclass = "marble"


	## Options
	monitored = True
	fail_after = 60
	wait_poll = 0.1
	verbose	= False


	## Other
	hbpid = None
	hbstate = False


	## Init
	def __init__(self):
		self.instancename = os.path.basename(__file__)
		self.instanceid = str(uuid.uuid4())
		self.instancehost = socket.gethostname()
		self.instancestart = time.time()


	## Sets up connection
	def connect(self,bustype=None,server=None,port=None,password=None,channel=None):
		try:
			if bustype == None: bustype = self.comm.bustype
			if server == None: server = self.comm.server
			if port == None: port = self.comm.port
			if password == None: password = self.comm.password
			if channel == None: channel = self.comm.channel
			self.comm.bustype = bustype
			self.comm.server = server
			self.comm.port = port
			self.comm.password = password
			self.comm.channel = channel
			self.comm.__init__()
			return(True)
		except:
			return(False)


	## Checks for data
	def check(self,queue):
		if self.monitored:
			data = self.mon.checkout(queue)
		else:
			data = self.comm.pop(queue)
		return(data)


	## Waits for data
	def wait(self,queue):
		hbstate = False
		data = self.check(queue)
		self.info.updateStatus()
		while data == None or data == False:
			self.info.message = "waiting"
			time.sleep(self.wait_poll)
			if self.verbose: print("\t[I] Nothing in queue %s, waiting %s seconds..."%(queue,self.wait_poll))
			data = self.check(queue)
			self.info.updateStatus()
		self.info.message = "Executing job"
		self.info.updateStatus()
		self.info.opInc()
		if self.monitored:
			hbstate = True
			self.hbpid = Thread(target=self.heartbeat)
			self.hbpid.start()
		return(data)


	## Keeps job alive in the monitor
	def heartbeat(self):
		while self.hbstate:
			self.mon.heartbeat()
			time.sleep(self.comm.ttl / 4)


	## Tells the monitor the job is finished
	def finish(self):
		self.hbstate = False
		self.mon.finish()


	## Sends data to a queue
	def send(self,queue,data):
		self.comm.push(queue,data)
		if self.verbose: print("\t[I] Sending data to queue %s"%(queue))


	## Sends data to a queue
	def expedite(self,queue,data):
		self.comm.push(queue,data,True)
		if self.verbose: print("\t[I] Sending data to front of queue %s"%(queue))


	## Elevate a marble
	def elevate(self,queue,data):
		self.elev.lift(queue,data)
		if self.verbose: print("\t[I] Sending data to an upstream queue %s"%(queue))


	## Reports message
	def report(self,message):
		self.info.message = message
		self.info.updateStatus()




## CLI Tools
class CLI:
	comm = Communicator()


	## Verb options
	subjects = ["running","startup","starting","cli"]
	displaytypes = ["table","json"]
	rotations = ["horizontal","vertical"]
	tabletypes = ["none","grid","top"]
	labels = ['node','class','name','message','ops','uptime','sync','id']


	## Init
	def __init__(self):

		## Loads display type
		if not self.comm.get("cli_option_display"):
			self.display = "table"

		## Loads labels
		if not self.comm.get("cli_option_labels"):
			self.comm.set("cli_option_labels",self.labels)
		if not self.comm.get("cli_option_labelorder"):
			self.comm.set("cli_option_labelorder",self.labels)



		## Loads rotation
		if not self.comm.get("cli_option_rotation"):
			self.rotation = "vertical"


		## Loads table type
		if not self.comm.get("cli_option_tabletype"):
			self.tabletype = "top"



	## Rotate 2d arrays
	def rotate(self,matrix,degree=90):
		if degree in [0, 90, 180, 270, 360]:
			return matrix if not degree else self.rotate(zip(*matrix[::-1]), degree-90)


	## Display a table
	def tableview(self,matrix,label=None):
		s = [[str(e) for e in row] for row in matrix]
		lens = [max(map(len, col)) for col in zip(*s)]
		fmt = ' | '.join('{{:{}}}'.format(x) for x in lens)
		table = [fmt.format(*row) for row in s]
		tabletext = ''
		if not label or label == "none":
			for i in table:
				tabletext += i+'\n'
		elif label == "top":
			tabletext = table[0]+'\n'+'-'*len(max(table))+'\n'
			for i in table[1:]:
				tabletext += i+'\n'
		elif label == "grid":
			line = '-'*len(max(table))
			tabletext = line + '\n'
			for i in table:
				tabletext += i + '\n' + line + '\n'
		return(tabletext)


	## Gets status
	def status(self):
		nodes = self.comm.show('status_*')
		nodestatus = []
		for node in nodes:
			cursor = {}
			data = self.comm.get(node)
			cursor['node'] = data['host']
			cursor['sync'] = str(time.time() - data['timestamp'])
			cursor['uptime'] = str(data['timestamp'] - data['starttime'])
			cursor['class'] = data['class']
			cursor['name'] = data['name']
			cursor['id'] = data['id']
			cursor['message'] = data['message']
			cursor['ops'] = data['ops']
			nodestatus.append(cursor)
		headers = nodestatus[0].keys()
		rows = []
		for node in nodestatus:
			row = []
			for header in headers:
				row.append(node[header])
			rows.append(row)
		matrixraw = self.rotate([headers] + rows,270)
		matrix = []
		matrixall = []
		if self.rotation == "horizontal": degree = 0
		if self.rotation == "vertical": degree = 90
		for i in matrixraw:
			matrixall.append(list(i))

		## Get only allowed items
		items = self.comm.get("cli_option_labels")
		for i in matrixall:
			if i[0] in items:
				matrix.append(i)

		## Order items
		matrixordered = []
		for anchor in self.comm.get("cli_option_labelorder"):
			for cursor in matrix:
				if anchor == cursor[0]:
					if not cursor in matrixordered: matrixordered.append(cursor)
		for i in matrixordered:
			matrix.remove(i)
		matrix = matrix+matrixordered
		
		## Display
		if self.display == "json":
			print(json.dumps(nodestatus,indent=2))
		elif self.display == "table":
			print(self.tableview(self.rotate(matrix,degree),self.tabletype))




	## Cleany display time
	def cleanTime(self,seconds):
		m, s = divmod(seconds, 60)
		h, m = divmod(m, 60)
		time = "%d:%02d:%02d"%(h, m, s)
		return(time)


	## Help
	def help(self,key=None):
		if key == None:
			text = 'This is help text.\nIt is the default one.'
		if key == 'show':
			text = 'This is help text.\nIt is the "show" one.'
		print(text)


	## Error
	def error(self, text, level=1):
		print "\t[E] %s"%(text)


	## The 'show' verb
	def show(self,subject=False, action=False, option=False):
		c = False
		if subject:
			sub = False
			try: sub = difflib.get_close_matches(subject, self.subjects)[0]
			except: pass
			if sub:
				if sub == 'running':
					self.status()
				elif sub == 'startup':
					pass
				elif sub == 'starting':
					pass
				elif sub == 'cli':
					if action.lower() == "items":
						print self.comm.get("cli_option_labels")
			else:
				self.error("Unknown subject '%s'"%(subject))
			c+=1
		if not c:
			self.help('show')


	## The 'set' verb
	def set(self,subject=False, action=False, option=False):
		c = False
		if subject:
			sub = False
			try: sub = difflib.get_close_matches(subject, self.subjects)[0]
			except: pass
			if sub:
				if sub == 'running':
					self.status()
				elif sub == 'startup':
					pass
				elif sub == 'starting':
					pass
				elif sub == 'cli':
					if action.lower() == "display":
						if option.lower() in self.displaytypes:
							self.comm.set("cli_option_display",option.lower())
						else:
							self.error("Unknown option '%s'"%(option))
					elif action.lower() == "rotation" or action.lower() == "rotate" or action.lower() == "orientation" or action.lower() == "orient":
						if option.lower() in self.rotations:
							self.comm.set("cli_option_rotation",option.lower())
						else:
							self.error("Unknown option '%s'"%(option))
					elif action.lower() == "table":
						if option.lower() in self.tabletypes:
							self.comm.set("cli_option_tabletype",option.lower())
						else:
							self.error("Unknown option '%s'"%(option))
					elif action.lower() == "label":
						if option.lower() == "order":
							print "Current:"
							print self.comm.get("cli_option_labelorder")
							order = raw_input("\nNew: ")
							if order == "":
								self.comm.set("cli_option_labelorder",self.comm.get("cli_option_tables"))
							else:
								self.comm.set("cli_option_labelorder",order.split(' '))
						else:
							self.error("Unknown option '%s'"%(option))
					else:
						self.error("Unknown action '%s'"%(action))
			else:
				self.error("Unknown subject '%s'"%(subject))
			c+=1
		if not c:
			self.help('show')



	## The 'add' verb
	def add(self,subject=False, action=False, option=False):
		c = False
		if subject:
			sub = False
			try: sub = difflib.get_close_matches(subject, self.subjects)[0]
			except: pass
			if sub:
				if sub == 'running':
					self.status()
				elif sub == 'startup':
					pass
				elif sub == 'starting':
					pass
				elif sub == 'cli':
					if action.lower() == "tag" or action.lower() == "label":
						current = self.comm.get("cli_option_labels")
						if option.lower() in self.labels:
							current += [option.lower()]
							print current
						else:
							self.error("Unknown label '%s'"%(option))
						self.comm.set("cli_option_labels",current)
					else:
						self.error("Unknown action '%s'"%(action))
			else:
				self.error("Unknown subject '%s'"%(subject))
			c+=1
		if not c:
			self.help('show')


	## The 'remove' verb
	def remove(self,subject=False, action=False, option=False):
		c = False
		if subject:
			sub = False
			try: sub = difflib.get_close_matches(subject, self.subjects)[0]
			except: pass
			if sub:
				if sub == 'running':
					self.status()
				elif sub == 'startup':
					pass
				elif sub == 'starting':
					pass
				elif sub == 'cli':
					if action.lower() == "tag" or action.lower() == "label":
						current = self.comm.get("cli_option_labels")
						current.remove(option.lower())
						self.comm.set("cli_option_labels",current)
					else:
						self.error("Unknown action '%s'"%(action))
			else:
				self.error("Unknown subject '%s'"%(subject))
			c+=1
		if not c:
			self.help('show')


	## Parse arguments
	def parseArgs(self,arglist):
		params = []
		args = arglist[1:]
		i = 0
		quoted = False
		selection = ''
		while i < len(args):
			if "'" in args[i] or '"' in args[i]:
					quoted = not quoted
			if not quoted:
				selection += args[i]
			params.append(selection)
			selection = ''
			i+=1
		return(params)


	## Process arguments
	def args(self,arglist):

		## Get params
		params = self.parseArgs(arglist)
		verb = False
		subject = False
		action = False
		options = False

		## Pick out command args
		try:
			verb = params[0]
			try:
				subject = params[1]
				try:
					action = params[2]
					try:
						options = params[3]
					except: pass
				except: pass
			except: pass
		except: pass
		

		## Handle verbs
		if verb:
			if verb.lower() == "show" or verb.lower() == "get":
				self.show(subject,action,options)
			elif verb.lower() == "set":
				self.set(subject,action,options)
			elif verb.lower() == "add":
				self.add(subject,action,options)
			elif verb.lower() == "remove" or verb.lower() == "rem":
				self.remove(subject,action,options)
			else:
				self.error("Unknown verb '%s'"%(verb))
		else:
			self.help()
































































