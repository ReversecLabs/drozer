from drozer.modules import common, Module

class Debuggable(Module, common.Filters, common.PackageManager):

    name = "Find debuggable packages"
    description = "Lists packages which are debuggable."
    examples = ""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "package"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    FLAG_DEBUGGABLE = 0x00000002

    def add_arguments(self, parser):
        parser.add_argument("-f", "--filter", action="store", dest="filter", default=None, help="filter term")
        parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=False, help="be verbose")

    def execute(self, arguments):
        for package in self.packageManager().getPackages(common.PackageManager.GET_PERMISSIONS):
            application = package.applicationInfo

            if arguments.filter == None or package.packageName.upper().find(arguments.filter.upper()) >= 0:
                if (application.flags & Debuggable.FLAG_DEBUGGABLE) != 0:
                    self.stdout.write("Package: %s\n"%package.packageName)
                    self.stdout.write("  UID: %s\n"%application.uid)
                    self.stdout.write("  Permissions:\n")

                    permissions = package.requestedPermissions
                    if permissions != None:
                        for permission in permissions:
                            self.stdout.write("   - %s\n"%permission)
                    else:
                        self.stdout.write("   - None.\n")
                    self.stdout.write("\n")
                elif arguments.verbose:
                    self.stdout.write("Package: %s\n"%package.packageName)
                    self.stdout.write("  Not Debuggable.\n")
                    self.stdout.write("\n")
