from drozer.modules import common, Module

class SFlag(Module, common.ToyBox, common.Shell, common.SuperUser, common.PackageManager):

    name = "Find suid/sgid files in the given folder or package"
    description = "Find suid/sgid files in the given folder or package. Target can be a directory path or package name."
    examples = """dz> run scanner.misc.sflag_binaries /system
Discovered suid/sgid files in /system:
  /system/bin/su
  /system/xbin/su
  ...<snipped>...

dz> run scanner.misc.sflag_binaries com.android.browser --privileged
Discovered suid/sgid files in /data/data/com.android.browser:
  ...
"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2013-08-16"
    license = "BSD (3 clause)"
    path = ["scanner", "misc"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("target", help="the target directory path or package name to search")
        parser.add_argument("-p", "--privileged", action="store_true", default=False, help="request root to perform the task in a privileged context")

    def _resolve_target(self, target):
        """
        Resolve the target to a directory path.
        If target looks like a package name (contains dots, no slashes),
        try to get the package data directory.
        Returns tuple: (resolved_path, display_name, error_message)
        """
        # If target contains a slash, treat it as a directory path
        if '/' in target:
            return (target, target, None)

        # If target contains dots, it might be a package name
        if '.' in target:
            try:
                package = self.packageManager().getPackageInfo(target, 0)
                data_dir = package.applicationInfo.dataDir
                if data_dir:
                    return (data_dir, target, None)
                else:
                    return (None, target, "Package '%s' has no data directory" % target)
            except common.PackageManager.NoSuchPackageException:
                # Maybe it's still a directory path that contains dots
                return (target, target, None)
            except Exception as e:
                return (None, target, "Error resolving package '%s': %s" % (target, str(e)))

        # Otherwise treat as directory path
        return (target, target, None)

    def execute(self, arguments):
        # Resolve target to directory path
        resolved_path, display_name, error = self._resolve_target(arguments.target)

        if error:
            self.stderr.write("%s\n" % error)
            return

        if not resolved_path:
            self.stderr.write("Could not resolve target: %s\n" % arguments.target)
            return

        if self.isFindInstalled():
            command = "find %s -type f \( -perm -04000 -o -perm -02000 \) \-exec ls {} \;" % resolved_path
        else:
            if (self.isToyBoxInstalled() == True):
                command = self.toyboxPath() + " find %s -type f \( -perm -04000 -o -perm -02000 \) \-exec ls {} \;" % resolved_path
            else:
                self.stderr.write("Since the Agent does not have a find binary, this command requires ToyBox to complete. Run tools.setup.toybox and then retry.\n")
                self.stderr.write("Note: On Android 10+, ToyBox cannot be executed from app data directories due to security restrictions.\n")
                self.stderr.write("The native find binary should be available on most Android devices.\n")
                return

        privileged = arguments.privileged
        if privileged:
            if self.isAnySuInstalled():
                command = self.suPath() + " -c \"%s\"" % command
            else:
                self.stdout.write("su is not installed...reverting back to unprivileged mode\n")
                privileged = False

        files = self.shellExec(command)
        writable_files = []

        for f in iter(files.split("\n")):
            if not f.startswith('find: ') and len(f.strip()) > 0:
                writable_files.append(f)

        if len(writable_files) > 0:
            self.stdout.write("Discovered suid/sgid files in %s:\n" % display_name)
            for f in writable_files:
                self.stdout.write("  %s\n" % f)
        else:
            if privileged:
                self.stdout.write("No suid/sgid files found in %s\n" % display_name)
            else:
                self.stdout.write("No suid/sgid files found in %s\nTry running again with --privileged option just to make sure (requires root)\n" % display_name)

    def get_completion_suggestions(self, action, text, **kwargs):
        if action.dest == "target":
            return common.path_completion.on_agent(text, self)
