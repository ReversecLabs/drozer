from drozer.modules import common, Module
import pdb

class Backup(Module, common.Filters, common.PackageManager):

    name = "Lists packages that use the backup API (returns true on FLAG_ALLOW_BACKUP)"
    description = "Lists packages that use the backup API (retruns true on FLAG_ALLOW_BACKUP)"
    examples = ""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "package"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    FLAG_ALLOW_BACKUP = 0x0008000
    API_KEY_HANDLE = "com.google.android.backup.api_key"

    def add_arguments(self, parser):
        parser.add_argument("-f", "--filter", action="store", dest="filter", default=None, help="filter term (By Package Name)")
        parser.add_argument("-k", "--api-keys", action="store_true", dest="api_key", default=False, help="Only print packages that contain api keys")
    def execute(self, arguments):
        if arguments.api_key:
            packages = [s for s in self.packageManager().getPackages(common.PackageManager.GET_META_DATA | common.PackageManager.GET_ACTIVITIES) if s.applicationInfo.metaData != None and s.applicationInfo.metaData.containsKey(Backup.API_KEY_HANDLE)]
        else:
            packages = self.packageManager().getPackages(common.PackageManager.GET_META_DATA | common.PackageManager.GET_ACTIVITIES)

        for package in [p for p in packages if arguments.filter == None or p.packageName.upper().find(arguments.filter.upper()) >= 0]:
            application = package.applicationInfo

            if (application.flags & Backup.FLAG_ALLOW_BACKUP) != 0:
                self.stdout.write("Package: %s\n"%package.packageName)
                self.stdout.write("  UID: %s\n"%application.uid)
                self.stdout.write("  Backup Agent: %s\n"%application.backupAgentName)
                if application.metaData != None and application.metaData.containsKey(Backup.API_KEY_HANDLE):
                    self.stdout.write("  API Key: %s\n" % application.metaData.getString(Backup.API_KEY_HANDLE))
                else:
                    self.stdout.write("  API Key: Unknown\n")
                    
