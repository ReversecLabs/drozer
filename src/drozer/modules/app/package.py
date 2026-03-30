import re

from drozer import android
from drozer.modules import common, Module

class AttackSurface(Module, common.Filters, common.PackageManager):

    name = "Get attack surface of package"
    description = "Examine the attack surface of an installed package."
    examples = """Finding the attack surface of the built-in browser

    dz> run app.package.attacksurface com.android.browser

    6 activities exported
    4 broadcast receivers exported
    1 content providers exported
    0 services exported"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "package"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("package", help="the identifier of the package to inspect")

    def execute(self, arguments):
        if arguments.package != None:
            package = self.packageManager().getPackageInfo(arguments.package, common.PackageManager.GET_ACTIVITIES | common.PackageManager.GET_RECEIVERS | common.PackageManager.GET_PROVIDERS | common.PackageManager.GET_SERVICES)
            application = package.applicationInfo

            # yaynoteyay
            # removed `list()` from here because i added `list()` to `src/drozer/modules/common/filtering.py` line 16
            activities = self.match_filter(package.activities, 'exported', True)
            receivers = self.match_filter(package.receivers, 'exported', True)
            providers = self.match_filter(package.providers, 'exported', True)
            services = self.match_filter(package.services, 'exported', True)
            
            self.stdout.write("Attack Surface:\n")
            self.stdout.write("  %d activities exported\n" % len(activities))
            self.stdout.write("  %d broadcast receivers exported\n" % len(receivers))
            self.stdout.write("  %d content providers exported\n" % len(providers))
            self.stdout.write("  %d services exported\n" % len(services))

            if (application.flags & application.FLAG_DEBUGGABLE) != 0:
                self.stdout.write("    is debuggable\n")

            if package.sharedUserId != None:
                self.stdout.write("    Shared UID (%s)\n" % package.sharedUserId)
        else:
            self.stdout.write("No package specified\n")

class Info(Module, common.Filters, common.PackageManager, common.IntentFilter):

    name = "Get information about installed packages"
    description = "List all installed packages on the device with optional filters. Specify optional keywords to search for in the package information, or granted permissions."
    examples = """Finding all packages with the keyword "browser" in their name:

    dz> run app.package.info -f browser

    Package: com.android.browser
      Process name: com.android.browser
      Version: 4.1.1
      Data Directory: /data/data/com.android.browser
      APK path: /system/app/Browser.apk
      UID: 10014
      GID: [3003, 1015, 1028]
      Shared libraries: null
      Permissions:
      - android.permission.ACCESS_COARSE_LOCATION
      - android.permission.ACCESS_DOWNLOAD_MANAGER
      - android.permission.ACCESS_FINE_LOCATION
      ...

