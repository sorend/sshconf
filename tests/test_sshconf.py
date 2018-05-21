from __future__ import print_function
import sshconf
import pytest
import os

test_config = os.path.join(os.path.dirname(__file__), "test_config")
test_config2 = os.path.join(os.path.dirname(__file__), "test_config2")

def test_parsing():
    c = sshconf.read_ssh_config(test_config)
    assert len(c.hosts()) == 2
    assert c.host("*")["user"] == "something"
    assert c.host("svu")["proxycommand"] == "nc -w 300 -x localhost:9050 %h %p"

    s1 = c.config().splitlines()
    s2 = open(test_config).readlines()
    assert len(s1) == len(s2)

def test_set():
    c = sshconf.read_ssh_config(test_config)

    c.set("svu", Compression="no", Port=2222)

    print(c.config())
    print("svu", c.host('svu'))
    
    assert "\tCompression\tno" in c.config()
    assert "\tPort\t2222" in c.config()

def test_set_host_failed():
    c = sshconf.read_ssh_config(test_config)

    with pytest.raises(ValueError):
        c.set("svu", Host="svu-new")

def test_rename():

    c = sshconf.read_ssh_config(test_config)

    assert c.host("svu")["hostname"] == "www.svuniversity.ac.in"

    c.rename("svu", "svu-new")

    assert "Host\tsvu-new" in c.config()
    assert "Host\tsvu\n" not in c.config()
    assert "svu" not in c.hosts()
    assert "svu-new" in c.hosts()

    c.set("svu-new", Port=123, HostName="www.svuniversity.ac.in")  # has to be success
    assert c.host("svu-new")["port"] == 123
    assert c.host("svu-new")["hostname"] == "www.svuniversity.ac.in"  # still same

    with pytest.raises(ValueError):  # we can't refer to the renamed host
        c.set("svu", Port=123)

def test_update_fail():
    c = sshconf.read_ssh_config(test_config)

    with pytest.raises(ValueError):
        c.set("notfound", Port=1234)

def test_add():

    c = sshconf.read_ssh_config(test_config)

    c.add("venkateswara", Hostname="venkateswara.onion", User="other", Port=22,
          ProxyCommand="nc -w 300 -x localhost:9050 %h %p")

    assert "venkateswara" in c.hosts()
    assert c.host("venkateswara")["proxycommand"] == "nc -w 300 -x localhost:9050 %h %p"

    assert "Host\tvenkateswara" in c.config()

    with pytest.raises(ValueError):
        c.add("svu")

    with pytest.raises(ValueError):
        c.add("venkateswara")

def test_save():
    import tempfile
    tc = os.path.join(tempfile.gettempdir(), "temp_ssh_config-4123")
    try:
        c = sshconf.read_ssh_config(test_config)

        c.set("svu", Hostname="ssh.svuniversity.ac.in", User="mca")
        c.write(tc)

        c2 = sshconf.read_ssh_config(tc)
        assert c2.host("svu")["hostname"] == "ssh.svuniversity.ac.in"
        assert c2.host("svu")["user"] == "mca"

        assert c.config() == c2.config()

    finally:
        os.remove(tc)

def test_empty():
    import tempfile
    tc = os.path.join(tempfile.gettempdir(), "temp_ssh_config-123")
    try:
        c = sshconf.empty_ssh_config()
        c.add("svu33", HostName="ssh33.svu.local", User="mca", Port=22)
        c.write(tc)
        c2 = sshconf.read_ssh_config(tc)
        assert 1 == len(c2.hosts())
        assert c2.host("svu33")["hostname"] == "ssh33.svu.local"
    finally:
        os.remove(tc)

def test_mapping_set_existing_key():
    c = sshconf.read_ssh_config(test_config)
    c.set("svu", Hostname="ssh.svuniversity.ac.in", User="mca", proxycommand="nc --help")

    print(c.config())
    
    assert "Hostname\tssh.svuniversity.ac.in" in c.config()
    assert "User\tmca" in c.config()
    assert "ProxyCommand\tnc --help" in c.config()

def test_mapping_set_new_key():
    c = sshconf.read_ssh_config(test_config)

    c.set("svu", forwardAgent='yes', unknownpropertylikethis='noway')

    assert "Hostname   www.svuniversity.ac.in" in c.config()  # old parameters
    assert "Port       22" in c.config()
    assert "ForwardAgent\tyes" in c.config()  # new parameter has been properly cased
    assert "unknownpropertylikethis\tnoway" in c.config()

def test_mapping_add_new_keys():
    c = sshconf.read_ssh_config(test_config)
    c.add("svu-new", forwardAgent="yes", unknownpropertylikethis="noway", Hostname="ssh.svuni.local",
          user="mmccaa")

    assert "Host\tsvu-new" in c.config()
    assert "ForwardAgent\tyes" in c.config()
    assert "unknownpropertylikethis\tnoway" in c.config()
    assert "HostName\tssh.svuni.local" in c.config()

    assert "forwardagent" in c.host("svu-new")
    assert "unknownpropertylikethis" in c.host("svu-new")
    assert "hostname" in c.host("svu-new")
    assert "user" in c.host("svu-new")

def test_remove():

    def lines(fn):
        with open(fn, "r") as f:
            return len(f.read().splitlines())

    import tempfile
    tc = os.path.join(tempfile.gettempdir(), "temp_ssh_config-123")
    try:
        c = sshconf.read_ssh_config(test_config)

        assert 14 == lines(test_config)

        c.remove("svu")
        c.write(tc)

        assert 9 == lines(tc)
        assert "# within-host-comment" not in c.config()

    finally:
        os.remove(tc)

def test_read_duplicate_keys():

    c = sshconf.read_ssh_config(test_config2)

    host = c.host('foo')
    assert 5 == len(host.keys())
    assert "localforward" in host
    assert 2 == len(host["localforward"])

def test_set_duplicate_keys():

    c = sshconf.read_ssh_config(test_config2)

    lfs = c.host('foo')['localforward']

    assert type(lfs) is list
    assert len(lfs) == 2
    lfs.append("1234 localhost:4321")

    c.set('foo', localforward=lfs)

    import tempfile
    tc = os.path.join(tempfile.gettempdir(), "temp_ssh_config-tudk")
    try:
        c.write(tc)

        d = sshconf.read_ssh_config(tc)

        host2 = d.host('foo')
        assert len(host2["localforward"]) == 3
    finally:
        os.remove(tc)

def test_mapping_remove_existing_key():
    c = sshconf.read_ssh_config(test_config)

    svu = c.host('svu')
    print(svu)
    c.unset("svu", 'proxycommand')

    print(c.config())
    assert "ProxyCommand" not in c.config()
    svu2 = c.host('svu')
    assert 'proxycommand' not in svu2
    assert 'hostname' in svu2
    assert 'port' in svu2
