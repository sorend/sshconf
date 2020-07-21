#!/usr/bin/env python

from __future__ import print_function
from sshconf import read_ssh_config, empty_ssh_config_file
from os.path import expanduser

# read the user ssh config file and print hosts
c = read_ssh_config(expanduser("~/.ssh/config"))

# save it again
c.save()

# write it to a new file
c.write(expanduser("~/.ssh/new-config"))


# add a host
c.add("svu", Hostname="ssh.svu.local", Port=22, User="shakti")
print("svu", c.host("svu"))

# update a host
c.set("svu", Port=1234, ProxyJump="gateway.cs.svu-ac.in")
print("svu", c.host("svu"))

# remove a setting from a host
c.unset("svu", "ProxyJump")
print("svu", c.host("svu"))

# rename a host
c.rename("svu", "svu-server")
print("svu-server", c.host("svu-server"))

# list all hosts
all_hosts = c.hosts()
print("hosts", all_hosts)

# remove a host
c.remove("svu-server")
print("has svu-server?", "svu-server" in c.hosts())

# add a new include
i = empty_ssh_config_file()
i.add("svu-jumper", Hostname="venkatadri.cs.svu-ac.in", Port=2222, User="mcalogin")
c.add_include("jumpers", i)

# get the config as string
print(c.config())

# save it all
c.save()
