
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


Below is some example use:

    from __future__ import print_function
    from sshconf import read_ssh_config, empty_ssh_config
    from os.path import expanduser

    c = read_ssh_config(expanduser("~/.ssh/config"))
    print("hosts", c.hosts())

    # assuming you have a host "svu"
    print("svu host", c.host("svu"))  # print the settings
    c.set("svu", Hostname="ssh.svu.local", Port=1234)
    print("svu host now", c.host("svu"))
    c.unset("svu", "port")
    print("svu host now", c.host("svu"))

    c.add("newsvu", Hostname="ssh-new.svu.local", Port=22, User="stud1234")
    print("newsvu", c.host("newsvu"))

    c.rename("newsvu", "svu-new")
    print("svu-new", c.host("svu-new"))

    # overwrite existing file(s)
    c.save()

    # write all to a new file
    c.write(expanduser("~/.ssh/newconfig"))

    # creating a new config file.
    c2 = empty_ssh_config_file()
    c2.add("svu", Hostname="ssh.svu.local", User="teachmca", Port=22)
    c2.write("newconfig")

    c2.remove("svu")  # remove


A few things to note:
- `save()` overwrites the files you read from.
- `write()` writes a new config file. If you used `Include` in the read configuration, output will contain everything in one file.
- indent for new lines is auto-probed from existing config lines, and defaults to two spaces.


About
-----

sshconf is created at the Department of Computer Science at Sri Venkateswara University, Tirupati, INDIA by a student as part of his projects.
