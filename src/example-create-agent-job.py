import json
import time
import socket
import base64
from marblerun import Agent
from marblerun import Communicator

agent = Agent()
comm = Communicator()

script = '''
import time
print "starting job!"
time.sleep(10)
print "I'm done!"
'''

job	=	{
			"script":	{
							"filename":"test.py",
							"executor":"python",
							"arguments":"",
							"contents":base64.b64encode(script),
						}
		}
comm.push(socket.gethostname(),json.dumps(job))
time.sleep(3)