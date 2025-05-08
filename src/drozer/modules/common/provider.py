from pysolar.reflection import ReflectionException

from drozer.modules.common import loader
from drozer.modules.common.package_manager import PackageManager

# DEBUG
from optparse import OptionParser
import inspect

class Provider(loader.ClassLoader):
    """
    Utility methods for interacting with content providers.
    """

    __content_resolver_proxy = None

    class ContentResolverProxy(object):
        """
        Wrapper for the native Java ContentResolver object, which provides
        convenience methods for constructing some requests and handling some of
        the return types.
        """

        def __init__(self, module):
            self.__module = module
            self.__content_resolver = module.getContext().getContentResolver()
            
            self.__must_release_client = False

        def delete(self, uri, selection, selectionArgs):
            """
            Delete from a content provider, given filter conditions.
            """
            
            client = self.__get_client(uri)

            return_val = None
            try:
                return_val = client.delete(self.parseUri(uri), selection, selectionArgs)
            except ReflectionException as e:
                # yaynoteyay
                # for some reason, ReflectionException doesn't have a `message` attribute
                # so convert to string first
                if str(e).startswith("Unknown Exception"):
                    raise ReflectionException("Could not delete from %s." % uri)
                else:
                    raise
            finally:
                self.__release(client)

            return return_val

        def insert(self, uri, contentValues):
            """
            Insert contentValues into a content provider.
            """
            
            client = self.__get_client(uri)

            return_val = None
            try:
                return_val = client.insert(self.parseUri(uri), contentValues)
            except ReflectionException as e:
                # yaynoteyay
                # for some reason, ReflectionException doesn't have a `message` attribute
                # so convert to string first
                if str(e).startswith("Unknown Exception"):
                    raise ReflectionException("Could not insert into %s." % uri)
                else:
                    raise
            finally:            
                self.__release(client)

            return return_val

        def parseUri(self, uri):
            """
            Convert a String into a Java URI Object.
            """

            return self.__module.klass("android.net.Uri").parse(uri)

        def query(self, uri, projection=None, selection=None, selectionArgs=None, sortOrder=None):
            """
            Query a database-backed content provider, with an optional projection,
            filter conditions and sort order.
            """

            client = self.__get_client(uri)
            
            if client == None:
                raise ReflectionException("Could not get a ContentProviderClient for %s." % uri)
            
            cursor = None
            
            try:
                cursor = client.query(self.parseUri(uri), projection, selection, selectionArgs, sortOrder)
            except ReflectionException as e:

                # yaynoteyay
                # for some reason, ReflectionException doesn't have a `message` attribute
                # so convert to string first
                if str(e).startswith("Unknown Exception"):
                    raise ReflectionException("Could not query %s." % uri)
                else:
                    raise
            finally:  
                self.__release(client)

            return cursor
            

        def read(self, uri):
            """
            Read a file from a file-system-based content provider.
            """
            
            ByteStreamReader = self.__module.loadClass("common/ByteStreamReader.apk", "ByteStreamReader")
            
            client = self.__get_client(uri)

            if self.__must_release_client:
                fd = None
   
                if client != None:
                    try:
                        fd = client.openFile(self.parseUri(uri), "r")
                    except ReflectionException as e:
                        # yaynoteyay
                        # for some reason, ReflectionException doesn't have a `message` attribute
                        # so convert to string first
                        if str(e).startswith("Unknown Exception"):
                            raise ReflectionException("Could not read from %s." % uri)
                        else:
                            raise
    
                self.__release(client)
    
                if fd != None:

                    # yaynoteyay
                    # TODO WILLIAM PLEASE
                    # original code assumed that `ByteStreamReader()` could be converted to `String` automatically. this time, it can't.
                    # for now, returning base64 string
                    yayencodedyay = ByteStreamReader.read(self.__module.new("java.io.FileInputStream", fd.getFileDescriptor())).base64_encode()
                    return yayencodedyay.decode('utf-8')
                else:
                    raise Provider.UnableToOpenFileException(uri)
            else:
                input_stream = self.__content_resolver.openInputStream(self.parseUri(uri))
                
                if input_stream != None:
                    # yaynoteyay
                    # TODO WILLIAM PLEASE
                    # original code assumed that `ByteStreamReader()` could be converted to `String` automatically. this time, it can't.
                    # for now, returning as bytes
                    return ByteStreamReader.read(self.__module.new("java.io.FileInputStream", fd.getFileDescriptor()))
                else:
                    raise Provider.UnableToOpenFileException(uri)

        def update(self, uri, contentValues, selection, selectionArgs):
            """
            Update records in a content provider with contentValues.
            """
            
            client = self.__get_client(uri)

            return_val = None
            try:
                return_val = client.update(self.parseUri(uri), contentValues, selection, selectionArgs)
            except ReflectionException as e:
                # yaynoteyay
                # for some reason, ReflectionException doesn't have a `message` attribute
                # so convert to string first
                if str(e).startswith("Unknown Exception"):
                    raise ReflectionException("Could not update %s." % uri)
                else:
                    raise
            finally:
                self.__release(client)
            
            return return_val
        
        def call(self, uri, method, argument=None, bundle=None):
            """
            Executes against a content provider's "call" method
            """

            client = self.__get_client(uri)
            
            if client == None:
                raise ReflectionException("Could not get a ContentProviderClient for %s." % uri)
            
            yaycallresultyay = None
            
            try:
                yaycallresultyay = client.call(method, argument, bundle)
            except ReflectionException as e:

                # yaynoteyay
                # for some reason, ReflectionException doesn't have a `message` attribute
                # so convert to string first
                if str(e).startswith("Unknown Exception"):
                    raise ReflectionException("Could not call %s." % uri)
                else:
                    raise
            finally:  
                self.__release(client)

            return yaycallresultyay
        
        def __get_client(self, uri):
            try:
                self.__must_release_client = True
                
                return self.__content_resolver.acquireUnstableContentProviderClient(self.parseUri(uri))
            except ReflectionException:
                self.__must_release_client = False
                
                return self.__content_resolver
        
        def __release(self, client):
            if self.__must_release_client and client != None:
                try:
                    client.release()
                except ReflectionException:
                    pass
            
    def contentResolver(self):
        """
        Get a ContentResolver to interact with a ContentProvider.
        """

        if self.__content_resolver_proxy == None:
            self.__content_resolver_proxy = Provider.ContentResolverProxy(self)

        return self.__content_resolver_proxy

    def findAllContentUris(self, package):
        """
        Search a package (or packages) for content providers, by searching the
        manifest and looking for content:// paths in the binary.
        """

        uris = set([])

        # collect content uris by enumerating all authorities, and uris detected
        # in the source
        
        if package == None:
            for package in self.packageManager().getPackages(PackageManager.GET_PROVIDERS | PackageManager.GET_URI_PERMISSION_PATTERNS):
                try:
                    uris = uris.union(self.__search_package(package))
                except ReflectionException as e:
                    if "java.util.zip.ZipException: unknown format" in str(e):
                        self.stderr.write("Skipping package %s, because we cannot unzip it..." % package.applicationInfo.packageName)
                    else:
                        raise
        else:
            package = self.packageManager().getPackageInfo(package, PackageManager.GET_PROVIDERS)

            try:
                uris = uris.union(self.__search_package(package))
            except ReflectionException as e:
                if "java.util.zip.ZipException: unknown format" in str(e):
                    self.stderr.write("Skipping package %s, because we cannot unzip it..." % package.applicationInfo.packageName)
                else:
                    raise

        return uris
        
    def findContentUris(self, package):
        """
        Search a package for content providers, by looking for content:// paths
        in the binary.
        """

        self.deleteFile("/".join([self.cacheDir(), "classes.dex"]))

        content_uris = []
        for path in self.packageManager().getSourcePaths(package):
            strings = []

            if ".apk" in path:
                dex_file = self.extractFromZip("classes.dex", path, self.cacheDir())

                if dex_file != None:
                    strings = self.getStrings(dex_file.getAbsolutePath())

                    dex_file.delete()
                
                # look for an odex file too, because some system packages do not
                # list these in sourceDir
                strings += self.getStrings(path.replace(".apk", ".odex")) 
            elif (".odex" in path):
                strings = self.getStrings(path)
            
            content_uris.append((path, filter(lambda s: ("CONTENT://" in s.upper()) and ("CONTENT://" != s.upper()), strings)))

        return content_uris

    def getResultSet(self, cursor):
        """
        Get a result set from a database cursor, as a 2D array.
        """

        rows = []
        blob_type = self.klass("android.database.Cursor").FIELD_TYPE_BLOB

        if cursor != None:
            columns = cursor.getColumnNames()
            rows.append(columns)

            cursor.moveToFirst()
            while cursor.isAfterLast() == False:
                row = []

                for i in range(len(columns)):
                    try:
                        if(cursor.getType(i) == blob_type):
                            row.append("%s (Base64-encoded)" % (cursor.getBlob(i).base64_encode()))
                        else:
                            row.append(cursor.getString(i))
                    except ReflectionException as e:
                        # yaynoteyay
                        # for some reason, ReflectionException doesn't have a `message` attribute
                        # so convert to string first
                        if str(e).startswith("getType"):
                            try:
                                row.append(cursor.getString(i))
                            except ReflectionException as e:
                                # yaynoteyay
                                # for some reason, ReflectionException doesn't have a `message` attribute
                                # so convert to string first
                                if str(e).startswith("unknown error: Unable to convert BLOB to string"):
                                    row.append("%s (Base64-encoded)" % (cursor.getBlob(i).base64_encode()))
                                else:
                                    raise
                        else:
                            raise

                rows.append(row)

                cursor.moveToNext()

            return rows
        else:
            return None

    def __search_package(self, package):
        """
        Search a package's manifest and binary for content provider URIs, and
        create a union set of them.
        """

        print("Scanning %s..." % package.packageName)

        uris = set([])

        if package.providers != None:
            for provider in package.providers:
                if provider.authority != None:
                    paths = set([])
                    
                    if provider.uriPermissionPatterns != None:
                        for pattern in provider.uriPermissionPatterns:
                            paths.add(str(pattern.getPath()))
                    if provider.pathPermissions != None:
                        for permission in provider.pathPermissions:
                            paths.add(str(permission.getPath()))
                            
                    # TODO: try to handle wildcard paths sensibly, like /contacts/.*/xyz
                    
                    for authority in provider.authority.split(";"):
                        uris.add("content://%s/" % authority)
                        
                        for path in paths:
                            uris.add("content://%s%s" % (authority, path))
        for (path, content_uris) in self.findContentUris(package.packageName):
            content_uris = list(content_uris)
            if len(content_uris) > 0:
                for uri in content_uris:
                    uris.add(uri[uri.upper().find("CONTENT"):])
        
        # one more pass, make sure we get the / and non-/ version of each URI
        for uri in set(uris):
            if uri.endswith("/"):
                uris.add(uri[uri.upper().find("CONTENT"):-1])
            else:
                uris.add(uri[uri.upper().find("CONTENT"):] + "/")

        return sorted(uris)
        
        
    class UnableToOpenFileException(ReflectionException):
        
        def __str__(self):
            # the original source code
            # return "it was not possible to open the file represented by: %s" % (self.message)
            # but there is no `UnableToOpenFileException.message`
            return "Could not find either the specified file or provider. Check your spelling"
