from pysolar.reflection import ReflectionException

from drozer.modules import common, Module

class FindUris(Module, common.FileSystem, common.PackageManager, common.Provider, common.Strings, common.ZipFile):

    name = "Search for content providers that can be queried from our context."
    description = "Search for content providers that can be queried from our context."
    examples = "run scanner.provider.finduris"
    author = "Luander (luander.r@samsung.com)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["scanner", "provider"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("-a", "--package", help="specify a package to search")
    
    def execute(self, arguments):
        accessible_uris = set([])
        
        # attempt to query each content uri
        for uri in self.findAllContentUris(arguments.package):
            try:
                response = self.contentResolver().query(uri)
            except ReflectionException:
                response = None
            
            if response == None:
                self.stdout.write("No response from content URI:      %s\n" % uri)
            else:
                self.stdout.write("Got a response from content Uri:  %s\n" % uri)

                accessible_uris.add(uri)

        # print out a report
        if len(accessible_uris) > 0:
            self.stdout.write("\nFor sure accessible content URIs:\n")
            for uri in accessible_uris:
                self.stdout.write("  %s\n" % uri)
        else:
            self.stdout.write("\nNone of the content URIs replied.\nUse `app.provider.info` to check for each URI's permissions.\nUse `app.provider.query` to send custom queries.\n")
