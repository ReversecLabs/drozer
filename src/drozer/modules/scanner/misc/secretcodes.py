from drozer.modules import common, Module

class SecretCodes(Module, common.ClassLoader, common.PackageManager):
    
    name = "Search for secret codes that can be used from the dialer"
    description = "Finds Secret Codes from all installed packages."
    examples = ""
    author = "Mike (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["scanner", "misc"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("-v", "--verbose", action="store_true", default=False, help="be verbose")

    def execute(self, arguments):
        SecretCodes = self.loadClass("scanner/misc/SecretCodes.apk", "SecretCodes")

        for package in self.packageManager().getPackages():
            codes = SecretCodes.find(self.getContext(), package.packageName)

            if len(codes) > 0 or arguments.verbose == True:
                self.stdout.write("Package: %s\n" % package.packageName)

                for code in codes:
                    self.stdout.write("  %s\n" % code)

                self.stdout.write("\n")
                
