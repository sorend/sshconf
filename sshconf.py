
import re

# taken from "man ssh"
KNOWN_PARAMS = (
    "AddressFamily",
    "BatchMode",
    "BindAddress",
    "ChallengeResponseAuthentication",
    "CheckHostIP",
    "Cipher",
    "Ciphers",
    "ClearAllForwardings",
    "Compression",
    "CompressionLevel",
    "ConnectionAttempts",
    "ConnectTimeout",
    "ControlMaster",
    "ControlPath",
    "DynamicForward",
    "EscapeChar",
    "ForwardAgent",
    "ForwardX11",
    "ForwardX11Trusted",
    "GatewayPorts",
    "GlobalKnownHostsFile",
    "GSSAPIAuthentication",
    "GSSAPIDelegateCredentials",
    "HashKnownHosts",
    "Host",
    "HostbasedAuthentication",
    "HostKeyAlgorithms",
    "HostKeyAlias",
    "HostName",
    "IdentityFile",
    "IdentitiesOnly",
    "KbdInteractiveDevices",
    "LocalForward",
    "LogLevel",
    "MACs",
    "NoHostAuthenticationForLocalhost",
    "NumberOfPasswordPrompts",
    "PasswordAuthentication",
    "Port",
    "PreferredAuthentications",
    "Protocol",
    "ProxyCommand",
    "PubkeyAuthentication",
    "RemoteForward",
    "RhostsRSAAuthentication",
    "RSAAuthentication",
    "SendEnv",
    "ServerAliveInterval",
    "ServerAliveCountMax",
    "SmartcardDevice",
    "StrictHostKeyChecking",
    "TCPKeepAlive",
    "UsePrivilegedPort",
    "User",
    "UserKnownHostsFile",
    "VerifyHostKeyDNS",
    "XAuthLocation",
    "Host",
    "HostbasedAuthentication",
    "HostbasedKeyTypes",
    "HostKeyAlgorithms",
    "HostKeyAlias",
    "HostName",
    "IdentitiesOnly",
    "IdentityAgent",
    "IdentityFile",
    "Include",
    "IPQoS",
    "KbdInteractiveAuthentication",
    "KbdInteractiveDevices",
    "KexAlgorithms",
    "LocalCommand",
    "LocalForward",
    "LogLevel",
    "MACs",
    "Match",
    "NoHostAuthenticationForLocalhost",
    "NumberOfPasswordPrompts",
    "PasswordAuthentication",
    "PermitLocalCommand",
    "PKCS11Provider",
    "Port",
    "PreferredAuthentications",
    "Protocol",
    "ProxyCommand",
    "ProxyJump",
    "ProxyUseFdpass",
    "PubkeyAcceptedKeyTypes",
    "PubkeyAuthentication",
    "RekeyLimit",
    "RemoteForward",
    "RequestTTY",
    "RhostsRSAAuthentication",
    "RSAAuthentication",
    "SendEnv",
    "ServerAliveInterval",
    "ServerAliveCountMax",
    "StreamLocalBindMask",
    "StreamLocalBindUnlink",
    "StrictHostKeyChecking",
    "TCPKeepAlive",
    "Tunnel",
    "TunnelDevice",
    "UpdateHostKeys",
    "UsePrivilegedPort",
    "User",
    "UserKnownHostsFile",
    "VerifyHostKeyDNS",
    "VisualHostKey",
    "XAuthLocation"
)

known_params = [ x.lower() for x in KNOWN_PARAMS ]

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

def _remap_key(key):
    """ Change key into correct casing if we know the parameter """
    if key in KNOWN_PARAMS:
        return key
    else:
        if key.lower() in known_params:
            return KNOWN_PARAMS[known_params.index(key.lower())]
        else:
            return key

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
                if k.lower() == "host":
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

        Dictionary always contains lowercase versions of the attribute names.

        Parameters
        ----------
        host : the host to return values for.

        Returns
        -------
        dict of key value pairs, excluding "Host", empty map if host is not found.
        """
        if host in self.hosts_:
            return { k: v for k, v in [ (x["key"].lower(), x["value"]) for x in self.lines_
                                        if x["host"] == host and x["key"].lower() != "host" ]}
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

        if "host" in map(lambda x: x.lower(), kwargs.keys()):
            raise ValueError("Cannot modify Host value with update, use rename.")

        def update_line(k, v):
            return "\t%s\t%s" % (k, v)

        for key, value in kwargs.items():
            found = False
            lower_key = key.lower()
            for line in self.lines_:
                if line["host"] == host and line["key"].lower() == lower_key:
                    line["value"] = value
                    line["line"] = update_line(line["key"], value)
                    found = True

            if not found:
                mapped_key = _remap_key(key)
                max_idx = max([ idx for idx, line in enumerate(self.lines_) if line["host"] == host ])
                self.lines_.insert(max_idx + 1, dict(line=update_line(mapped_key, value),
                                                     host=host, key=mapped_key, value=value))

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
                if line["key"].lower() == "host":
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
            mapped_k = _remap_key(k)
            self.lines_.append(dict(line="\t%s\t%s" % (mapped_k, str(v)), host=host, key=mapped_k, value=v))
        self.lines_.append(dict(line="", host=None))

    def remove(self, host):
        """
        Removes a host from the SSH configuration.

        Parameters
        ----------
        host : The host to remove
        """
        if host not in self.hosts_:
            raise ValueError("Host %s: not found." % host)
        self.hosts_.remove(host)
        # remove lines, including comments inside the host lines
        host_lines = [ idx for idx, x in enumerate(self.lines_) if x["host"] == host ]
        remove_range = reversed(range(min(host_lines), max(host_lines) + 1))
        for idx in remove_range:
            del self.lines_[idx]

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
