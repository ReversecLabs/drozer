import os

from drozer.modules.common import file_system, shell

class ToyBox(shell.Shell):
    """
    Utility methods for installing and using toybox on the Agent.
    """

    def toyboxPath(self):
        """
        Get the path to which Toybox is installed on the Agent.
        """

        return self.workingDir() + "/bin/toybox"

    def _localPath(self,arch):
        """
        Get the path to the toybox binary on the local system.
        """
        if arch == "armeabi":
            return os.path.join(os.path.dirname(__file__), "..", "tools", "setup","arm", "toybox")
        elif arch == "arm64":
            return os.path.join(os.path.dirname(__file__), "..", "tools", "setup","arm64", "toybox")
        elif arch == "x86":
            return os.path.join(os.path.dirname(__file__), "..", "tools", "setup","x86", "toybox")
        elif arch == "x86_64":
            return os.path.join(os.path.dirname(__file__), "..", "tools", "setup","x86_64", "toybox")
        else:
            return None

    def toyBoxExec(self, command):
        """
        Execute a command using Toybox.
        """

        return self.shellExec("%s %s" % (self.toyboxPath(), command))

    def isToyBoxInstalled(self):
        """
        Test whether Toybox is installed on the Agent.
        """

        return self.exists(self.toyboxPath())

    def installToyBox(self,arch):
        """
        Install Toybox on the Agent.
        """

        if self.ensureDirectory(self.toyboxPath()[0:self.toyboxPath().rindex("/")]):

            bytes_copied = self.uploadFile(self._localPath(arch), self.toyboxPath())
    
            if bytes_copied != os.path.getsize(self._localPath(arch)):
                return False
            else:
                self.shellExec("chmod 775 " + self.toyboxPath())
                
                return True
        else:
            return False
