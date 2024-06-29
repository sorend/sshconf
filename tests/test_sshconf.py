import sshconf
import pytest
import os

test_config = os.path.join(os.path.dirname(__file__), "test_config")
test_config2 = os.path.join(os.path.dirname(__file__), "test_config2")
test_config_include_specific = os.path.join(os.path.dirname(__file__), "test_config_include_specific")


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

    assert "  Compression no" in c.config()
    assert "  Port 2222" in c.config()


def test_set_host_failed():
    c = sshconf.read_ssh_config(test_config)

    with pytest.raises(ValueError):
        c.set("svu", Host="svu-new")


def test_rename():

    c = sshconf.read_ssh_config(test_config)

    assert c.host("svu")["hostname"] == "www.svuniversity.ac.in"

    hosts = c.hosts()

    c.rename("svu", "svu-new")

    hosts2 = c.hosts()

    assert hosts.index("svu") == hosts2.index("svu-new")  # order is the same

    assert "Host svu-new" in c.config()
    assert "Host svu\n" not in c.config()
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

    hosts = list(c.hosts())

    c.add("venkateswara", Hostname="venkateswara.onion", User="other", Port=22,
          ProxyCommand="nc -w 300 -x localhost:9050 %h %p")

    hosts2 = list(c.hosts())

    assert hosts + ["venkateswara"] == hosts2

    assert "venkateswara" in c.hosts()
    assert c.host("venkateswara")["proxycommand"] == "nc -w 300 -x localhost:9050 %h %p"

    assert "Host venkateswara" in c.config()

    with pytest.raises(ValueError):
        c.add("svu")

    with pytest.raises(ValueError):
        c.add("venkateswara")


def test_add_before_host():

    c = sshconf.read_ssh_config(test_config)

    hosts = list(c.hosts())

    c.add("venkateswara", before_host="svu", Hostname="venkateswara.onion", User="other", Port=22,
          ProxyCommand="nc -w 300 -x localhost:9050 %h %p")

    hosts2 = list(c.hosts())

    c.add("venkateswara2", before_host="*", Hostname="venkateswara.onion", User="other", Port=22,
          ProxyCommand="nc -w 300 -x localhost:9050 %h %p")

    hosts3 = list(c.hosts())

    new_config = c.config()

    print("new config", new_config)

    assert hosts == ["*", "svu"]
    assert hosts2 == ["*", "venkateswara", "svu"]
    assert hosts3 == ["venkateswara2", "*", "venkateswara", "svu"]

    assert "venkateswara" in c.hosts()

    assert "Host venkateswara" in new_config

    with pytest.raises(ValueError):  # cant add before a host that is not found
        c.add("svucs", before_host="not-found-host", Hostname="venkateswara.onion", User="other", Port=22,
              ProxyCommand="nc -w 300 -x localhost:9050 %h %p")

    with pytest.raises(ValueError):  # its there now
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
        c = sshconf.empty_ssh_config_file()
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

    assert "Hostname ssh.svuniversity.ac.in" in c.config()
    assert "User mca" in c.config()
    assert "ProxyCommand nc --help" in c.config()


def test_mapping_set_existing_key_multi_values():
    c = sshconf.read_ssh_config(test_config)
    c.set("svu", Hostname="ssh.svuniversity.ac.in", User="mca",
          remoteforward=["localhost:3322 localhost:22",
                         "localhost:10809 172.26.176.1:10809"])
    print(c.config())

    assert "Hostname ssh.svuniversity.ac.in" in c.config()
    assert "User mca" in c.config()
    assert "RemoteForward localhost:3322 localhost:22" in c.config()
    assert "RemoteForward localhost:10809 172.26.176.1:10809" in c.config()


def test_mapping_set_new_key():
    c = sshconf.read_ssh_config(test_config)

    c.set("svu", forwardAgent='yes', unknownpropertylikethis='noway')

    assert "Hostname   www.svuniversity.ac.in" in c.config()  # old parameters
    assert "Port       22" in c.config()
    assert "ForwardAgent yes" in c.config()  # new parameter has been properly cased
    assert "unknownpropertylikethis noway" in c.config()


def test_mapping_add_new_keys():
    c = sshconf.read_ssh_config(test_config)
    c.add("svu-new", forwardAgent="yes", unknownpropertylikethis="noway", Hostname="ssh.svuni.local",
          user="mmccaa")

    assert "Host svu-new" in c.config()
    assert "ForwardAgent yes" in c.config()
    assert "unknownpropertylikethis noway" in c.config()
    assert "HostName ssh.svuni.local" in c.config()

    assert "forwardagent" in c.host("svu-new")
    assert "unknownpropertylikethis" in c.host("svu-new")
    assert "hostname" in c.host("svu-new")
    assert "user" in c.host("svu-new")


def test_remove():
    c = sshconf.read_ssh_config(test_config)

    c.add("abc", forwardAgent="yes", unknownpropertylikethis="noway", Hostname="ssh.svuni.local",
          user="mmccaa")

    c.add("def", forwardAgent="yes", unknownpropertylikethis="noway", Hostname="ssh.svuni.local",
          user="mmccaa")

    config1 = c.config()
    hosts = list(c.hosts())
    c.remove("abc")
    config2 = c.config()
    hosts2 = list(c.hosts())
    c.remove("svu")
    config3 = c.config()
    hosts3 = list(c.hosts())

    assert "abc" in hosts
    assert "abc" not in hosts2

    assert "Host abc" in config1
    assert "Host abc" not in config2
    assert "Host svu" not in config3

    assert hosts2 == ["*", "svu", "def"]  # test order
    assert hosts3 == ["*", "def"]

    assert "# within-host-comment" not in config3


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


def test_read_included_specific():
    c = sshconf.read_ssh_config(test_config_include_specific)

    hosts = c.hosts()
    print("hosts", hosts)

    assert 'svuincluded' in hosts

    h = c.host("svuincluded")
    print(h)
    print(c.config())


def test_save_with_included(tmpdir):
    conf = tmpdir.join("config")
    incl = tmpdir.join("included_host")

    conf.write("""
Host svu.local
    Hostname ssh.svu.local
    User something

Include included_host
    """)

    incl.write("""
Host svu.included
    Hostname ssh.svu.included
    User whatever
    """)

    c = sshconf.read_ssh_config(conf)

    hosts = c.hosts()
    print("hosts", hosts)

    assert 'svu.local' in hosts
    assert 'svu.included' in hosts

    h = c.host("svu.included")
    print(h)

    c.set("svu.included", Hostname="ssh2.svu.included", Port="1234")
    h = c.host("svu.included")
    print(h)
    print(c.config())

    c.save()
    assert "ssh2.svu.included" not in conf.read()
    assert "ssh2.svu.included" in incl.read()


def test_read_included_glob(tmpdir):
    conf = tmpdir.join("config")
    incl = tmpdir.mkdir("conf.d").join("included_host")

    conf.write("""
Host svu.local
    Hostname ssh.svu.local
    User something

Include conf.d/*
    """)

    incl.write("""
Host svu.included
    Hostname ssh.svu.included
    User whatever
    """)

    c = sshconf.read_ssh_config(conf)

    hosts = c.hosts()
    print("hosts", hosts)

    assert 'svu.local' in hosts
    assert 'svu.included' in hosts
