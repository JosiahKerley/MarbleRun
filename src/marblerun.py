import os
import json
import uuid
import time
import redis
import base64
import socket
import platform
import multiprocessing


## Facilitates communitcation on the bus.
class Communicator:
	bustype	= "redis"
	server	= "localhost"
	port	= 6379
	channel	= 0
	ttl		= 15
	verbose	= False

	
	def __init__(self):
		if self.bustype == "redis":
			self.bus = redis.StrictRedis(host = self.server, port = self.port, db = self.channel)

	def push(self,queue,data,reverse=False):
		if self.bustype == "redis":
			if reverse:
				return(self.bus.rpush(queue,data))
			else:
				return(self.bus.lpush(queue,data))

	def pop(self,queue,reverse=False):
		if self.bustype == "redis":
			if reverse:
				return(self.bus.rpop(queue))
			else:
				return(self.bus.lpop(queue))

	def transfer(self,output,input):
		if self.bustype == "redis":
			return(self.bus.rpoplpush(output,input))

	def dump(self,queue,pop=False):
		if self.bustype == "redis":
			items = []
			for i in range(0,self.bus.llen(queue)):
				if pop:
					items.append(self.bus.rpop(queue))
				else:
					items.append(self.bus.lindex(queue,i))
			return(items)

	def destroy(self,key):
		if self.bustype == "redis":
			try:
				return(self.bus.delete(key))
			except:
				return(False)

	def set(self,key,value,ttl=False):
		if self.bustype == "redis":
			val = self.bus.set(key,value)
			if ttl: self.bus.expire(key,ttl)
			return(val)

	def get(self,key,ttl=False):
		if self.bustype == "redis":
			if ttl: self.bus.expire(key,ttl)
			return(self.bus.get(key))




## Provides assured execution and failure handling
class Monitor:
	comm	= Communicator()
	id		= "0"
	queue	= "monitor"
	private	= "_private"
	lock	= "_lock"
	ttl		= comm.ttl
	verbose	= False


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
				self.comm.push(self.queue,json.dumps(message))
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
		message = self.comm.pop(self.queue)
		if not message == None:
			if self.verbose: print("\t[M] Message from worker received")
			message = json.loads(message)
			if self.verbose: print("\t\t[M] Message details:")
			if self.verbose: print(json.dumps(message,indent=2)+"\n\n\n")
			c = 0
			while self.comm.get(message["lock"]):
				if self.verbose: print("\t[M] Locked for %ss"%(str(c)))
				c += 1
				time.sleep(1)
			if self.comm.dump(message["private"]):
				if self.verbose: print("\t[M] Looks like it died, adding it back to the original queue...")
				self.comm.push(message["public"],self.comm.pop(message["private"]))
			else:
				if self.verbose: print("\t[M] Job completed on its own volition")
		else:
			if self.verbose: print("\t[M] No messages from workers found")


## Gathers and reports information about nodes
class Informant:
	comm			= Communicator()
	id				= "0"
	nodemodel		= "%s_nodemodel"%(id)
	reportqueue		= "%s_reportedinfo"%(id)
	verbose			= False
	nodemodel		= {}
	clustermodel	= {}


	def __init__(self):
		self.nodemodel = self.gatherSystemInfo()


	def gatherSystemInfo(self):
		model	=	{
						"hostname"	:	False,
						"ip"		:	False,
						"kernel"	:	False,
						"os"		:	False,
						"family"	:	False,
						"version"	:	False,
						"virtual"	:	False,
						"arch"		:	False,
					}
		model["hostname"]		= socket.gethostname()
		model["ip"]				= socket.gethostbyname(socket.gethostname())
		model["arch"]			= os.environ["PROCESSOR_ARCHITECTURE"]
		if os.name == 'nt':
			model["kernel"]		= ['nt']
			model["os"]			= ['windows']
			model["family"]		= ['nt']
			model["version"]	= platform.win32_ver()
		return(model)


	def reportModel(self):
		self.comm.push(self.reportqueue,json.dumps(self.model))


	def compileNodeModel(self):
		model = {}
		reportednodes = self.comm.dump(self.reportqueue,True)
		for nodejson in reportednodes:
			node = json.loads(nodejson)
			model[node["hostname"]] = node
		self.clustermodel = model
		return(model)


	def postNodeModel(self):
		self.comm.set(self.clustermodel,json.dumps(self.clustermodel))


	def getNodeModel(self):
		return(json.loads(self.comm.get(self.clustermodel)))



class Agent:
	comm	= Communicator()
	info	= Informant()
	verbose	= False
	maxpids	= multiprocessing.cpu_count() - 1
	pool	= None


	def rallyWorkers_(self):
		self.pool = multiprocessing.Pool(self.maxpids)
		self.pool.map(f, range(self.maxpids))


	def doWork(self):
		mon	= Monitor()
		job = mon.checkout(socket.gethostname())
		if job:
			job = json.loads(job)
			with open(job["script"]["filename"],"w") as f:
				f.write(base64.b64decode(job["script"]["contents"]))
			proc = multiprocessing.Process(target=self.workerSpace, args=(job["script"]["executor"],job["script"]["filename"],job["script"]["arguments"],))
			proc.start()
			while proc.is_alive():
				mon.heartbeat()
				time.sleep(1)
			mon.finish()

	def workerSpace(self,executor,filename,arguments=None):
		cmd = '"%s" "%s" "%s"'%(executor,filename,arguments)
		cmd = '%s %s %s'%(executor,filename,arguments)
		print cmd
		try:
			os.system(cmd)
			return(True)
		except:
			return(False)














#if self.verbose: print("\t\t[] ")








































