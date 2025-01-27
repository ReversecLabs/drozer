from drozer.modules import common, Module

class ReadableFiles(Module, common.BusyBox, common.Shell, common.SuperUser):

    name = "Find world-readable files in the given folder"
    description = "Find world-readable files in the given folder"
    examples = """dz> run scanner.misc.readablefiles /data -p
Discovered world-readable files in /data:
  /data/system/packages-stopped.xml
  /data/system/packages.list
  /data/system/packages.xml
  /data/system/uiderrors.txt
  ...<snipped>...
"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2013-04-18"
    license = "BSD (3 clause)"
    path = ["scanner", "misc"]
    
    def add_arguments(self, parser):
        parser.add_argument("target", help="the target directory to search")
        parser.add_argument("-p", "--privileged", action="store_true", default=False, help="request root to perform the task in a privileged context")

    def execute(self, arguments):
        if self.isFindInstalled():
            command = "find %s \( -type b -o -type c -o -type f -o -type s \) -perm -o=r \-exec ls {} \;" % arguments.target
        else:
            if (self.isBusyBoxInstalled() == True):
                command = self.busyboxPath() + " find %s\( -type b -o -type c -o -type f -o -type s \) -perm -o=r \-exec ls {} \;" % arguments.target
            else:
                self.stderr.write("Since the Agent does not have a find binary, this command requires BusyBox to complete. Run tools.setup.busybox and then retry.\n")
                return

        privileged = arguments.privileged
        if privileged:
            if self.isAnySuInstalled():
                command = self.suPath() + " -c \"%s\"" % command
            else:
                self.stdout.write("su is not installed...reverting back to unprivileged mode\n")
                privileged = False
                    
        files = self.shellExec(command)
        readable_files = []

        for f in iter(files.split("\n")):
            if not f.startswith('find: ') and len(f.strip()) > 0:
                readable_files.append(f)

        if len(readable_files) > 0:
            self.stdout.write("Discovered world-readable files in %s:\n" % arguments.target)
            for f in readable_files:
                self.stdout.write("  %s\n" % f)
        else:
            if privileged:
                self.stdout.write("No world-readable files found in %s\n" % arguments.target)
            else:
                self.stdout.write("No world-readable files found in %s\nTry running again with --privileged option just to make sure (requires root)\n" % arguments.target)

    def get_completion_suggestions(self, action, text, **kwargs):
        if action.dest == "target":
            return common.path_completion.on_agent(text, self)