Finding all packages with the "INSTALL_PACKAGES" permission:

    dz> run app.package.info -p INSTALL_PACKAGES

    Package: com.android.packageinstaller
      Process Name: com.android.packageinstaller
      Version: 4.1.1-403059
      Data Directory: /data/data/com.android.packageinstaller
      APK Path: /system/app/PackageInstaller.apk
      UID: 10003
      GID: [1028]
      Shared Libraries: null
      Shared User ID: null
      Permissions:
      - android.permission.INSTALL_PACKAGES
      - android.permission.DELETE_PACKAGES
      - android.permission.CLEAR_APP_CACHE
      - android.permission.READ_PHONE_STATE
      - android.permission.CLEAR_APP_USER_DATA
      - android.permission.READ_EXTERNAL_STORAGE"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "package"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("-a", "--package", default=None, help="the identifier of the package to inspect")
        parser.add_argument("-d", "--defines-permission", default=None, help="filter by the permissions a package defines")
        parser.add_argument("-f", "--filter", default=None, help="keyword filter conditions")
        parser.add_argument("-g", "--gid", default=None, help="filter packages by GID")
        parser.add_argument("-p", "--permission", default=None, help="permission filter conditions")
        parser.add_argument("-u", "--uid", default=None, help="filter packages by UID")
        parser.add_argument("-i", "--show-intent-filters", action="store_true", default=False , help="show intent filters")

    def execute(self, arguments):
        if arguments.package == None:
            for package in self.packageManager().getPackages(common.PackageManager.GET_PERMISSIONS | common.PackageManager.GET_CONFIGURATIONS | common.PackageManager.GET_GIDS | common.PackageManager.GET_SHARED_LIBRARY_FILES | common.PackageManager.GET_ACTIVITIES):
               self.__get_package(arguments, package) 
        else:
            package = self.packageManager().getPackageInfo(arguments.package, common.PackageManager.GET_PERMISSIONS | common.PackageManager.GET_CONFIGURATIONS | common.PackageManager.GET_GIDS | common.PackageManager.GET_SHARED_LIBRARY_FILES | common.PackageManager.GET_ACTIVITIES)
            self.__get_package(arguments, package)
            
    def get_completion_suggestions(self, action, text, **kwargs):
        if action.dest == "permission":
            return android.permissions

    def __print_intent_filters(self, intent_filters):
        for intent_filter in intent_filters:
            if len(intent_filter.actions) > 0:
                self.stdout.write("    - Actions:\n")
                for action in intent_filter.actions:
                    self.stdout.write("      - %s\n" % action)
            if len(intent_filter.categories) > 0:
                self.stdout.write("    - Categories:\n")
                for category in intent_filter.categories:
                    self.stdout.write("      - %s\n" % category)
            if len(intent_filter.datas) > 0:
                self.stdout.write("    - Data:\n" )
                for data in intent_filter.datas:
                    self.stdout.write("      - %s\n" % data)

    def __get_package(self, arguments, package):
        application = package.applicationInfo
        activities = package.activities
        services = package.services

        intent_matches = not (arguments.show_intent_filters and arguments.filter)

        if not intent_matches and arguments.filter != None: 
            if activities != None:
                for activity in activities:
                    if not intent_matches:
                        for intent_filter in self.find_intent_filters(activity, 'activity'):
                            if len(intent_filter.actions) > 0:
                                for action in intent_filter.actions:
                                    if action != None and action.upper().find(arguments.filter.upper()) >= 0:
                                        intent_matches = True
                                        break

                            if len(intent_filter.datas) > 0:
                                for data in intent_filter.datas:
                                    if data.scheme != None and data.scheme != False and data.scheme.upper().find(arguments.filter.upper()) >= 0:
                                        intent_matches = True
                                        break

                            if len(intent_filter.categories) > 0:
                                for category in intent_filter.categories:
                                    if category != None and category.upper().find(arguments.filter.upper()) >= 0:
                                        intent_matches = True
                                        break
                    else:
                        break

            if services != None:
                for service in services:
                    if not intent_matches:
                        for intent_filter in self.find_intent_filters(service, 'service'):
                            if len(intent_filter.actions) > 0:
                                for action in intent_filter.actions:
                                    if action != None and action.upper().find(arguments.filter.upper()) >= 0:
                                        intent_matches = True
                                        break

                            if len(intent_filter.uris) > 0:
                                for data in intent_filter.datas:
                                    if data.scheme != None and data.scheme != False and data.scheme.upper().find(arguments.filter.upper()) >= 0:
                                        intent_matches = True
                                        break

                            if len(intent_filter.categories) > 0:
                                for category in intent_filter.categories:
                                    if category != None and category.upper().find(arguments.filter.upper()) >= 0:
                                        intent_matches = True
                                        break
                    else:
                        break

        if (arguments.defines_permission == None or package.permissions != None and True in map(lambda p: p.name.upper().find(arguments.defines_permission.upper()) >= 0, package.permissions)) and (arguments.filter == None or package.packageName.upper().find(arguments.filter.upper()) >= 0 or self.packageManager().getApplicationLabel(package.packageName).upper().find(arguments.filter.upper()) >= 0) and (arguments.gid == None or package.gids != None and True in map(lambda g: g == int(arguments.gid), package.gids)) and (arguments.permission == None or package.requestedPermissions != None and True in map(lambda p: p.upper().find(arguments.permission.upper()) >= 0, package.requestedPermissions)) and (arguments.uid == None or arguments.uid == str(package.applicationInfo.uid)) and intent_matches: 
            self.stdout.write("Package: %s\n" % application.packageName)
            self.stdout.write("  Application Label: %s\n" % self.packageManager().getApplicationLabel(application.packageName))
            self.stdout.write("  Process Name: %s\n" % application.processName)
            self.stdout.write("  Version: %s\n" % package.versionName)
            self.stdout.write("  Data Directory: %s\n" % application.dataDir)
            self.stdout.write("  APK Path: %s\n" % application.publicSourceDir)
            self.stdout.write("  UID: %s\n" % application.uid)
            if package.gids != None:
                self.stdout.write("  GID: %s\n" % package.gids)
            else:
                self.stdout.write("  GID: None\n")
            self.stdout.write("  Shared Libraries: %s\n" % application.sharedLibraryFiles)
            self.stdout.write("  Shared User ID: %s\n" % package.sharedUserId)
            self.stdout.write("  Uses Permissions:\n")
            if package.requestedPermissions != None:
                for permission in package.requestedPermissions:
                    self.stdout.write("  - %s\n" % permission)
            else:
                self.stdout.write("  - None\n")
            self.stdout.write("  Defines Permissions:\n")
            if package.permissions != None:
                for permission in package.permissions:
                    self.stdout.write("  - %s\n" % permission.name)
            else:
                self.stdout.write("  - None\n")
            if arguments.show_intent_filters:
                ifcount = 0
                self.stdout.write("  Intent Filters:\n")

                if activities != None:
                    for activity in activities:
                       intent_filters = self.find_intent_filters(activity, 'activity')
                       if len(intent_filters) > 0:
                           ifcount += len(intent_filters)
                           
                           self.stdout.write("  - %s\n" % activity.name)
                           self.__print_intent_filters(intent_filters)

                if services!= None:
                    for service in services:
                        intent_filters = self.find_intent_filters(service, 'service')
                        if len(intent_filters) > 0:
                            ifcount += len(intent_filters)

                            self.stdout.write("  - %s\n" % service.name)
                            self.__print_intent_filters(intent_filters)

                if ifcount==0:
                    self.stdout.write("  - None")
            self.stdout.write("\n")

                
                                                       
