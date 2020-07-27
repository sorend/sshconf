
import os
import re
import glob
from collections import defaultdict, namedtuple, Counter

# taken from "man ssh"
KNOWN_PARAMS = (
    "AddKeysToAgent",
    "AddressFamily",
    "BatchMode",
    "BindAddress",
    "CanonicalDomains",
    "CanonicalizeFallbackLocal",
    "CanonicalizeHostname",
    "CanonicalizeMaxDots",
    "CanonicalizePermittedCNAMEs",
    "CertificateFile",
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
    "ControlPersist",
    "DynamicForward",
    "EscapeChar",
    "ExitOnForwardFailure",
    "FingerprintHash",
    "ForwardAgent",
    "ForwardX11",
    "ForwardX11Timeout",
    "ForwardX11Trusted",
    "GatewayPorts",
    "GlobalKnownHostsFile",
    "GSSAPIAuthentication",
    "GSSAPIKeyExchange",
    "GSSAPIClientIdentity",
    "GSSAPIDelegateCredentials",
    "GSSAPIRenewalForcesRekey",
    "GSSAPITrustDns",
    "GSSAPIKexAlgorithms",
    "HashKnownHosts",
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

DEFAULT_INDENT = '  '

known_params = [x.lower() for x in KNOWN_PARAMS]  # pylint: disable=invalid-name

class ConfigLine:  # pylint: disable=too-few-public-methods
    """ Holds configuration for a line in ssh config """
    def __init__(self, path, line, key=None, value=None, ref=None):
        self.path = path
        self.line = line
        self.key = key
        self.value = value
        self.ref = ref
        # derivatives
        self.lower_key = key.lower() if key is not None else None

    def is_host(self, host):
        return isinstance(self.ref, Host) and self.ref.name == host

    def __repr__(self):
        return "path=%s, ref=%s, key=%s, value=%s | %s" % (self.path, self.ref, self.key, self.value, self.line)

class Host:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name

class Match:
    def __init__(self, name):
        self.name = name

def _read_lines(path):
    with open(path, "r") as fh:
        return fh.read().splitlines()

def _line_split_key_value(line):
    upto_comment = line.split("#")[0]
    kv = [x.strip() for x in re.split(r"\s+", upto_comment.strip(), 1)]
    return kv if len(kv) == 2 else None

def _parse_configline(path, cur_entry, line, level0=True):
    kv = _line_split_key_value(line)
    if kv is None:
        return cur_entry, ConfigLine(path=path, line=line, ref=cur_entry)
    else:
        key, value = kv
        if level0 and key.lower() == "host":
            cur_entry = Host(value)
        elif level0 and key.lower() == "match":
            cur_entry = Match(value)
        return cur_entry, ConfigLine(path=path, line=line, key=key, value=value, ref=cur_entry)

def _parse_with_includes(parsed_lines, cur_entry, base_path, path, level0):
    """Parse lines from ssh config file"""
    for line in _read_lines(path):
        cur_entry, cl = _parse_configline(path, cur_entry, line, level0)
        parsed_lines.append(cl)
        if cl.lower_key == "include":
            include_paths = _resolve_includes(base_path, cl.value)
            for include_path in include_paths:
                _parse_with_includes(parsed_lines, cur_entry, base_path, include_path, cur_entry is None)

def read_ssh_config(path):
    base_path = os.path.dirname(path)
    parsed_lines = []
    _parse_with_includes(parsed_lines, None, base_path, path, True)

    # use most popular indent as indent for file, default '  '
    indents = [ _line_indent(x.line) for x in parsed_lines
                if x.ref is not None and x.lower_key is not None and x.lower_key not in ["host", "match"] ]
    counter = Counter(indents)
    popular = list(reversed(sorted(counter.items(), key=lambda e: e[1])))
    indent = popular[0][0] if len(popular) > 0 else DEFAULT_INDENT

    # initialize hosts
    hosts = set([ x.ref.name for x in parsed_lines if isinstance(x.ref, Host) ])

    return SshConfig(path, parsed_lines, indent)

def empty_ssh_config_file():
    """
    Creates a new empty ssh configuration.
    """
    return SshConfig(None, [], DEFAULT_INDENT)

def _remap_key(key):
    """ Change key into correct casing if we know the parameter """
    if key in KNOWN_PARAMS:
        return key
    if key.lower() in known_params:
        return KNOWN_PARAMS[known_params.index(key.lower())]
    return key

def _line_indent(s):
    return s[0: len(s) - len(s.lstrip())]

class SshConfig(object):
    """
    Class for manipulating SSH configuration.
    """
    def __init__(self, root_path, parsed_lines, indent):
        self.root_path_ = root_path
        self.lines_ = parsed_lines
        self.indent_ = indent

    def hosts(self):
        """
        Return the hosts found in the configuration.

        Returns
        -------
        Tuple of Host entries (including "*" if found)
        """
        return tuple(set([ x.ref.name for x in self.lines_ if isinstance(x.ref, Host)]))

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
        if host in self.hosts():
            vals = defaultdict(list)
            for k, value in [(x.lower_key, x.value) for x in self.lines_ if x.is_host(host) and x.key is not None and x.lower_key != "host"  ]:
                vals[k].append(value)
            flatten = lambda x: x[0] if len(x) == 1 else x
            return {k: flatten(v) for k, v in vals.items()}
        return {}

    def set(self, host, **kwargs):
        """
        Set configuration values for an existing host.
        Overwrites values for existing settings, or adds new settings.

        Parameters
        ----------
        host : the Host to modify.
        **kwargs : The new configuration parameters
        """
        self.__check_host_args(host, kwargs)

        for key, values in kwargs.items():
            if type(values) not in [list, tuple]:  # pylint: disable=unidiomatic-typecheck
                values = [values]

            lower_key = key.lower()
            update_idx = [idx for idx, x in enumerate(self.lines_)
                          if x.is_host(host) and x.lower_key == lower_key]
            extra_remove = []
            for idx in update_idx:
                if values:  # values available, update the line
                    value = values.pop()
                    self.lines_[idx].line = self._new_line(self.lines_[idx].key, value)
                    self.lines_[idx].value = value
                else:                # no more values available, remove the line
                    extra_remove.append(idx)

            for idx in reversed(sorted(extra_remove)):
                del self.lines_[idx]

            if values:
                mapped_key = _remap_key(key)
                insert_idx = min([ idx for idx, line in enumerate(self.lines_) if line.is_host(host) and line.lower_key == "host" ])
                insert_line = self.lines_[insert_idx]
                for value in values:
                    self.lines_.insert(insert_idx + 1, ConfigLine(path=insert_line.path,
                                                                  line=self._new_line(mapped_key, value),
                                                                  ref=Host(host),
                                                                  key=mapped_key,
                                                                  value=value))

    def unset(self, host, *args):
        """
        Removes settings for a host.

        Parameters
        ----------
        host : the host to remove settings from.
        *args : list of settings to removes.
        """
        args = [ x.lower() for x in args ]
        self.__check_host_args(host, args)
        remove_idx = [idx for idx, x in enumerate(self.lines_)
                      if x.is_host(host) and x.lower_key in args]
        for idx in reversed(sorted(remove_idx)):
            del self.lines_[idx]

    def __check_host_args(self, host, keys):
        """Checks parameters"""
        if host not in self.hosts():
            raise ValueError("Host %s: not found" % host)
        if "host" in [x.lower() for x in keys]:
            raise ValueError("Cannot modify Host value")

    def rename(self, old_host, new_host):
        """
        Renames a host configuration.

        Parameters
        ----------
        old_host : the host to rename.
        new_host : the new host value
        """
        if new_host in self.hosts():
            raise ValueError("Host %s: already exists." % new_host)
        new_host_ref = Host(new_host)
        for line in self.lines_:  # update lines
            if line.is_host(old_host):
                line.ref = new_host_ref
                if line.lower_key == "host":
                    line.value = new_host
                    line.line = "Host %s" % new_host

    def add(self, host, **kwargs):
        """
        Add another host to the SSH configuration.

        Parameters
        ----------
        host: The Host entry to add.
        **kwargs: The parameters for the host (without "Host" parameter itself)
        """
        if host in self.hosts():
            raise ValueError("Host %s: exists (use update)." % host)
        new_host_ref = Host(host)
        self.lines_.append(ConfigLine(path=self.root_path_, line="", ref=new_host_ref))
        self.lines_.append(ConfigLine(path=self.root_path_, line="Host %s" % host, ref=new_host_ref, key="Host", value=host))
        for k, v in kwargs.items():
            if type(v) not in [list, tuple]:
                v = [v]
            mapped_k = _remap_key(k)
            for value in v:
                new_line = self._new_line(mapped_k, value)
                self.lines_.append(ConfigLine(path=self.root_path_, line=new_line, ref=new_host_ref, key=mapped_k, value=value))
        self.lines_.append(ConfigLine(path=self.root_path_, line="", ref=new_host_ref))

    def remove(self, host):
        """
        Removes a host from the SSH configuration.

        Parameters
        ----------
        host : The host to remove
        """
        if host not in self.hosts():
            raise ValueError("Host %s: not found." % host)
        # remove lines, including comments inside the host lines
        host_lines = [ idx for idx, x in enumerate(self.lines_) if x.is_host(host) and x.key is not None ]
        remove_range = reversed(range(min(host_lines), max(host_lines) + 1))
        for idx in remove_range:
            del self.lines_[idx]

    def config(self, filter_includes=False):
        """
        Return the configuration as a string.
        """
        def the_filter(k):
            if filter_includes and k is not None and k == "include":
                return False
            else:
                return True
            
        return "\n".join([x.line for x in self.lines_ if the_filter(x.key)])

    def write(self, path):
        """
        Writes ssh config file

        Parameters
        ----------
        path : The file to write to
        """
        with open(path, "w") as fh_:
            fh_.write(self.config())


    def _new_line(self, key, value):
        return "%s%s %s" % (self.indent_, key, str(value))


def _resolve_includes(base_path, path):
    search_path = os.path.join(base_path, os.path.expanduser(path))
    return glob.glob(search_path)
