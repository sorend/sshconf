#!/usr/bin/env python3

import versiontag

version = versiontag.get_version(pypi=True).strip()

with open("sshconf.py", "r") as f:
    text = f.read()

text = text.replace("0.0.dev0", version)

with open("sshconf.py", "w") as f:
    f.write(text)
