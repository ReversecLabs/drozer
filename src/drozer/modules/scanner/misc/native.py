from drozer.modules import common, Module

class Native(Module, common.ClassLoader, common.Filters, common.PackageManager):

    name = "Find native components included in packages"
    description = "Lists packages which use native code.\nNOTE: This only checks for libraries that are bundled inside the package APK. System packages often do not contain the libraries they use inside their APK and so this module will miss them."
    examples = ""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["scanner", "misc"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("-a", "--package", help="specify a package to search")
        parser.add_argument("-f", "--filter", action="store", dest="filter", default=None, help="filter term")
        parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", default=False, help="be verbose")

    def execute(self, arguments):
        Native = self.loadClass("common/Native.apk", "Native")

        if arguments.package != None:
            package = self.packageManager().getPackageInfo(arguments.package, common.PackageManager.GET_PROVIDERS | common.PackageManager.GET_SHARED_LIBRARY_FILES)
            
            self.__find_libraries(package, True, Native)
        else:
            for package in self.packageManager().getPackages(common.PackageManager.GET_PERMISSIONS | common.PackageManager.GET_SHARED_LIBRARY_FILES):
                if arguments.filter == None or package.packageName.upper().find(arguments.filter.upper()) >= 0:
                    self.__find_libraries(package, arguments.verbose, Native)
    
    def __find_libraries(self, package, verbose, Native):
        bundled_libraries = Native.list(package.applicationInfo)
        shared_libraries = package.applicationInfo.sharedLibraryFiles



        self.stdout.write("Package: %s\n" % package.packageName)

        if len(bundled_libraries) > 0:
            self.stdout.write("  Bundled Native Libraries:\n")

            for library in bundled_libraries:
                self.stdout.write("   - %s\n"%library)
            self.stdout.write("\n")

        if shared_libraries != None:
            self.stdout.write("  Shared Native Libraries:\n")

            for library in shared_libraries:
                self.stdout.write("   - %s\n"%library)
                self.stdout.write("\n")

        if shared_libraries == None and len(bundled_libraries) == 0 and verbose:
            self.stdout.write("  No Native Libraries.\n")
            self.stdout.write("\n")
            
