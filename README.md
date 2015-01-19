## MarbleRun
MarbleRun is a simple, asynchronous tool built for making batch processing easier.

### How it works:
MarbleRun is currently implemented with python and requires Redis.  Currently, jobs are added to a queue, and processed by python through the MR library.  Jobs can be either monitored (meaning that there is an error handling daemon that rides along with jobs) or unmonitored.

#### Classes
There are four classes currently implemented natively:

* Communicator - Handle all communication between the message bus and higher order classes/functions.  Provides verbs such as push and pop
* Elevator - Provides inter-node message passing and defacto data locality
* Monitor - Handles dropped jobs via a heartbeat mechanism
* Marble - Provides simple, high level access for scripts

#### Daemons
Although MR is not meant to be a service itself, but rather a toolkit for batch processing, there are two daemons currently built in to handle Monitor and Elevator services.  'mrmond.py' handles the Monitor functions, and 'mrelevd.py' handles the Elevator functions.

#### Example Jobs

##### Monitored job
Here is a basic job the pulls data in from a queue, processes it, and routes it to other queues:
```python
from marblerun import Marble
marble = Marble()

## Process data
while True:
	data = marble.wait("test-monitored")
	print data
	if data == "Test Data: 1":
		marble.elevate("test-monitored","sending this to a higher run!")
	if data == "Test Data: 3":
		marble.send("test-monitored","This data is at the back of the queue!")
		marble.expedite("test-monitored","This data is at the front of the queue!")
	marble.finish()
```
This example is a monitored run; it waits for data via the *wait* function, when data is available, it processes it, sends data to a another queue via the *elevate* function, adds data to a queue via the *send* function, and adds data to a queue for immediate processing via the *expidite* function.  Finally, it informs the monitor that execution was succesfull by issuing the *finish* function.

##### Unmonitored job
This example does the same as above, however, does not utilize a monitor.  This means that if the process crashes or hangs, there is no way for the system to know that the data needs to be re-added into it's original queue.

```python
marble = Marble()
marble.monitored = False

## Process data
while True:
	data = marble.wait("test-unmonitored")
	print data
```

##### Monitored job that will make the Monitors think it failed
Finally, this example demonstrates a job that will cause Monitors to think it failed by not issuing a *finish* when complete.

```python
from marblerun import Marble
marble = Marble()

## Process data
while True:
	data = marble.wait("test-monitored")
	print data
	if data == "Test Data: 3":
		marble.send("test-monitored","This data is at the back of the queue!")
		marble.expedite("test-monitored","This data is at the front of the queue!")
	#marble.finish()
```


#### Architecture