class LaunchIntent(Module, common.PackageManager):

    name = "Get launch intent of package"
    description = "Get the launch intent of an installed package."
    examples = """Finding the launch intent of the Android browser package:

    dz> run app.package.launchintent com.android.browser

    Intent: 
      Action: android.intent.action.MAIN
      Component: {com.android.browser/com.android.browser.BrowserActivity}
      Data: null
      Categories: 
        android.intent.category.LAUNCHER
      Flags: [ACTIVITY_NEW_TASK]
      Mime Type: null
      Extras: null"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2013-03-06"
    license = "BSD (3 clause)"
    path = ["app", "package"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("package", help="the identifier of the package to inspect")
        parser.add_argument("-r", "--raw", action="store_true", default=False, help="display the raw output of the intent (as if you were calling intent.toString())")

    def execute(self, arguments):
        intent = self.packageManager().getLaunchIntentForPackage(arguments.package)

        if intent != None:
            if not arguments.raw:
                self.processIntent(intent)
            else:
                self.stdout.write("%s\n\n" % str(intent.toString()))
        else:
            self.stdout.write("No Launch Intent found.\n\n")
    
    def processIntent(self, intent):

        self.stdout.write("Launch Intent:\n")
        self.stdout.write("  Action: %s\n"%intent.getAction())
        self.stdout.write("  Component: %s\n"%intent.getComponent().toShortString())
        self.stdout.write("  Data: %s\n"%intent.getDataString())
        if intent.getCategories() == None:
            self.stdout.write("  Categories: null\n")
        else:
            self.stdout.write("  Categories: \n")
            for category in intent.getCategories().toArray():
                self.stdout.write("     - %s\n"%str(category.toString()))

        self.stdout.write("  Flags: %s\n"%self.processFlags(intent.getFlags()))
        self.stdout.write("  Mime Type: %s\n"%intent.getType())
        
        extras = intent.getExtras()
        if extras != None:
            if not extras.isEmpty():
                self.stdout.write("  Extras: \n")
                for extra in extras.keySet():
                    self.stdout.write("    - %s\n"%extras.get(extra))
        else:
            self.stdout.write("  Extras: null\n")

    def processFlags(self, flags):

        out = ""
        #flags are a bit mask
        for key in android.Intent.flags.keys():
            for i in range(0, 8):
                flag = flags & (0x0000000F << i*4)
                if android.Intent.flags.get(key) == flag:
                    out = out + "%s, "%key
        if out is not "":
            return "[%s]"%out[:-2]
        else:
            return "null"
            
        
    
class List(Module, common.PackageManager):

    name = "List Packages"
    description = "List all installed packages on the device. Specify optional keywords to search for in the package name."
    examples = """Finding all packages with the keyword "browser" in their name:

    dz> run app.package.list -f browser

    com.android.browser"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "package"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("-d", "--defines-permission", default=None, help="filter by the permissions a package defines")
        parser.add_argument("-f", "--filter", default=None, help="keyword filter conditions")
        parser.add_argument("-g", "--gid", default=None, help="filter packages by GID")
        parser.add_argument("-p", "--permission", default=None, help="permission filter conditions")
        parser.add_argument("-u", "--uid", default=None, help="filter packages by UID")
        parser.add_argument("-n", "--no_app_name", action="store_true", default=False, help="do not print the app name")

    def execute(self, arguments):
        for package in self.packageManager().getPackages(common.PackageManager.GET_PERMISSIONS | common.PackageManager.GET_CONFIGURATIONS | common.PackageManager.GET_GIDS | common.PackageManager.GET_SHARED_LIBRARY_FILES):
            self.__get_package(arguments, package)

    def __get_package(self, arguments, package):
        application = package.applicationInfo

        if (arguments.defines_permission == None or package.permissions != None and True in map(lambda p: p.name.upper().find(arguments.defines_permission.upper()) >= 0, package.permissions)) and (arguments.filter == None or package.packageName.upper().find(arguments.filter.upper()) >= 0 or self.packageManager().getApplicationLabel(application.packageName).upper().find(arguments.filter.upper()) >= 0) and (arguments.gid == None or package.gids != None and True in map(lambda g: g == int(arguments.gid), package.gids)) and (arguments.permission == None or package.requestedPermissions != None and True in map(lambda p: p.upper().find(arguments.permission.upper()) >= 0, package.requestedPermissions)) and (arguments.uid == None or arguments.uid == str(package.applicationInfo.uid)):
            if arguments.no_app_name:
                self.stdout.write("%s\n" % application.packageName)
            else:
                try:
                    self.stdout.write("%s (%s)" % (application.packageName, self.packageManager().getApplicationLabel(application.packageName)))
                    self.stdout.write("\n")
                except IOError as e:
                    self.stdout.write(" (Warning: Cannot decode application label)\n")
                

