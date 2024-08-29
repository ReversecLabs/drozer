import shutil
import os
from urllib.error import HTTPError

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
        self._parser.add_argument("--latest", "-l", action="store_true", help="for use with set_apk, download the lates drozer agent from WithSecureLabs repository")
        self._parser.add_argument("--file", "-f", default=None, help="for use with set_apk, set a local file as the base for custom drozer agents")
        self._parser.add_argument("--version", "-v", default=None, help="for use with set_apk, specify the apk version to install")
        self._parser.add_argument("--url", "-u", default=None, help="for use with set_apk, download apk from url")

    def do_interactive(self, arguments):
        presets = {
            "red":      (android.permissions, [], "drozer_red", "red"),
            "purple":   ([
                            "android.permissions.INTERNET",
                            "android.permission.SYSTEM_ALERT_WINDOW",
                            "android.permission.FOREGROUND_SERVICE"
                         ], [], "drozer_purple", "purple")
        }

        """build a drozer Agent with an interactive cli"""
        options_tree = [
            OT("standard-agent"),
            OT("rogue-agent")
        ]
        # agent_type = FancyBase.choose_fill(options_tree, strict=True, head="Select drozer agent type",
        #                                    max_options=len(options_tree))

        base_apk = Configuration.library("standard-agent")
        if base_apk is None:
            print("Could not find base apk, has it been set with \"set-apk\"")
            return
        packager = builder.Packager.init_from_folder(base_apk)

        permissions = set(packager.get_manifest_file().permissions())
        security_permissions = set(packager.get_manifest_file().security_permissions())

        built = None
        name = None
        theme = None
        port = 31415

        print("set drozer options:\n")
        while True:
            options_tree = [  # maps must be re-created to be consumed again :c
                OT("add", map(lambda x: OT(x.split('.')[-1]), android.permissions)),
                OT("remove", map(lambda x: OT(x.split('.')[-1]), permissions)),
                OT("preset", [OT("red"), OT("purple")]),
                OT("define"),
                OT("list", [OT("set"), OT("all")]),
                OT("set", [OT("name"),
                           OT("theme", [OT("purple"), OT("red"), OT("green"), OT("blue")]),
                           OT("port")]),
                OT("config"),
                OT("build"),
                OT("help"),
                OT("exit")
            ]

            choice = (FancyBase.choose_fill(options_tree)
                      .split(' '))
            num_segments = len(choice)

            help_str = """"
            add PERMISSION_NAME     add permission to manifest
            define PERMISSION_NAME PROTECTION_LEVEL
                                    define security permission
            remove PERMISSION_NAME  remove permission from manifest
            list all                list all available permissions
            list set                list all set permissions
            set name NAME           set the package name of the output apk
            set theme THEME         set the application theme
            set port PORT           set the default listening port for drozer server
            config                  print currently set configuration
            build [OUTPUT]          build the apk with an optional name
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
                        permissions.append(perm_full_name)
                    else:
                        print("permission " + perm_full_name + " is not valid")
                case "preset":
                    if num_segments == 1:
                        print("preset requires a value")
                        continue
                    try:
                        preset = presets[choice[1].lower()]
                        permissions, security_permissions, name, theme = preset
                    except KeyError:
                        print(f"unknown preset {choice[1]}")
                        continue
                case "remove":
                    if num_segments == 1:
                        print("permission name required after \"remove\"")
                        continue
                    perm_full_name = "android.permission." + choice[1]
                    try:
                        permissions.remove(perm_full_name)
                    except ValueError:
                        pass
                case "define":
                    if num_segments < 3:
                        print("define requires two arguments")
                        pass
                    security_permissions.append((choice[1], choice[2]))
                case "list":
                    if num_segments == 1:
                        print("list requires a option (all, set)")
                        continue
                    match choice[1]:
                        case "all":
                            print("android permissions:\n" + '\n'.join(android.permissions))
                        case "set":
                            print("set permissions:\n" + '\n'.join(permissions))
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
                    print("\n".join(map(lambda x: f"\t{x}", permissions)))
                    print("security permission:")
                    print("\n".join(map(lambda x: f"\t{x[0]}\t{x[1]}", security_permissions)))
                case "build":
                    built = self.build_std(packager, permissions=permissions, name=name, theme=theme)
                    out_name = choice[1] if num_segments > 1 else "."
                    out = shutil.copy(built, out_name)
                    print("Done:", out)
                case "exit":
                    break
        print("cleaning up working directory...")
        packager.close()

    def do_build(self, arguments):
        """build a drozer Agent"""

        source = "rogue-agent" if (arguments.rogue or arguments.no_gui) else "standard-agent"
        base_apk = Configuration.library("standard-agent")
        if base_apk is None:
            print("Could not find base apk, has it been set with \"set-apk\"")
            return
        packager = builder.Packager.init_from_folder(base_apk)

        define_permission = set(map(lambda x: tuple(x.split(':', 1)), arguments.define_permission))\
            if arguments.define_permission is not None else\
            None
        built = self.build_std(packager, permissions=set(arguments.permission), define_permission=define_permission,
                               name=arguments.name, theme=arguments.theme)

        if arguments.out is not None:
            out = shutil.copy(built, arguments.out)
        else:
            out = shutil.copy(built, ".")
        packager.close()
        print("Done:", out)

    @staticmethod
    def build_std(packager, permissions=None, define_permission=None, name=None, theme=None):
        permissions = permissions or set()
        defined_permissions = define_permission or set()

        # ensure minimal permissions
        permissions.add("com.android.permissions.Internet")
        permissions.add("com.withsecure.dz.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION")
        defined_permissions.add(("com.withsecure.dz.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION", "signature"))

        m_ver = packager.get_apktool_file()['versionInfo']['versionName']
        c_ver = meta.version.__str__()

        if m_ver != c_ver:
            print("Version Mismatch: Consider updating your build(s)")
            print("Agent Version: %s" % m_ver)
            print("drozer Version: %s" % c_ver)

        man = packager.get_manifest_file()
        for p in permissions:  # add our perms
            man.add_permission(p)

        for permission_name, protection_level in defined_permissions:
            man.define_permission(permission_name, protection_level)

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

    def do_set_apk(self, arguments):
        """set the base apk for use with build commands"""

        out_path = os.path.join(Configuration.library_path(), "standard-agent")
        if arguments.file is not None:
            self._set_apk(arguments.file, out_path)
        elif arguments.url is not None or arguments.version is not None or arguments.latest:
            if arguments.url is not None:
                url = arguments.url
            elif arguments.version is not None:
                url = f"{Configuration._ws_dz_agent_url}download/{arguments.version}/drozer-agent.apk"
            else:
                url = f"{Configuration.ws_dz_agent_url}latest/download/drozer-agent.apk"

            self._download_apk(url, out_path)
        else:
            print("You must specify an apk with a local file, url, or use the latest flag")
    
    @classmethod
    def _download_apk(cls, source, out_path):
        with TemporaryDirectory() as tmp:
            apk_path = os.path.join(tmp, "agent.apk")

            print(f"Downloading latest apk from: {source}")

            try:
                request = urlopen(source)
            except HTTPError as e:
                if e.code == 404:
                    print(f"Release does not appear to exist, if you specified a custom version or url verify that it exists")
                else:
                    print(f"Unexpected HTTP error occurred, verify you can access the repository at: {source}")
                raise e

            with open(apk_path, "wb") as f:
                f.write(request.read())
            print("Download finished")
            
            cls._set_apk_from_tmp(apk_path, out_path, tmp)
            print("Cleaning up working directory")
        print("done!")
    
    @classmethod
    def _set_apk(cls, apk_path, out_path):
        with TemporaryDirectory as tmp:
            cls._set_apk_from_tmp(apk_path, out_path, tmp)

    @classmethod
    def _set_apk_from_tmp(cls, apk_path, out_path, tmp):
        unpack_path = os.path.join(tmp, "agent")
        print("Unpacking apk")

        try:
            builder.Packager.unpack_apk(apk_path, unpack_path)
        except Exception as e:
            print("Unable to unpack apk, it may be corrupt")
            raise e

        print("Unpack finished")

        p = builder.Packager.init_from_tmp_folder(tmp)

        man = p.get_manifest_file()  # clear all uses-perms and perms from manifest
        man.remove_all_perms()
        man.write()

        if os.path.exists(out_path):
            print("Removing existing agent base")
            shutil.rmtree(out_path)
        print("Copying to library, this may take some time...")
        shutil.copytree(unpack_path, out_path)
