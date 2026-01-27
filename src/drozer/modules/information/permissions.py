from drozer.modules import common, Module

class Permissions(Module, common.PackageManager):
    
    name = "Get a list of all permissions used by packages on the device"
    description = "Get a list of all permissions used by packages on the device as well as their descriptions and protection levels"
    examples = '''
    dz> run information.permissions --permission android.permission.INSTALL_PACKAGES
    Allows the app to install new or updated Android packages. Malicious apps may use this to add new apps with arbitrarily powerful permissions.
    18 - signature|system
    '''
    author = "Tyrone (@mwrlabs)"
    date = "2014-06-17"
    license = "BSD (3 clause)"
    path = ["information"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("--permission", help="filter by specific permission")
        parser.add_argument("--protectionlevel", help="filter by protection level")

    def execute(self, arguments):

        con = self.getContext() 
        pm = con.getPackageManager()
        res = con.getResources()

        if (arguments.permission):
            prot = self.__getProtLevel(pm, arguments.permission)
            if (prot != ""):
                self.stdout.write(self.__getDescription(pm, res, arguments.permission) + "\n")
                self.stdout.write(prot + "\n")
            else:
                self.stdout.write("No such permission defined\n")
        else:

            permissionList = []
            
            # Iterate through each package and get unique permissions
            for package in self.packageManager().getPackages(common.PackageManager.GET_PERMISSIONS):
                    if package.requestedPermissions != None:
                        for permission in package.requestedPermissions:
                            if permission not in permissionList:
                                permissionList.append(str(permission))
            
            # Print sorted
            for permission in sorted(permissionList):

                prot = self.__getProtLevel(pm, permission)
                display = False

                if (arguments.protectionlevel):
                    if (arguments.protectionlevel.upper() in prot.upper()):
                        display = True
                else:
                    display = True

                if (display):
                    self.stdout.write(permission + "\n")
                    self.stdout.write(self.__getDescription(pm, res, permission) + "\n")
                    self.stdout.write(prot + "\n\n")

    __protectionLevels = {
        0x01 : 'dangerous',        
        0x02 : 'signature',        
        0x03 : 'signatureOrSystem',        
        0x10 : 'system',
        0x20 : 'development'
    }

    def __getProtLevel(self, pm, permission):

        try:

            pl = pm.getPermissionInfo(permission, 0).protectionLevel
            plHumanReadable = ""

            if (pl == 0):
                plHumanReadable = "normal"
            else:
                for k, v in sorted(self.__protectionLevels.items()):
                    if (pl & k == k):
                        plHumanReadable += v + "|"
                    
                plHumanReadable = plHumanReadable.strip("|")

            return str(pl) + " - " + plHumanReadable

        except:
            return "Unable to retrieve protectionLevel"

    def __getDescription(self, pm, res, permission):

        try:

            descriptionRes = pm.getPermissionInfo(permission, 0).descriptionRes
            return res.getString(descriptionRes)

        except:
            return "No description"