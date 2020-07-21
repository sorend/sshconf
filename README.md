
sshconf
===========

[![PyPi version](https://pypip.in/v/sshconf/badge.png)](https://github.com/sorend/sshconf)
[![Build Status](https://travis-ci.com/sorend/sshconf.svg?branch=master)](https://travis-ci.com/sorend/sshconf)
[![codecov](https://codecov.io/gh/sorend/sshconf/branch/master/graph/badge.svg)](https://codecov.io/gh/sorend/sshconf)


Sshconf is a library for reading and modifying your ssh/config file in a non-intrusive way, meaning
your file should look more or less the same after modifications. Idea is to keep it simple,
so you can modify it for your needs.

Read more about ssh config files here: [Create SSH config file on Linux](https://www.cyberciti.biz/faq/create-ssh-config-file-on-linux-unix/)


Installation and usage
---------------------------

Install through pip is the most easy way. You can install from the Git source directly:

    pip install sshconf

### Reading and writing

    from __future__ import print_function
    from sshconf import read_ssh_config, empty_ssh_config_file
    from os.path import expanduser

    # read the user ssh config file and print hosts
    c = read_ssh_config(expanduser("~/.ssh/config"))

    # save it again
    c.save()

    # write it to a new file
    c.write(expanduser("~/.ssh/new-config"))

### Working with hosts

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

### Working with includes

    # add a new include
    i = empty_ssh_config_file()
    i.add("svu-jumper", Hostname="venkatadri.cs.svu-ac.in", Port=2222, User="mcalogin")
    c.add_include("jumpers", i)

    # get the config as string
    print(c.config())

    # save it all
    c.save()


About
-----

sshconf is created at the Department of Computer Science at Sri Venkateswara University, Tirupati, INDIA by a student as part of his projects.
