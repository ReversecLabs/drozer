from reversec.common import cli, path_completion

from drozer import util
from drozer.server import dz, uploader
from drozer.ssl.provider import Provider

import sys

class Server(cli.Base):
    """
    drozer console COMMAND [OPTIONS]
    
    Starts a new drozer Server, or runs utilities to interact with a running
    Server.

    The drozer Server accepts connections from agents, and routes sessions
    from your console to those agents. It also exposes an HTTP server and TCP
    streams to assist you in deploying payloads to devices.
    """
    
    def __init__(self):
        cli.Base.__init__(self)
        
    def do_delete(self, arguments):
        """delete a resource from the drozer Server"""
        
        arguments.server = util.parse_server(arguments.server)
        if arguments.ssl != None and arguments.ssl == []:
            arguments.ssl = Provider().get_keypair("drozer-server")
        
        if uploader.delete(arguments, arguments.resource):
            sys.stdout.write("Success\n")
        else:
            sys.stdout.write("Failed\n")

    def args_for_delete(self):
        self._parser.add_argument("resource", help="specify a resource path on the drozer Server")
        self._parser.add_argument("--credentials", default=None, nargs=2, metavar=("username", "password"), help="add a username/password pair that can be used to upload files to the server")
        self._parser.add_argument("--server", default=None, metavar="HOST[:PORT]", help="specify the address and port of the drozer server")
        self._parser.add_argument("--ssl", action=util.StoreZeroOrTwo, help="enable SSL, optionally specifying the key and certificate", nargs="*")
    
    def do_start(self, arguments):
        """start a drozer Server"""
        
        dz.serve(arguments)
    
    def args_for_start(self):
        self._parser.add_argument("--credentials", action="append", default=[], nargs=2, metavar=("username", "password"), help="add a username/password pair that can be used to upload files to the server")
        self._parser.add_argument("--ping-interval", default=15, metavar="SECS", type=int, help="the interval at which to ping connected agents")
        self._parser.add_argument("--port", default=31415, metavar="PORT", type=int, help="specify the port on which to bind the server")
        self._parser.add_argument("--ssl", action=util.StoreZeroOrTwo, help="enable SSL, optionally specifying the key and certificate", nargs="*")
    
    def do_upload(self, arguments):
        """upload a resource to the drozer Server"""
        
        arguments.server = util.parse_server(arguments.server)
        if arguments.ssl != None and arguments.ssl == []:
            arguments.ssl = Provider().get_keypair("drozer-server")
        
        if uploader.upload(arguments, arguments.resource, open(arguments.file).read(), magic=arguments.magic):
            sys.stdout.write("Success\n")
        else:
            sys.stdout.write("Failed\n")
    
    def args_for_upload(self):
        self._parser.add_argument("resource", help="specify a resource path on the drozer Server")
        self._parser.add_argument("file", help="specify a file to upload to the drozer Server")
        self._parser.add_argument("--magic", help="specify a magic byte for the resource")
        self._parser.add_argument("--credentials", default=None, nargs=2, metavar=("username", "password"), help="add a username/password pair that can be used to upload files to the server")
        self._parser.add_argument("--server", default=None, metavar="HOST[:PORT]", help="specify the address and port of the drozer server")
        self._parser.add_argument("--ssl", action=util.StoreZeroOrTwo, help="enable SSL, optionally specifying the key and certificate", nargs="*")
        
    def get_completion_suggestions(self, action, text, line, **kwargs):
        if action.dest == "server":
            return ["localhost:31415"]
        elif action.dest == "file":
            return path_completion.complete(text)
        elif action.dest == "resource":
            return ["/view.jsp"]
            
