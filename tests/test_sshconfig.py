from __future__ import print_function
import sshconfig
import pytest
import os

test_config = os.path.join(os.path.dirname(__file__), "test_config")

def test_parsing():
    c = sshconfig.read_ssh_config(test_config)
    assert len(c.hosts()) == 2
    assert c.host("*")["User"] == "something"
    assert c.host("svu")["ProxyCommand"] == "nc -w 300 -x localhost:9050 %h %p"

    s1 = c.config().splitlines()
    s2 = open(test_config).readlines()
    assert len(s1) == len(s2)

def test_update():
    c = sshconfig.read_ssh_config(test_config)

    c.update("svu", Compression="no", Port=2222)
    assert "\tCompression\tno" in c.config()
    assert "\tPort\t2222" in c.config()

def test_update_host_failed():
    c = sshconfig.read_ssh_config(test_config)

    with pytest.raises(ValueError):
        c.update("svu", Host="svu-new")

def test_rename():

    c = sshconfig.read_ssh_config(test_config)

    assert c.host("svu")["Hostname"] == "www.svuniversity.ac.in"

    c.rename("svu", "svu-new")

    assert "Host\tsvu-new" in c.config()
    assert "Host\tsvu\n" not in c.config()
    assert "svu" not in c.hosts()
    assert "svu-new" in c.hosts()

    c.update("svu-new", Port=123)  # has to be success
    assert c.host("svu-new")["Port"] == 123
    assert c.host("svu-new")["Hostname"] == "www.svuniversity.ac.in"  # still same

    with pytest.raises(ValueError):  # we can't refer to the renamed host
        c.update("svu", Port=123)

def test_update_fail():
    c = sshconfig.read_ssh_config(test_config)

    with pytest.raises(ValueError):
        c.update("notfound", Port=1234)

def test_add():

    c = sshconfig.read_ssh_config(test_config)

    c.add("venkateswara", Hostname="venkateswara.onion", User="other", Port=22,
          ProxyCommand="nc -w 300 -x localhost:9050 %h %p")

    assert "venkateswara" in c.hosts()
    assert c.host("venkateswara")["ProxyCommand"] == "nc -w 300 -x localhost:9050 %h %p"

    assert "Host\tvenkateswara" in c.config()

    with pytest.raises(ValueError):
        c.add("svu")

    with pytest.raises(ValueError):
        c.add("venkateswara")

def test_save():
    import tempfile

    tc = os.path.join(tempfile.gettempdir(), "temp_ssh_config-4123")
    try:
        c = sshconfig.read_ssh_config(test_config)

        c.update("svu", Hostname="ssh.svuniversity.ac.in", User="mca")
        c.write(tc)

        c2 = sshconfig.read_ssh_config(tc)
        assert c2.host("svu")["Hostname"] == "ssh.svuniversity.ac.in"
        assert c2.host("svu")["User"] == "mca"

    finally:
        os.remove(tc)

def test_empty():
    import tempfile
    tc = os.path.join(tempfile.gettempdir(), "temp_ssh_config-123")
    try:
        c = sshconfig.empty_ssh_config()
        c.add("svu33", Hostname="ssh33.svu.local", User="mca", Port=22)
        c.write(tc)
        c2 = sshconfig.read_ssh_config(tc)
        assert 1 == len(c2.hosts())
        assert c2.host("svu33")["Hostname"] == "ssh33.svu.local"
    finally:
        os.remove(tc)
