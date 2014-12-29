import json
import uuid
import time
import redis
import socket

class Communicator:
	bustype	= "redis"
	server	= "localhost"
	port	= 6379
	channel	= 0
	ttl		= 60
	ttl		= 5
	
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





class Monitor:
	comm	= Communicator()
	id		= "0"
	queue	= "monitor"
	private	= "_private"
	lock	= "_lock"
	ttl		= comm.ttl


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
			message	=	{
							"id":self.id,"node":socket.gethostname(),
							"public":public,
							"private":private,
							"lock":lock,
							"timestamp":int(time.time())
						}
			self.comm.push(self.queue,json.dumps(message))
			return(self.comm.transfer(public,private))
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
		if lock == None: lock = self.lock
		try:
			self.comm.set(lock,True,self.ttl)
			return(True)
		except:
			return(False)


	## Process monitored queue
	def monitorQueue(self):
		message = self.comm.pop(self.queue)
		if not message == None:
			message = json.loads(message)
			print json.dumps(message,indent=2)
			c = 0
			while self.comm.get(message["lock"]):
				print("Locked for %ss"%(str(c)))
				c += 1
				time.sleep(1)
			if self.comm.dump(message["private"]):
				print("Looks like it died, adding it back to the original queue...")
				self.comm.push(message["public"],self.comm.pop(message["private"]))
			else:
				print("Looks good!")























