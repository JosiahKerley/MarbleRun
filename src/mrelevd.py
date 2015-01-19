from marblerun import Elevator
elev = Elevator()
elev.verbose = True

## Upstream options
elev.bustype = "redis"
elev.server = "localhost"
elev.password = None
elev.port = 6379
elev.channel = 1

## Run
elev.daemon()