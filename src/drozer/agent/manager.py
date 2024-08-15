import shutil

from WithSecure.common.cli_fancy import *
from drozer import android, meta
from drozer.agent import builder, manifest

class AgentManager(cli.Base):
    """
    drozer agent COMMAND [OPTIONS]
    
    A utility for building custom drozer Agents.
    """
    
    def __init__(self):
        cli.Base.__init__(self)
        
        self._parser.add_argument("--rogue", action="store_true", default=False, help="create a rogue agent with no GUI")
        self._parser.add_argument("--no-gui", action="store_true", default=False, help="deprecated: rather use --rogue. create an agent with no GUI")
        self._parser.add_argument("--granular", action="store_true", default=False, help="don't request all permissions when building GUI-less agent")
        self._parser.add_argument("--permission", "-p", nargs="+", help="add permissions to the Agent manifest")
        self._parser.add_argument("--define-permission", "-d", metavar="name:protectionLevel", nargs="+", help="define a permission and protectionLevel in the Agent manifest")
        self._parser.add_argument("--server", default=None, metavar="HOST[:PORT]", help="specify the address and port of the drozer server")
        self._parser.add_argument("--name", "-n", default=None, help="set package name to allow multiple instances")
        self._parser.add_argument("--theme", "-t", default=None, help="set app theme (red/blue/purple)")
        self._parser.add_argument("--out", "-o", default=None, help="set output file")

    def do_build(self, arguments):
        """build a drozer Agent"""

        source = (arguments.rogue or arguments.no_gui) and "rogue-agent" or "standard-agent"
        packager = builder.Packager()
        packager.unpack(source)
        
        if arguments.rogue or arguments.no_gui:
            if arguments.server is not None:
                packager.get_config_file().put_server(arguments.server)
            
            if not arguments.granular:
                permissions = set(android.permissions)
            else:
                permissions = set([])
        else:
            permissions = set([])
        
        if arguments.permission is not None:
            permissions = permissions.union(arguments.permission)

        defined_permissions = {}
        if arguments.define_permission is not None:
            defined_permissions = dict(map(lambda x: x.split(':'), arguments.define_permission))

        # add extra permissions to the Manifest file
        m = packager.get_manifest_file()

        m_ver = packager.get_apktool_file()['versionInfo']['versionName']
        c_ver = meta.version.__str__()
        
        if m_ver != c_ver:
            print("Version Mismatch: Consider updating your build(s)")
            print("Agent Version: %s" % m_ver)
            print("drozer Version: %s" % c_ver)

        for p in permissions:
            m.add_permission(p)

        for name, protectionLevel in defined_permissions.items():
            m.define_permission(name, protectionLevel)

        if arguments.name is not None:
            m.set_name(arguments.name)

        if arguments.theme is not None:
            packager.get_config_file().put("theme", arguments.theme)

        built = packager.package()

        if arguments.out is not None:
            out = shutil.copy(built, arguments.out)
            print("Done:", out)
        else:
            print("Done:", built)
