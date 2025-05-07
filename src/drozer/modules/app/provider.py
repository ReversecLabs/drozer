import os
import base64

from drozer import android
from drozer.modules import common, Module

class Columns(Module, common.Provider, common.TableFormatter):

    name = "List columns in content provider"
    description = "List the columns in the specified content provider URI."
    examples = """List the columns of content://settings/secure

    dz> run app.provider.columns content://settings/secure
    | _id | name | value |"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "provider"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("uri", help="the content provider uri to query")

    def execute(self, arguments):
        c = self.contentResolver().query(arguments.uri)

        if c != None:
            columns = c.getColumnNames()
            c.close();

            self.print_table([columns])
        else:
            self.stderr.write("Unable to get columns from %s\n"%arguments.uri)

class Delete(Module, common.Provider):

    name = "Delete from a content provider"
    description = "Delete from the specified content provider URI."
    examples = """Delete from content://settings/secure, with name condition:

    dz> run app.provider.delete content://settings/secure
                --selection "name=?"
                --selection-args my_setting"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "provider"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("uri", help="the content provider uri to query")
        parser.add_argument("--selection", default=None, metavar="conditions", help="the conditions to apply to the query, as in \"WHERE <conditions>\"")
        parser.add_argument("--selection-args", default=None, metavar="arg", nargs="*", help="any parameters to replace '?' in --selection")
    
    def execute(self, arguments):
        self.contentResolver().delete(arguments.uri, arguments.selection, arguments.selection_args)

        self.stdout.write("Done.\n\n")

class Download(Module, common.Provider):

    name = "Download a file from a content provider that supports files"
    description = "Read from the specified content uri using openInputStream, and download to the local file system"
    examples = """Download, using directory traversal on a content provider:

    dz> run app.provider.download content://vulnerable.provider/../../../system/etc/hosts /tmp/hostsfile
    Written 25 bytes"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "provider"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("uri", help="the content provider URI to read a file through")
        parser.add_argument("destination", help="path to save the downloaded file to")

    def execute(self, arguments):
        data = self.contentResolver().read(arguments.uri)

        # yaynoteyay
        # TODO WILLIAM PLEASE
        # data is a base64 encoded string
        data = base64.b64decode(data)
        
        if os.path.isdir(arguments.destination):
            arguments.destination = os.path.sep.join([arguments.destination, arguments.uri.split("/")[-1]])
        
        # yaynoteyay
        # TODO WILLIAM PLEASE
        # instead of `output.write(str(data))`
        # we just write as a binary file
        output = open(arguments.destination, 'wb')
        output.write(data)
        output.close()

        self.stdout.write("Written %d bytes\n\n" % len(data))

    def get_completion_suggestions(self, action, text, **kwargs):
        if action.dest == "destination":
            return common.path_completion.on_console(text)
        
class FindUri(Module, common.FileSystem, common.PackageManager, common.Provider, common.Strings, common.ZipFile):

    name = "Find referenced content URIs in a package"
    description = """Finds Content URIs within a package.
    
