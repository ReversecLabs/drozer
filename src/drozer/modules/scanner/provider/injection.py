from pysolar.reflection import ReflectionException

from drozer.modules import common, Module

class Injection(Module, common.FileSystem, common.PackageManager, common.Provider, common.Strings, common.ZipFile):

    name = "Test content providers for SQL injection vulnerabilities."
    description = "Search for content providers with SQL Injection vulnerabilities."
    examples = ""
    author = "Rob (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["scanner", "provider"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("-a", "--package", "--uri", dest="package_or_uri", help="specify a package, or content uri to search", metavar="<package or uri>")
        
    def execute(self, arguments):
        vulnerable = { 'projection': set([]), 'selection': set([]), 'uris': set([]) }
    
        if arguments.package_or_uri != None and arguments.package_or_uri.startswith("content://"):
            self.__test_uri(arguments.package_or_uri, vulnerable)
        else:
            for uri in self.findAllContentUris(arguments.package_or_uri):
                self.__test_uri(uri, vulnerable)

        # remove the collection of vulnerable URIs from the set of all URIs
        vulnerable['uris'] = vulnerable['uris'] - vulnerable['projection'] - vulnerable['selection']
                        
        # print out a report
        self.stdout.write("Not Vulnerable:\n")
        if len(vulnerable['uris']) > 0:
            for uri in vulnerable['uris']:
                self.stdout.write("  %s\n" % uri)
        else:
            self.stdout.write("  No non-vulnerable URIs found.\n")

        self.stdout.write("\nInjection in Projection:\n")
        if len(vulnerable['projection']) > 0:
            for uri in vulnerable['projection']:
                self.stdout.write("  %s\n" % uri)
        else:
            self.stdout.write("  No vulnerabilities found.\n")

        self.stdout.write("\nInjection in Selection:\n")
        if len(vulnerable['selection']) > 0:
            for uri in vulnerable['selection']:
                self.stdout.write("  %s\n" % uri)
        else:
            self.stdout.write("  No vulnerabilities found.\n")

    def __test_uri(self, uri, vulnerable):
        vulnerable['uris'].add(uri)

        try:
            self.contentResolver().query(uri, projection=["'"])
        except ReflectionException as e:
            if "unrecognized token" in str(e):
                vulnerable['projection'].add(uri)

        try:
            self.contentResolver().query(uri, selection="'")
        except ReflectionException as e:
            if "unrecognized token" in str(e):
                vulnerable['selection'].add(uri)
            
