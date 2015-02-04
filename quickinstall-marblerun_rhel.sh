#!/bin/bash

url=https://github.com/JosiahKerley/MarbleRun
cd /tmp
git clone $url
cd MarbleRun
yum install -y redis python-redis
chkconfig redis on
service redis restart
pip install redis
mkdir -p /opt/MarbleRun/daemons
mkdir -p /opt/MarbleRun/conf.d
mkdir -p /opt/MarbleRun/examples
mkdir -p /etc/marblerun
ln -s /opt/MarbleRun/conf.d /etc/marblerun/
ln -s /opt/MarbleRun/daemons/mrmon.py /usr/bin/mr-monitor
chmod +x /usr/bin/mr-monitor
echo '{"path": "/opt/MarbleRun/daemons/mrmond.py","dir": "/tmp","instances": "<[cores]>-1"}' > /etc/marblerun/conf.d/01-monitor.json
cp daemons/* /opt/MarbleRun/daemons/
cp examples/* /opt/MarbleRun/examples/
chmod +x /opt/MarbleRun/daemons/*
cat tools/mr.py > /usr/bin/mr
chmod +x /usr/bin/mr
cd src
python setup.py install
cd /tmp
rm -rf MarbleRun
iptable -A INPUT -p tcp -m tcp --dport 6379 -j ACCEPT
service iptables save