This module uses a number of strategies to identify a content URI, including inspecting the authorities, path permissions and searching for strings inside the package."""
    examples = """Find content provider URIs in the Browser:

    dz> run app.provider.finduri com.android.browser
    Scanning com.android.browser...
    content://com.android.browser.home/res/raw/
    content://browser/search_suggest_query
    content://browser/
    content://com.android.browser.snapshots/
    content://com.android.browser/bookmarks/search_suggest_query
    content://com.android.browser/
    content://com.google.settings/partner
    content://com.android.browser.snapshots
    content://com.google.android.partnersetup.rlzappprovider/
    content://com.android.browser.home/
    content://browser/bookmarks/search_suggest_query"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-13-18"
    license = "BSD (3 clause)"
    path = ["app", "provider"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("package", help="the package to search for content provider uris")

    def execute(self, arguments):
        uris = self.findAllContentUris(arguments.package)
        
        if len(uris) > 0:
            for uri in uris:
                self.stdout.write("%s\n" % uri[uri.upper().find("CONTENT"):])
        else:
            self.stdout.write("No Content URIs found.\n")

class Info(Module, common.Filters, common.PackageManager):

    name = "Get information about exported content providers"
    description = "List information about exported content providers, with optional filters."
    examples = """Find content provider with the keyword "settings" in them:

    dz> run app.provider.info -f settings

    Package name: com.google.android.gsf
    Authority: com.google.settings
    Required Permission - Read: null
    Required Permission - Write: com.google.android.providers.settings.permission.WRITE_GSETTINGS
    Grant Uri Permissions: false
    Multiprocess allowed: false

    Package name: com.android.providers.settings
    Authority: settings
    Required Permission - Read: null
    Required Permission - Write: android.permission.WRITE_SETTINGS
    Grant Uri Permissions: false
    Multiprocess allowed: false

Finding content providers that do not require permissions to read/write:

    dz> run app.provider.info -p null

    Package name: com.google.android.gsf
    Authority: com.google.settings
    Required Permission - Read: null
    Required Permission - Write: com.google.android.providers.settings.permission.WRITE_GSETTINGS
    Grant Uri Permissions: false
    Multiprocess allowed: false

    ..."""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "provider"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    PatternMatcherTypes = { 0: "PATTERN_LITERAL", 1: "PATTERN_PREFIX", 2: "PATTERN_SIMPLE_GLOB" }

    def add_arguments(self, parser):
        parser.add_argument("-a", "--package", default=None, help="specify the package to inspect")
        parser.add_argument("-f", "--filter", default=None, help="specify filter conditions")
        parser.add_argument("-p", "--permission", default=None, help="specify permission conditions")
        parser.add_argument("-u", "--unexported", action="store_true", default=False, help="include providers that are not exported")
        parser.add_argument("-v", "--verbose", action="store_true", default=False, help="be verbose")

    def execute(self, arguments):
        if arguments.package == None:
            for package in self.packageManager().getPackages(common.PackageManager.GET_PROVIDERS | common.PackageManager.GET_URI_PERMISSION_PATTERNS):
                self.__get_providers(arguments, package)
        else:
            package = self.packageManager().getPackageInfo(arguments.package, common.PackageManager.GET_PROVIDERS | common.PackageManager.GET_URI_PERMISSION_PATTERNS)

            self.__get_providers(arguments, package)
            
    def get_completion_suggestions(self, action, text, **kwargs):
        if action.dest == "permission":
            return ["null"] + android.permissions

    def __get_providers(self, arguments, package):
        providers = self.match_filter(package.providers, 'authority', arguments.filter)        
        
        if arguments.permission != None:
            r_providers = self.match_filter(providers, 'readPermission', arguments.permission)
            w_providers = self.match_filter(providers, 'writePermission', arguments.permission)

            providers = set(r_providers + w_providers)
            
        exported_providers = self.match_filter(providers, 'exported', True)
        hidden_providers = self.match_filter(providers, 'exported', False)

        if len(exported_providers) > 0 or arguments.unexported and len(providers) > 0:
            self.stdout.write("Package: %s\n" % package.packageName)
            if(arguments.unexported):
                self.stdout.write("  Exported Providers:\n")
            for provider in exported_providers:
                if(provider.authority == None):
                    provider.authority = "null"
                for authority in provider.authority.split(";"):
                    self.__print_provider(provider, authority, "    " if arguments.unexported else "  ") # 2-space indent if we're only printing exported providers, 4 if we're doing both exported and unexported
            if(arguments.unexported):
                self.stdout.write("  Hidden Providers:\n")
                for provider in hidden_providers:
                    if(provider.authority == None):
                        provider.authority = "null"
                    for authority in provider.authority.split(";"):
                        self.__print_provider(provider, authority, "    ")
            self.stdout.write("\n")
        elif arguments.package or arguments.verbose:
            self.stdout.write("Package: %s\n" % package.packageName)
            self.stdout.write("  No matching providers.\n\n")

    def __print_provider(self, provider, authority, prefix):
        self.stdout.write("%sAuthority: %s\n" % (prefix, authority))
        self.stdout.write("%s  Read Permission: %s\n" % (prefix, provider.readPermission))
        self.stdout.write("%s  Write Permission: %s\n" % (prefix, provider.writePermission))
        self.stdout.write("%s  Content Provider: %s\n" % (prefix, provider.name))
        self.stdout.write("%s  Multiprocess Allowed: %s\n" % (prefix, provider.multiprocess))
        self.stdout.write("%s  Grant Uri Permissions: %s\n" % (prefix, provider.grantUriPermissions))
        if provider.uriPermissionPatterns != None:
            self.stdout.write("%s  Uri Permission Patterns:\n" % prefix)
            for pattern in provider.uriPermissionPatterns:
                self.stdout.write("%s    Path: %s\n" % (prefix, pattern.getPath()))
                self.stdout.write("%s      Type: %s\n" % (prefix, Info.PatternMatcherTypes[int(pattern.getType())]))
        if provider.pathPermissions != None:
            self.stdout.write("%s  Path Permissions:\n" % prefix)
            for permission in provider.pathPermissions:
                self.stdout.write("%s    Path: %s\n" % (prefix, permission.getPath()))
                self.stdout.write("%s      Type: %s\n" % (prefix, Info.PatternMatcherTypes[int(permission.getType())]))
                self.stdout.write("%s      Read Permission: %s\n" % (prefix, permission.getReadPermission()))
                self.stdout.write("%s      Write Permission: %s\n" % (prefix, permission.getWritePermission()))

class Insert(Module, common.Provider):

    name = "Insert into a Content Provider"
    description = "Insert into a content provider."
    examples = """Insert into a vulnerable content provider:

    dz> run app.provider.insert content://com.vulnerable.im/messages
                --string date 1331763850325
                --string type 0
                --integer _id 7"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "provider"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("uri", help="the content provider uri to insert into")
        parser.add_argument('--boolean', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--double', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--float', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--integer', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--long', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--short', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--string', action="append", nargs=2, metavar=('column', 'data'))
    
    def execute(self, arguments):
        values = self.new("android.content.ContentValues")

        if arguments.boolean != None:
            for b in arguments.boolean:
                values.put(b[0], self.arg(b[1].upper().startswith("T"), obj_type="boolean"))
        if arguments.double != None:
            for d in arguments.double:
                values.put(d[0], self.arg(d[1], obj_type="double"))
        if arguments.float != None:
            for f in arguments.float:
                values.put(f[0], self.arg(f[1], obj_type="float"))
        if arguments.integer != None:
            for i in arguments.integer:
                values.put(i[0], self.arg(int(i[1]), obj_type="int"))
        if arguments.long != None:
            for l in arguments.long:
                values.put(l[0], self.arg(l[1], obj_type="long"))
        if arguments.short != None:
            for s in arguments.short:
                values.put(s[0], self.arg(s[1], obj_type="short"))
        if arguments.string != None:
            for s in arguments.string:
                values.put(s[0], self.arg(s[1], obj_type="string"))

        self.contentResolver().insert(arguments.uri, values);

        self.stdout.write("Done.\n\n")
        
class Query(Module, common.Provider, common.TableFormatter):

    name = "Query a content provider"
    description = "Query a content provider"
    examples = """Querying the settings content provider:

    dz> run app.provider.query content://settings/secure

    | _id | name                                    | value   |
    | 5   | assisted_gps_enabled                    | 1       |
    | 9   | wifi_networks_available_notification_on | 1       |
    | 10  | sys_storage_full_threshold_bytes        | 2097152 |
    | ... | ...                                     | ...     |

Querying, with a WHERE clause in the SELECT statement:

    dz> run app.provider.query content://settings/secure
                --selection "_id=?"
                --selection-args 10
    
    | _id | name                                    | value   |
    | 10  | sys_storage_full_threshold_bytes        | 2097152 |"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "provider"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("uri", help="the content provider uri to query")
        parser.add_argument("--projection", default=None, metavar="columns", nargs="*", help="the columns to SELECT from the database, as in \"SELECT <projection> FROM ...\"")
        parser.add_argument("--selection", default=None, metavar="conditions", help="the conditions to apply to the query, as in \"WHERE <conditions>\"")
        parser.add_argument("--selection-args", default=None, metavar="arg", nargs="*", help="any parameters to replace '?' in --selection")
        parser.add_argument("--order", default=None, metavar="by_column", help="the column to order results by")
        parser.add_argument("--vertical", action="store_true", default=False)

    def execute(self, arguments):
        c = self.contentResolver().query(arguments.uri, arguments.projection, arguments.selection, arguments.selection_args, arguments.order)

        if c != None:
            rows = self.getResultSet(c)

            self.print_table(rows, show_headers=True, vertical=arguments.vertical)
        else:
            self.stdout.write("Unknown Error.\n\n")

class Read(Module, common.Provider):

    name = "Read from a content provider that supports files"
    description = "Read from the specified content uri using openInputStream"
    examples = """Attempt directory traversal on a content provider:

    dz> run app.provider.read content://settings/secure/../../../system/etc/hosts
    java.io.FileNotFoundException: No files supported by provider at content://settings/secure/../../../system/etc/hosts"""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "provider"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("uri", help="the content provider URI to read a file through")

    def execute(self, arguments):
        # yaynoteyay
        # TODO WILLIAM PLEASE
        # the old code could more easily convert the retrieved file to a string
        # this time we can't. so we convert to base64, and then decode here while ignoring errors, since we are just printing to console anyway.
        yayencodedyay = self.contentResolver().read(arguments.uri)
        self.stdout.write(base64.b64decode(yayencodedyay).decode("utf-8", errors="ignore") + "\n")
        
class Update(Module, common.Provider):

    name = "Update a record in a content provider"
    description = "Update the specified content provider URI"
    examples = """Updating, the assisted_gps_enabled setting:

    dz> run app.provider.update content://settings/secure
                --selection "name=?"
                --selection-args assisted_gps_enabled
                --integer value 0
    Done."""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "provider"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("uri", help="the content provider uri to update in")
        parser.add_argument("--selection", default=None, metavar="conditions", help="the conditions to apply to the query, as in \"WHERE <conditions>\"")
        parser.add_argument("--selection-args", default=None, metavar="arg", nargs="*", help="any parameters to replace '?' in --selection")
        parser.add_argument('--boolean', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--double', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--float', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--integer', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--long', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--short', action="append", nargs=2, metavar=('column', 'data'))
        parser.add_argument('--string', action="append", nargs=2, metavar=('column', 'data'))
    
    def execute(self, arguments):
        values = self.new("android.content.ContentValues")

        if arguments.boolean != None:
            for b in arguments.boolean:
                values.put(b[0], self.arg(b[1].upper().startswith("T"), obj_type="boolean"))
        if arguments.double != None:
            for d in arguments.double:
                values.put(d[0], self.arg(d[1], obj_type="double"))
        if arguments.float != None:
            for f in arguments.float:
                values.put(f[0], self.arg(f[1], obj_type="float"))
        if arguments.integer != None:
            for i in arguments.integer:
                values.put(i[0], self.arg(i[1], obj_type="integer"))
        if arguments.long != None:
            for l in arguments.long:
                values.put(l[0], self.arg(l[1], obj_type="long"))
        if arguments.short != None:
            for s in arguments.short:
                values.put(s[0], self.arg(s[1], obj_type="short"))
        if arguments.string != None:
            for s in arguments.string:
                values.put(s[0], self.arg(s[1], obj_type="string"))

        self.contentResolver().update(arguments.uri, values, arguments.selection, arguments.selection_args)

        self.stdout.write("Done.\n\n")

class Call(Module, common.Provider):

    name = "Call a call in a content provider"
    description = "Call a call in a content provider"
    examples = """Assuming that a Content Provider `call` method accepts the method `yaymethodyay`:

    dz> run app.provider.call content://yayauthorityyay
                --method "yaymethodyay"
                --argument "yayargumentyay"
                --bundle "S.yaystringyay=yayvalueyay;B.yaybooleanyay=false"

    Done."""
    author = "Yogehi (@yogehi) / Malicious Erection LLC"
    date = "2025-05-07"
    license = "BSD (3 clause)"
    path = ["app", "provider"]
    permissions = ["com.WithSecure.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("uri", help="the content provider URI that accepts a 'call'")
        parser.add_argument("--method", default=None, help="specify an method string")
        parser.add_argument("--argument", default=None, help="specify an argument string")
        parser.add_argument("--bundle", default=None, help="specify a bundle extra")
        

    def execute(self, arguments):
        yaybundleyay = self.new("android.os.Bundle")
        if arguments.bundle != None:
            # if bundle string ends with `;`, remove last `;`
            if arguments.bundle.endswith(';'):
                yaybundlestringyay = arguments.bundle[:-1]
            else:
                yaybundlestringyay = arguments.bundle
            # parse bundle string
            yaybundlearrayyay = yaybundlestringyay.split(';')
            for yayitemyay in yaybundlearrayyay:
                yayKeyyay = yayitemyay.split('=')[0]
                yayValueyay = yayitemyay.split('=')[1]
                if yayKeyyay.startswith("S."):
                    yaybundleyay.putString(yayKeyyay[2:], self.arg(yayValueyay, obj_type="string"))
                elif yayKeyyay.startswith("B."):
                    yaybundleyay.putBoolean(yayKeyyay[2:], self.arg(yayValueyay.lower().startswith('t'), obj_type="boolean"))
                elif yayKeyyay.startswith("b."):
                    yaybundleyay.putByte(yayKeyyay[2:], self.arg(yayValueyay, obj_type="byte"))
                elif yayKeyyay.startswith("c."):
                    yaybundleyay.putChar(yayKeyyay[2:], self.arg(yayValueyay, obj_type="char"))
                elif yayKeyyay.startswith("d."):
                    yaybundleyay.putDouble(yayKeyyay[2:], self.arg(yayValueyay, obj_type="double"))
                elif yayKeyyay.startswith("i."):
                    yaybundleyay.putInt(yayKeyyay[2:], self.arg(yayValueyay, obj_type="int"))
                elif yayKeyyay.startswith("f."):
                    yaybundleyay.putFloat(yayKeyyay[2:], self.arg(yayValueyay, obj_type="float"))
                elif yayKeyyay.startswith("l."):
                    yaybundleyay.putLong(yayKeyyay[2:], self.arg(yayValueyay, obj_type="long"))
                elif yayKeyyay.startswith("s."):
                    yaybundleyay.putShort(yayKeyyay[2:], self.arg(yayValueyay, obj_type="short"))

        yayencodedyay = self.contentResolver().call(arguments.uri, arguments.method, arguments.argument, yaybundleyay)
        self.stdout.write(base64.b64decode(yayencodedyay).decode("utf-8", errors="ignore") + "\n")