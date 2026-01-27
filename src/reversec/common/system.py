import os
import platform

from WithSecure.common.stream import DecolouredStream


def which(executable):
    """
    Implementation of the *nix `which` command, to find an executable on the
    current PATH.

    Update: added support for Windows hosts
    """
    if platform.system() == 'Windows':
        executable = executable + ".exe"

    for path in os.getenv("PATH", "").split(os.pathsep):
        trial = os.path.join(path, executable)

        if os.path.isfile(trial) and os.access(trial, os.X_OK):
            return trial


class Tee(object):
    """
    Implementation of the *nix Tee command, to direct an output stream at both
    the console and a file.

    Original Version by Luander <luander.r@samsung.com>
    """

    def __init__(self, console, name, mode='w'):
        self.console = console
        self.file = DecolouredStream(open(name, mode))

    def __del__(self):
        if hasattr(self, 'file') and self.file != None:
            self.file.close()

    def write(self, data):
        """
        Wrapper around the #write command of the stream, that writes the stream
        to both the console and file, before flushing the filestream.
        """

        self.console.write(data)
        self.file.write(data)
        self.file.flush()
