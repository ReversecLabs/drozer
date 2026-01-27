import functools
import urllib

from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer

from pysolar.reflection import ReflectionException

from drozer.modules import common, Module

class WebContentResolver(Module, common.PackageManager, common.Provider):

    name = "Start a web service interface to content providers."
    description = "Start a Web Service interface to Content Providers. This allows you to use web application testing capabilities and tools to test content providers."
    examples = """dz> run auxiliary.webcontentresolver --port 8080

    WebContentResolver started on port 8080.
    Ctrl+C to Stop"""
    author = "Nils (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["auxiliary"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("-p", "--port", default=8080, help="the port to start the WebContentResolver on")
    
    def execute(self, arguments):
        try:
            server = HTTPServer(('', int(arguments.port)), functools.partial(Handler, self))

            print("WebContentResolver started on port " + str(arguments.port) + ".")
            print("Ctrl+C to Stop")

            server.serve_forever()
        except KeyboardInterrupt:
            print("Stopping...\n")

            server.socket.close()

class Handler(BaseHTTPRequestHandler):

    header = """<html><head><title>drozer WebContentResolver</title><style type="text/css">body { font-family: "Lucida Grande", Verdana, Arial, Helvetica, sans-serif; font-size: 12px; } table { font-size: inherit; }</style></head><body><h1>drozer WebContentResolver</h1>\n"""
    footer = """</body></html>"""

    def __init__(self, module, *args, **kwargs):
        self.module = module

        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

        # grab the requested path, and parse it
        url = urllib.parse.urlparse(self.path)
        # split out the path component into an array
        path = [ x for x in url.path.split('/') if x ]
        # parse the trailing url parameters
        params = urllib.parse.parse_qs(url.query)

        try:
            if not path:
                # default behaviour: usage information
                self.wfile.write(bytes(self.header + self.usage() + self.footer, "utf-8"))
            elif path[0] == 'list':
                # if /list, produce a list of all known exported content provider uris
                output = self.__provider_list(filters=params.get('filter', [None])[0], permissions=params.get('permissions', [None])[0])

                self.wfile.write(bytes(self.header + output + self.footer, "utf-8"))
            elif path[0] == 'query':
                # if /query, build a query against the specified content uri, with
                # the projection and selection
                output = self.__query(params.get('uri', [None])[0], params.get('projection', [None])[0], params.get('selection', [None])[0], params.get('selectionArgs', [None])[0], params.get('selectionSort', [None])[0])

                self.wfile.write(bytes(self.header + output + self.footer, "utf-8"))
            else:
                # if the path is not recognised, print usage information
                self.wfile.write(bytes(self.header + self.usage() + self.footer, "utf-8"))
        except ReflectionException as e:
            # handle any ReflectionExceptions here, and show the error message in the
            # user's browser - this will help them to build their query
            self.wfile.write(bytes(self.header + self.__format_exception(e) + self.footer, "utf-8"))
    
    def __eligible_path_permission(self, permissions, path):
        return permissions == None or \
            permissions.lower() == "null" and (path.getReadPermission() == None or path.getWritePermission() == None) or \
            path.getReadPermission() != None and permissions.lower() in path.getReadPermission().lower() or \
            path.getWritePermission() != None and permissions.lower() in path.getWritePermission().lower()
             
    def __eligible_provider(self, permissions, provider):
        return permissions == None or \
            permissions.lower() == "null" and (provider.readPermission == None or provider.writePermission == None) or \
            provider.readPermission != None and permissions.lower() in provider.readPermission.lower() or \
            provider.writePermission != None and permissions.lower() in provider.writePermission.lower() or \
            provider.pathPermissions != None and True in map(lambda path: self.__eligible_path_permission(permissions, path), provider.pathPermissions)

    def __format_exception(self, e):
        return "<h1>" + str(e.__class__) + "</h1><p>" + str(e) + "</p>"

    def __provider_list(self, filters=None, permissions=None):
        """
        Print out a (filtered) list of Content Providers.
        """
        
        output = """<table><tr><th>Package</th>
                               <th colspan="2">Authorities</th>
                               <th>Read permission</th>
                               <th>Write permission</th>
                               <th>Multipermission</th></tr>
                            """

        def link(path, display):
            return "<a href='%s'>%s</a>" % (path, display)

        def linkcontent(url, display=None):
            return link("/query?uri=content://%s&projection=&selection=&selectionSort=" % url, display or url)

        def linkfilter(url, display=None):
            return link("/?filter=%s" % url, display or url)

        def linkperm(url, display=None):
            return link("/?permissions=%s" % url, display or url)

        for package in self.module.packageManager().getPackages(common.PackageManager.GET_PROVIDERS):
            
            if package.providers != None and (filters == None or filters.lower() in package.packageName.lower()):
                for provider in package.providers:

                    if self.__eligible_provider(permissions, provider):
                        # Give the general values first

                        if(not provider.exported):
                            continue
                        if(provider.authority != None):
                            authorities = provider.authority.split(";")
                        else:
                            authorities = "null"
                        output += "<tr><td>%s</td>" % linkfilter(provider.packageName)
                        output += "<td colspan='2'>%s</td>" % "<br/>".join([linkcontent(a) for a in authorities])
                        output += "<td>%s</td>" % linkperm(provider.readPermission)
                        output += "<td>%s</td>" % linkperm(provider.writePermission)
                        output += "<td>%s</td></tr>" % provider.multiprocess

                        if provider.pathPermissions != None:
                            for permission in provider.pathPermissions:
                                if self.__eligible_path_permission(permissions, permission):
                                    output += "<tr><td>&nbsp;</td><td>&nbsp;</td>"
                                    output += "<td>%s</td>" % linkcontent("%s%s" % (authorities[0], permission.getPath()), permission.getPath())
                                    output += "<td>%s</td>" % linkperm(permission.getReadPermission())
                                    output += "<td>%s</td>" % linkperm(permission.getWritePermission())
                                    output += "<td>&nbsp;</td></tr>"
        output += "</table>"
        return output

    def __query(self, uri, projection=None, selection=None, selectionArgs=None, sortOrder=None):
        """
        Query a Content Provider, with a projection and selection passed through the
        web interface.
        """
        
        cursor = self.module.contentResolver().query(uri, projection != None and projection.split(",") or None, selection, selectionArgs != None and selectionArgs.split(",") or None, sortOrder)
        output = "<table><thead><tr>"

        if cursor != None:
            rows = self.module.getResultSet(cursor)

            for v in rows[0]:
                output += "<th>%s</th>" % v
            
            output += "</tr></thead><tbody>"
            
            for r in rows[1:]:
                output += "<tr>"
                for v in r:
                    output += "<td>%s</td>" % v
                output += "</tr>"

            output += "</tbody></table>"
            
            return output
        else:
            return "Unable to query %s." % uri

    def usage(self):
        """
        Create HTML-formatted usage information for WebContentResolver.
        """
        
        return """
<p>WebContentProvider starts a Web Service interface to access Content Providers.</p>
<p>With WebContentProvider, you can use web application testing capabilities and tools to test content providers.</p>

<h2>Usage instructions:</h2>

<ul>
<li>To access a list of exported providers (<b>n.b.</b>, may take a few minutes):
  <a href="http://localhost:%d/list">http://localhost:%s/list</a></li>

<li>To access a particular provider:
  http://localhost:%d/query?uri=<b>&lt;uri&gt;</b>&projection=<b>&lt;projection&gt;</b>&selection=<b>&lt;selection&gt;</b>&selectionArgs=<b>&lt;selectionArgs&gt;</b>&sortOrder=<b>&lt;sortOrder&gt;</b></li>
</ul>
""" % (self.server.server_port, self.server.server_port, self.server.server_port)