class Manifest(Module, common.Assets):

    name = "Get AndroidManifest.xml of package"
    description = "Retrieves AndroidManifest.xml from an installed package."
    examples = """Getting the manifest for drozer

    dz> run app.package.manifest com.reversec.dz

    <manifest versionCode="2" versionName="1.1" package="com.reversec.dz">
      <uses-sdk minSdkVersion="8" targetSdkVersion="4">
      </uses-sdk>
      <uses-permission name="android.permission.INTERNET">
      </uses-permission>

      ...
    </manifest>"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "package"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("package", help="the identifier of the package")

    def execute(self, arguments):
        if arguments.package == None or arguments.package == "":
            self.stderr.write("No package provided.\n")
        else:
            self.__write_manifest(self.getAndroidManifest(arguments.package))
           
    
    def __write_manifest(self, manifest):
        lines = manifest.split("\n")
        level = 0
        
        for line in lines:
            if line.startswith("</"):
                level -= 1
            
            if line.startswith("<") and not line.startswith("</"):
                pattern = re.compile("(.*)<([^>]+)>(.*)")
                match = pattern.match(line)
                
                contents = match.group(2).split(" ", 1)
                
                self.stdout.write("%s%s<[color green]%s[/color]" % ("  " * level, match.group(1), contents[0]))
                if len(contents) > 1:
                    self.stdout.write(("\n%s%s" % ("  " * level, " " * (len(contents[0]) + 1))).join(map(lambda m: " [color purple]%s[/color]=[color red]\"%s\"[/color]" % m, re.compile("([^=]+)=\"([^\"]+)\"\s*").findall(contents[1]))))
                        
                self.stdout.write(">\n")
            else:
                self.stdout.write("%s%s\n" % ("  " * level, line))
            
            if line.startswith("<") and not "</" in line:
                level += 1


class Native(Module, common.ClassLoader, common.PackageManager):

    name = "Find Native libraries embedded in the application."
    description = "Find Native libraries embedded in the application."
    examples = ""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2013-03-23"
    license = "BSD (3 clause)"
    path = ["app", "package"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("package", help="the identifier of the package")
    
    def execute(self, arguments):
        Native = self.loadClass("common/Native.apk", "Native")
        
        package = self.packageManager().getPackageInfo(arguments.package, common.PackageManager.GET_PROVIDERS)
        libraries = Native.list(package.applicationInfo)

        if len(libraries) > 0:
            self.stdout.write("Package: %s\n" % package.packageName)
            self.stdout.write("  Native Libraries:\n")

            for library in libraries:
                self.stdout.write("   - %s\n"%library)
            self.stdout.write("\n")
        else:
            self.stdout.write("Package: %s\n" % package.packageName)
            self.stdout.write("  No Native Libraries.\n")
            self.stdout.write("\n")


class SharedUID(Module, common.PackageManager):

    name = "Look for packages with shared UIDs"
    description = "Finds packages that have shared UIDs and gives their accumulated permissions."
    examples = """Finding packages that share the UID 10011

    dz> run app.package.shareduid -u 10011

    UID: 10011 (com.motorola.blur.uid.provider_authenticator:10011)
    Package Name: com.motorola.blur.provider.photobucket
    Package Name: com.motorola.blur.provider.picasa
    Package Name: com.motorola.blur.provider.yahoo
    Package Name: com.motorola.blur.provider.twitter
    Package Name: com.motorola.blur.provider.fixedemail
    Package Name: com.motorola.blur.provider.motorola.app
    Package Name: com.motorola.blur.provider.orkut
    Package Name: com.motorola.blur.provider.email
    Package Name: com.motorola.blur.provider.facebook
    Package Name: com.motorola.blur.provider.lastfm
    Package Name: com.motorola.blur.provider.linkedin
    Package Name: com.motorola.blur.provider.youtube
    Package Name: com.motorola.blur.provider.skyrock
    Package Name: com.motorola.blur.provider.activesync
    Package Name: com.motorola.blur.provider.flickr
    Accumulated permissions: com.motorola.blur.setupprovider.Permissions.ACCESS_ACCOUNTS; ..."""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "package"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("-u", "--uid", default=None, help="specify uid")

    def execute(self, arguments):
        uids = set([])

        if arguments.uid == None:
            for package in self.packageManager().getPackages(common.PackageManager.GET_PERMISSIONS):
                uids.add(int(package.applicationInfo.uid))
        else:
            uids.add(int(arguments.uid))

        for uid in uids:
            self.stdout.write("UID: %d (%s)\n"%(uid, self.packageManager().getNameForUid(uid)))

            packages = self.packageManager().getPackagesForUid(uid)

            if packages != None:
                permissions = set([])

                for packageName in packages:
                    try:
                        package = self.packageManager().getPackageInfo(packageName, common.PackageManager.GET_PERMISSIONS)
                    except:
                        continue
                    self.stdout.write("  Package: %s\n"%packageName)

                    if package.requestedPermissions != None:
                        for permission in package.requestedPermissions:
                            # yaynoteyay
                            # `permission` is a `ReflectedString`
                            # convert it to `String` so it can be put in array `permissions`
                            permissions.add(str(permission))

                self.stdout.write("  Permissions: %s\n"%", ".join(map(lambda p: str(p), permissions)))
                self.stdout.write("\n")
            else:
                self.stdout.write("No such UID.\n")
