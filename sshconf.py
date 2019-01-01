
import re
from collections import defaultdict, namedtuple

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

known_params = [x.lower() for x in KNOWN_PARAMS]  # pylint: disable=invalid-name

class ConfigLine:  # pylint: disable=too-few-public-methods
    """ Holds configuration for a line in ssh config """
    def __init__(self, line, host=None, key=None, value=None):
        self.line = line
        self.host = host
        self.key = key
        self.value = value

def read_ssh_config(path):
    """
    Read ssh config file and return parsed SshConfig
    """
    with open(path, "r") as fh_:
        lines = fh_.read().splitlines()
    return SshConfig(lines)

def empty_ssh_config():
    """
    Creates a new empty ssh configuration.
    """
    return SshConfig([])

def _key_value(line):
    no_comment = line.split("#")[0]
    return [x.strip() for x in re.split(r"\s+", no_comment.strip(), 1)]

def _remap_key(key):
    """ Change key into correct casing if we know the parameter """
    if key in KNOWN_PARAMS:
        return key
    if key.lower() in known_params:
        return KNOWN_PARAMS[known_params.index(key.lower())]
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
        """Parse lines from ssh config file"""
        cur_entry = None
        for line in lines:
            kv_ = _key_value(line)
            if len(kv_) > 1:
                key, value = kv_
                if key.lower() == "host":
                    cur_entry = value
                    self.hosts_.add(value)
                self.lines_.append(ConfigLine(line=line, host=cur_entry, key=key, value=value))
            else:
                self.lines_.append(ConfigLine(line=line))

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
            vals = defaultdict(list)
            for k, value in [(x.key.lower(), x.value) for x in self.lines_
                             if x.host == host and x.key.lower() != "host"]:
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

        def update_line(key, value):
            """Produce new config line"""
            return "  %s %s" % (key, value)

        for key, values in kwargs.items():
            if type(values) not in [list, tuple]:  # pylint: disable=unidiomatic-typecheck
                values = [values]

            lower_key = key.lower()
            update_idx = [idx for idx, x in enumerate(self.lines_)
                          if x.host == host and x.key.lower() == lower_key]
            extra_remove = []
            for idx in update_idx:
                if values:  # values available, update the line
                    value = values.pop()
                    self.lines_[idx].line = update_line(self.lines_[idx].key, value)
                    self.lines_[idx].value = value
                else:                # no more values available, remove the line
                    extra_remove.append(idx)

            for idx in reversed(sorted(extra_remove)):
                del self.lines_[idx]

            if values:
                mapped_key = _remap_key(key)
                max_idx = max([idx for idx, line in enumerate(self.lines_) if line.host == host])
                for value in values:
                    self.lines_.insert(max_idx + 1, ConfigLine(line=update_line(mapped_key, value),
                                                               host=host, key=mapped_key,
                                                               value=value))

    def unset(self, host, *args):
        """
        Removes settings for a host.

        Parameters
        ----------
        host : the host to remove settings from.
        *args : list of settings to removes.
        """
        self.__check_host_args(host, args)
        remove_idx = [idx for idx, x in enumerate(self.lines_)
                      if x.host == host and x.key.lower() in args]
        for idx in reversed(sorted(remove_idx)):
            del self.lines_[idx]

    def __check_host_args(self, host, keys):
        """Checks parameters"""
        if host not in self.hosts_:
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
        if new_host in self.hosts_:
            raise ValueError("Host %s: already exists." % new_host)
        for line in self.lines_:  # update lines
            if line.host == old_host:
                line.host = new_host
                if line.key.lower() == "host":
                    line.value = new_host
                    line.line = "Host %s" % new_host
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
        self.lines_.append(ConfigLine(line="", host=None))
        self.lines_.append(ConfigLine(line="Host %s" % host, host=host, key="Host", value=host))
        for k, v in kwargs.items():
            if type(v) not in [list, tuple]:
                v = [v]
            mapped_k = _remap_key(k)
            for value in v:
                self.lines_.append(ConfigLine(line="  %s %s" % (mapped_k, str(value)), host=host, key=mapped_k, value=value))
        self.lines_.append(ConfigLine(line="", host=None))

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
        host_lines = [ idx for idx, x in enumerate(self.lines_) if x.host == host ]
        remove_range = reversed(range(min(host_lines), max(host_lines) + 1))
        for idx in remove_range:
            del self.lines_[idx]

    def config(self):
        """
        Return the configuration as a string.
        """
        return "\n".join([x.line for x in self.lines_])

    def write(self, path):
        """
        Writes ssh config file

        Parameters
        ----------
        path : The file to write to
        """
        with open(path, "w") as fh_:
            fh_.write(self.config())
