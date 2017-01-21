
import re

def read_ssh_config(path):
    """
    Read ssh config file and return parsed SshConfig
    """
    with open(path, "r") as f:
        lines = f.read().splitlines()
    return SshConfig(lines)

def empty_ssh_config():
    """
    Creates a new empty ssh configuration.
    """
    return SshConfig([])

def _key_value(line):
    no_comment = line.split("#")[0]
    return [ x.strip() for x in re.split(r"\s+", no_comment.strip(), 1) ]

class SshConfig(object):
    """
    Class for manipulating SSH configuration.
    """
    def __init__(self, lines):
        self.lines_ = []
        self.hosts_ = set()
        self.parse(lines)

    def parse(self, lines):
        cur_entry = None
        for line in lines:
            kv = _key_value(line)
            if len(kv) > 1:
                k, v = kv
                if k == "Host":
                    cur_entry = v
                    self.hosts_.add(v)
                self.lines_.append(dict(line=line, host=cur_entry, key=k, value=v))
            else:
                self.lines_.append(dict(line=line, host=None))

    def hosts(self):
        """
        Return the hosts found in the configuration.

        Returns
        -------
        Tuple of Host entries (including "*" if found)
        """
        return tuple(self.hosts_)

    def host(self, host):
        """
        Return the configuration of a specific host as a dictionary.

        Parameters
        ----------
        host : the host to return values for.

        Returns
        -------
        dict of key value pairs, excluding "Host"
        """
        if host in self.hosts_:
            return { k: v for k, v in [ (x["key"], x["value"]) for x in self.lines_
                                        if x["host"] == host and x["key"] != "Host" ]}
        else:
            return {}

    def update(self, host, **kwargs):
        """
        Update configuration for an existing host. Note, you can update the "Host" value, but
        it will still be referred to by the old "Host" value.

        Parameters
        ----------
        host : the Host to modify.
        **kwargs : The new configuration parameters
        """
        if host not in self.hosts_:
            raise ValueError("Host %s: not found." % host)

        if "Host" in kwargs:
            raise ValueError("Cannot modify Host value with update, use rename.")

        def update_line(k, v):
            return "\t%s\t%s" % (k, v)

        for key, value in kwargs.items():
            found = False
            for line in self.lines_:
                if line["host"] == host and line["key"] == key:
                    line["value"] = value
                    line["line"] = update_line(key, value)
                    found = True

            if not found:
                max_idx = max([ idx for idx, line in enumerate(self.lines_) if line["host"] == host ])
                self.lines_.insert(max_idx + 1, dict(line=update_line(key, value),
                                                     host=host, key=key, value=value))

    def rename(self, old_host, new_host):
        """
        Renames a host configuration.

        Parameters
        ----------
        old_host : the host to rename.
        new_host : the new host value
        """
        if new_host in self.hosts_:
            raise ValueError("Host %s: already exists." % new_host)
        for line in self.lines_:  # update lines
            if line["host"] == old_host:
                line["host"] = new_host
                if line["key"] == "Host":
                    line["value"] = new_host
                    line["line"] = "Host\t%s" % new_host
        self.hosts_.remove(old_host)  # update host cache
        self.hosts_.add(new_host)

    def add(self, host, **kwargs):
        """
        Add another host to the SSH configuration.

        Parameters
        ----------
        host: The Host entry to add.
        **kwargs: The parameters for the host (without "Host" parameter itself)
        """
        if host in self.hosts_:
            raise ValueError("Host %s: exists (use update)." % host)
        self.hosts_.add(host)
        self.lines_.append(dict(line="", host=None))
        self.lines_.append(dict(line="Host\t%s" % host, host=host, key="Host", value=host))
        for k, v in kwargs.items():
            self.lines_.append(dict(line="\t%s\t%s" % (k, str(v)), host=host, key=k, value=v))
        self.lines_.append(dict(line="", host=None))

    def config(self):
        """
        Return the configuration as a string.
        """
        return "\n".join([ x["line"] for x in self.lines_ ])

    def write(self, path):
        """
        Writes ssh config file

        Parameters
        ----------
        path : The file to write to
        """
        with open(path, "w") as f:
            f.write(self.config())
