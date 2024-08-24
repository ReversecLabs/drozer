import shutil
import os

from WithSecure.common.cli_fancy import *
from drozer import android, meta
from drozer.agent import builder, manifest
from drozer.configuration import Configuration
from urllib.request import urlopen
from tempfile import TemporaryDirectory

class AgentManager(FancyBase):
    """
    drozer agent COMMAND [OPTIONS]

    A utility for building custom drozer Agents.
    """

    def __init__(self):
        FancyBase.__init__(self)

        self._parser.add_argument("--rogue", action="store_true", default=False, help="create a rogue agent with no GUI")
        self._parser.add_argument("--no-gui", action="store_true", default=False, help="deprecated: rather use --rogue. create an agent with no GUI")
        self._parser.add_argument("--granular", action="store_true", default=False, help="don't request all permissions when building GUI-less agent")
        self._parser.add_argument("--permission", "-p", nargs="+", help="add permissions to the Agent manifest")
        self._parser.add_argument("--define-permission", "-d", metavar="name:protectionLevel", nargs="+", help="define a permission and protectionLevel in the Agent manifest")
        self._parser.add_argument("--server", default=None, metavar="HOST[:PORT]", help="specify the address and port of the drozer server")
        self._parser.add_argument("--name", "-n", default=None, help="set package name to allow multiple instances")
        self._parser.add_argument("--theme", "-t", default=None, help="set app theme (red/blue/purple)")
        self._parser.add_argument("--out", "-o", default=None, help="set output file")
        self._parser.add_argument("--file", "-f", default=None, help="apk file for use with set_apk")
        self._parser.add_argument("--version", "-v", default=None)

    def do_interactive(self, arguments):
        options_tree = [
            OT("standard-agent"),
            OT("rogue-agent")
        ]
        agent_type = FancyBase.choose_fill(options_tree, strict=True, head="Select drozer agent type",
                                           max_options=len(options_tree))

        packager = builder.Packager.init_from_folder(Configuration.library(agent_type))
        permisions = packager.get_manifest_file().permissions()

        built = None
        name = None
        theme = None
        port = 31415

        print("set drozer options:\n")
        while True:
            options_tree = [  # maps must be re-created to be consumed again :c
                OT("add", map(lambda x: OT(x.split('.')[-1]), android.permissions)),
                OT("remove", map(lambda x: OT(x.split('.')[-1]), permisions)),
                OT("list", [OT("set"), OT("all")]),
                OT("set", [OT("name"),
                           OT("theme", [OT("purple"), OT("red"), OT("green"), OT("blue")]),
                           OT("port")]),
                OT("config"),
                OT("build"),
                OT("help"),
                OT("exit")
            ]

            if built is not None:
                options_tree += [
                    OT("copy")
                ]

            choice = (FancyBase.choose_fill(options_tree)
                      .split(' '))
            num_segments = len(choice)

            help_str = """"
            add PERMISSION_NAME     add permission to manifest
            remove PERMISSION_NAME  remove permission from manifest
            list all                list all available permissions
            list set                list all set permissions
            set name NAME           set the package name of the output apk
            set theme THEME         set the application theme
            set port PORT           set the default listening port for drozer server
            config                  print currently set configuration
            build                   build the apk
            copy OUTPUT             copy a built apk to OUTPUT
            exit                    exit tool
            """

            match choice[0].lower():
                case "help":
                    print(help_str)
                case "add":
                    if num_segments == 1:
                        print("permission name required after \"add\"")
                        continue
                    perm_full_name = "android.permission." + choice[1]
                    if perm_full_name in android.permissions:
                        permisions.append(perm_full_name)
                    else:
                        print("permission " + perm_full_name + " is not valid")
                case "remove":
                    if num_segments == 1:
                        print("permission name required after \"remove\"")
                        continue
                    perm_full_name = "android.permission." + choice[1]
                    try:
                        permisions.remove(perm_full_name)
                    except ValueError:
                        pass
                case "list":
                    if num_segments == 1:
                        print("list requires a option (all, set)")
                        continue
                    match choice[1]:
                        case "all":
                            print("android permissions:\n" + '\n'.join(android.permissions))
                        case "set":
                            print("set permissions:\n" + '\n'.join(permisions))
                case "set":
                    if num_segments < 3:
                        print("set requires a name and value")
                    match choice[1]:
                        case "name":
                            name = choice[2]
                            print(f"name => {choice[2]}")
                        case "theme":
                            theme = choice[2]
                            print(f"theme => {choice[2]}")
                        case "port":
                            try:
                                int(choice[2])
                                packager.get_config_file().put("server-port", choice[2])
                                print(f"port => {choice[2]}")
                            except ValueError:
                                print("port must be an integer")
                        case _:
                            print(f"unrecognised key \"{choice[1]}\"")
                case "config":
                    print("---Drozer Configuration---")
                    if name is not None:
                        print(f"package name: {name}")
                    if theme is not None:
                        print(f"package theme: {theme}")
                    print(f"default port: {port}")
                    print("set permissions:")
                    print("\n".join(map(lambda x: "\t"+x, permisions)))
                case "build":
                    built = self.build_std(packager, permissions=permisions, name=name, theme=theme)
                    print("Done:", built)
                case "exit":
                    break
                case "copy":
                    if built is None:
                        print("apk must be built before copy can be used")
                        continue
                    if num_segments == 1:
                        print("copy requires an output directory")
                        continue
                    out = shutil.copy(built, choice[1])
                    print(f"copied to: {out}")
        print("cleaning up working directory...")
        packager.close()

    def do_build(self, arguments):
        """build a drozer Agent"""

        source = "rogue-agent" if (arguments.rogue or arguments.no_gui) else "standard-agent"
        packager = builder.Packager.init_from_folder(Configuration.library("standard-agent"))

        define_permission = list(map(lambda x: tuple(x.split(':', 1)), arguments.define_permission))\
            if arguments.define_permission is not None else\
            []
        built = self.build_std(packager, permissions=arguments.permission, define_permission=define_permission, name=arguments.name, theme=arguments.theme)

        if arguments.out is not None:
            out = shutil.copy(built, arguments.out)
        else:
            out = shutil.copy(built, ".")
        print("Done:", out)
        packager.close()

    @staticmethod
    def build_std(packager, permissions=None, define_permission=None, name=None, theme=None):
        permissions = permissions or []
        defined_permissions = define_permission or []

        m_ver = packager.get_apktool_file()['versionInfo']['versionName']
        c_ver = meta.version.__str__()

        if m_ver != c_ver:
            print("Version Mismatch: Consider updating your build(s)")
            print("Agent Version: %s" % m_ver)
            print("drozer Version: %s" % c_ver)

        man = packager.get_manifest_file()
        permissions_in_manifest = man.permissions()
        for p in permissions_in_manifest:  # remove unwanted perms
            if p not in permissions:
                man.remove_permission(p)
        for p in permissions:  # add our perms
            if p not in permissions_in_manifest:
                man.add_permission(p)

        for name, protectionLevel in defined_permissions:
            man.define_permission(name, protectionLevel)

        if name is not None:
            man.set_name(name)

        if theme is not None:
            packager.get_config_file().put("theme", theme)

        return packager.package()

    def build_rogue(self, packager, server=None, granular=False):
        if server is not None:
            packager.get_config_file().put_server(server)

        if not granular:
            permissions = set(android.permissions)
        else:
            permissions = set([])
        pass

    _ws_dz_agent_url = "https://github.com/WithSecureLabs/drozer-agent/releases/"

    def do_set_apk(self, arguments):
        out_path = Configuration.library_unchecked("standard-agent")
        if arguments.file is not None:
            self._set_apk(arguments.file, out_path)
        else:
            if arguments.version is not None:
                url = f"{self._ws_dz_agent_url}/download/{arguments.version}/drozer-agent.apk"
            else:
                url = f"{self._ws_dz_agent_url}latest/download/drozer-agent.apk"

            self._download_apk(url, out_path, version=arguments.version)
    
    @classmethod
    def _download_apk(cls, source, out_path, version=None):
        with TemporaryDirectory() as temp:
            apk_path = os.path.join(temp, "agent.apk")
            unpack_path = os.path.join(temp, "standard-agent")

            print(f"downloading latest apk from: {source}")
            request = urlopen(source)
            with open(apk_path, "wb") as f:
                f.write(request.read())
            print("Download finished")
            
            cls._set_apk_from_tmp(apk_path, out_path, unpack_path)

            print("done!")
    
    @classmethod
    def _set_apk(cls, apk_path, out_path):
        with TemporaryDirectory as tmp:
            cls._set_apk_from_tmp(apk_path, out_path, tmp)

    @classmethod
    def _set_apk_from_tmp(cls, apk_path, out_path, tmp_path):
        print("unpacking apk")
        builder.Packager.unpack_apk(apk_path, tmp_path)
        print("unpack finished")
        if os.path.exists(out_path):
            shutil.rmtree(out_path)
        print("copying to library, this may take some time...")
        shutil.copytree(tmp_path, out_path)
