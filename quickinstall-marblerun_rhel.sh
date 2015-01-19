#!/bin/bash

url=https://github.com/JosiahKerley/MarbleRun
cd /tmp
git clone $url
cd MarbleRun
yum install -y redis
chkconfig redis on
service redis restart
pip install redis
mkdir -p /opt/MarbleRun/daemons
mkdir -p /opt/MarbleRun/conf.d
mkdir -p /opt/MarbleRun/examples
mkdir -p /etc/marblerun
ln -s /opt/MarbleRun/conf.d /etc/marblerun/
echo '{"path": "/opt/MarbleRun/daemons/mrmond.py","dir": "/tmp","instances": "<[cores]>-1"}' > /etc/marblerun/conf.d/01-monitor.json
cp daemons/* /opt/MarbleRun/daemons/
cp examples/* /opt/MarbleRun/examples/
chmod +x /opt/MarbleRun/daemons/*
cd src
python setup.py install
cd /tmp
rm -rf MarbleRun

