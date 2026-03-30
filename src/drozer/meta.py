from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import json
import drozer

class Version:

    def __init__(self, version):
        major, minor, patch = version.split(".")

        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)

    def __eq__(self, other):
        return self.major == other.major and self.minor == other.minor and self.patch == other.patch

    def __gt__(self, other):
        return self.major > other.major or \
            self.major == other.major and self.minor > other.minor or \
            self.major == other.major and self.minor == other.minor and self.patch > other.patch

    def __lt__(self, other):
        return self.major < other.major or \
            self.major == other.major and self.minor < other.minor or \
            self.major == other.major and self.minor == other.minor and self.patch < other.patch

    def __str__(self):
        return "%d.%d.%d" % (self.major, self.minor, self.patch)

version = Version(drozer.__version__)

def latest_version():
    try:
        response = urlopen(Request("https://api.github.com/repos/ReversecLabs/drozer/releases/latest", None, {"user-agent": "drozer: %s" % str(version)}), None, 1)
        latestTag = json.load(response)
        latestVersion = Version(latestTag["tag_name"]), latestTag["created_at"][:10]
        return latestVersion
    except HTTPError:
        return None
    except URLError:
        return None
        
def latest_agent_version():
    try:
        response = urlopen(Request("https://api.github.com/repos/ReversecLabs/drozer-agent/releases/latest", None, {"user-agent": "drozer: %s" % str(version)}), None, 1)
        latestTag = json.load(response)
        latestAgentVersion = Version(latestTag["tag_name"]), latestTag["created_at"][:10]
        return latestAgentVersion
    except HTTPError:
        return None
    except URLError:
        return None


def print_version():
    print("%s %s\n" % ("drozer", version))
