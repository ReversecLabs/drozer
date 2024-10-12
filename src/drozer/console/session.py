import os
import re
import shlex
import sys
import textwrap
import traceback
import random

from pysolar.api.protobuf_pb2 import Message
from pysolar.api.transport.exceptions import ConnectionError
from pysolar.reflection import Reflector

from WithSecure.common import cmd_ext as cmd
from WithSecure.common import console
from WithSecure.common.stream import ColouredStream, DecolouredStream
from WithSecure.common.text import wrap

from drozer import meta
from drozer.configuration import Configuration
from drozer.console import clean
from drozer.console.sequencer import Sequencer
from drozer.modules import collection, common, loader, Module
from drozer.repoman import ModuleManager

class Session(cmd.Cmd):
    """
    drozer: Android Security Assessment Framework

    Type `help COMMAND` for more information on a particular command, or `help MODULE` for a particular module.
    """

    def __init__(self, server, session_id, arguments):
        cmd.Cmd.__init__(self)
        self.__base = ""
        self.__has_context = None
        self.__module_pushed_completers = 0
        self.__permissions = None
        self.__server = server
        self.__session_id = bytes(session_id, encoding='utf-8')
        self.__onecmd = arguments.onecmd
        self.active = True
        self.aliases = { "l": "list", "ls": "list", "ll": "list" }
        self.intro = "drozer Console (v%s)" % meta.version
        self.history_file = os.path.sep.join([os.path.expanduser("~"), ".drozer_history"])
        self.modules = collection.ModuleCollection(loader.ModuleLoader())
        self.prompt = "dz> "
        self.reflector = Reflector(self)
        if hasattr(arguments, 'no_color') and not arguments.no_color:
            self.stdout = ColouredStream(self.stdout)
            self.stderr = ColouredStream(self.stderr)
        else:
            self.stdout = DecolouredStream(self.stdout)
            self.stderr = DecolouredStream(self.stderr)

        m = Module(self)
        if m.has_context() and self.reflector.resolve("android.os.Build$VERSION").SDK_INT >= 24:
            dataDir = str(m.getContext().getDataDir().getCanonicalPath().native())
        elif m.has_context():
            dataDir = str(m.getContext().getApplicationInfo().dataDir)
        else:
            dataDir = str(m.new("java.io.File", ".").getCanonicalPath().native())
        self.variables = {  'PATH': dataDir +'/bin:/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin',
                            'WD': dataDir }
        
        self.__load_variables()

        if arguments.onecmd == None:
            self.__print_banner()

    def completefilename(self, text, line, begidx, endidx):
        """
        Provides readline auto-completion for filenames on the local (Console)
        file system.
        """

        return common.path_completion.on_console(text)

    def completemodules(self, text):
        """
        Provides readline auto-completion for drozer module names.
        """

        modules = self.modules.all(permissions=self.permissions(), prefix=self.__base)
        
        if self.__base == "":
            modules = list(filter(lambda m: m.startswith(text), modules))
        elif text.startswith("."):
            modules = list(filter(lambda m: m.startswith(text[1:]), modules))
        else:
            modules = map(lambda m: m[len(self.__base):], list(filter(lambda m: m.startswith(self.__base + text), modules)))
        
        #if len(modules) == 1 and text == modules[0]:
        #    return []

        return modules

    def completenamespaces(self, text):
        """
        Provides readline auto-completion for drozer namespaces.
        """

        if self.__base == "":
            return list(filter(lambda m: m.startswith(text), self.__namespaces()))
        elif text.startswith("."):
            namespaces = self.__namespaces(global_scope=True)
            namespaces.add("..")

            return map(lambda m: "." + m, list(filter(lambda m: m.startswith(text[1:]), namespaces)))
        else:
            return map(lambda m: m[len(self.__base):], list(filter(lambda m: m.startswith(self.__base + text), self.__namespaces())))

    def context(self):
        if self.has_context():
            return self.reflector.resolve("com.WithSecure.dz.Agent").getContext()
        else:
            return None
        
    def do_cd(self, args):
        """
        usage: cd NAMESPACE

        The namespace is taken as relative to the current location in the module tree:

            dz> cd information
            dz#information> cd native
            dz#information.native>

        To specify an absolute path, prefix it with a period character:

            dz#information.native> cd .package
            dz#package>

        It is still possible to run commands from other namespaces, by specifying the absolute path (prefixed by a period) to the `run` command:

            dz> cd package
            dz#package> run .activity.info

        Passing an empty string to `cd` will switch back to the root namespace:

            dz#information.native> cd
            dz>

        Passing '..' will move up one level:

            dz#information.native> cd ..
            dz#information>
        """
        argv = shlex.split(args, comments=True)

        if len(argv) == 1 and (argv[0] == "-h" or argv[0] == "--help"):
            self.do_help("cd")
            return

        if len(argv) == 0:
            argv.append("")

        if not self.__setBase(argv[0]):
            self.stderr.write("invalid path: %s\n"%argv[0])

    def complete_cd(self, *args):
        """
        Provides readline auto-completion for the `cd` command, suggesting
        namespaces.
        """

        return self.completenamespaces(args[0])

    def do_clean(self, args):
        """
        usage: clean
        
        Cleans APK and DEX files from drozer's cache.
        
        During normal operation, drozer uploads a number of APK files to your device, and extracts the DEX bytecode from others already on your device. This can start to consume a large amount of space, particularly if you are developing drozer modules.
        
        The `clean` command removes all of these cached files for you.
        
        drozer will automatically re-upload any files that it needs as you continue to use it.
        """

        files = clean.clean(self.reflector)
        
        self.stdout.write("Removed %d cached files.\n" % files)

    def do_contributors(self, args):
        """
        Display a list of drozer contributors.
        """
        
        argv = shlex.split(args, comments=True)
        
        if len(argv) == 1 and (argv[0] == "-h" or argv[0] == "--help"):
            self.do_help("contributors")
            return

        self.stdout.write("Core Contributors:\n")
        for contributor in [
            'WithSecure Labs (@withconsulting)', 
            'Ken Gannon (@Yogehi)', 
            'William Ben Embarek (@willbenem)', 
            'Miłosz Gaczkowski (@cyberMilosz)', 
            'Luander (luander.r@samsung.com)', 
            'Rodrigo Chiossi (r.chiossi@samsung.com)'
            ]:
            self.stdout.write("  %s\n"%contributor)

        self.stdout.write("\nModule Contributors:\n")
        for contributor in self.modules.contributors():
            self.stdout.write("  %s\n"%contributor)

    def do_exit(self, args):
        """
        Terminate your drozer session.
        """
        
        try:
            if self.active:
                self.__server.stopSession(self.__session_id)
                
                self.active = False
    
            return True
        except ConnectionError:
            self.active = False
            
            return True

    def do_help(self, args):
        """
        usage: help [COMMAND OR MODULE]

        Displays help information.
        """
        argv = shlex.split(args, comments=True)

        if len(argv) == 1 and (argv[0] == "-h" or argv[0] == "--help"):
            self.do_help("help")
            return

        if len(argv) > 0:
            if self.__module_name(argv[0]) in self.modules.all(permissions=self.permissions()) or self.__module_name("." + argv[0]) in self.modules.all(permissions=self.permissions()):
                self.do_run(" ".join([argv[0], "--help"]))
            else:
                try:
                    func = getattr(self, 'help_' + argv[0])
                except AttributeError:
                    try:
                        doc = getattr(self, 'do_' + argv[0]).__doc__
                        if doc:
                            self.stdout.write("%s\n" % wrap(textwrap.dedent(str(doc)).strip(), width=console.get_size()[0]))
                            return
                    except AttributeError:
                        pass
                    self.stdout.write("%s\n" % str(self.nohelp) % (argv[0],))
                    return
                func()
        else:
            cmd.Cmd.do_help(self, args)

    def complete_help(self, *args):
        """
        Provides readline auto-completion for the `help` command, offering
        commands, modules and topics.
        """

        commands = set(self.completenames(args[0]))
        modules = set(self.completemodules(args[0]))
        topics = set(a[5:] for a in self.get_names() if a.startswith('help_' + args[0]))

        return list(commands | modules | topics)

    def do_list(self, args):
        """
        usage: list [FILTER]

        Displays a list of the available modules, optionally filtered by name.

        Examples:

            dz> list
            activity.forintent
            activity.info
            ... snip ...
            dz> list debug
            information.debuggable
            dz>
        
        optional arguments:
        
          --unsupported         include a list of the modules that are not available on your device
        """
        argv = shlex.split(args, comments=True)

        if len(argv) == 1 and (argv[0] == "-h" or argv[0] == "--help"):
            self.do_help("list")
            return
        
        include_unsupported = False
        if "--unsupported" in argv:
            argv.remove("--unsupported")
            include_unsupported = True

        if "--all" in argv:
            argv.remove("--all")
            include_unsupported = True
        
        term = len(argv) > 0 and argv[0] or None
        
        s_modules = list(self.modules.all(contains=term, permissions=self.permissions(), prefix=self.__base))
        
        if include_unsupported:
            u_modules = list(filter(lambda m: not m in s_modules, self.modules.all(contains=term, permissions=None, prefix=self.__base)))
        else:
            u_modules = []

        self.stdout.write(console.format_dict(dict(map(lambda m: [m, self.modules.get(m).name], s_modules))) + "\n")
        
        if len(u_modules) > 0:
            self.stdout.write("Unsupported Modules:\n\n")
            self.stdout.write(console.format_dict(dict(map(lambda m: [m, self.modules.get(m).name], u_modules))) + "\n")

    def do_load(self, args):
        """
        usage: load FILE

        Loads a file, and executes it as a script.
        """
        argv = shlex.split(args, comments=True)

        if len(argv) == 1 and (argv[0] == "-h" or argv[0] == "--help"):
            self.do_help("load")
            return

        if len(argv) > 0:
            try:
                Sequencer(argv).run(self)
            except KeyboardInterrupt:
                self.stderr.write("\nCaught SIGINT. Interrupt again to terminate you session.\n")
            except Exception as e:
                self.handleException(e)
        else:
            self.do_help("load")

    def complete_load(self, text, line, begidx, endidx):
        """
        Provides readline auto-completion for the `load` command, offering
        local file names.
        """

        return self.completefilename(text, line, begidx, endidx)

    def do_module(self, args):
        """
        usage: module [COMMAND]
    
        Run the drozer Module and Repository Manager.
    
        The Repository Manager handles drozer modules and module repositories.
        """
        
        ModuleManager().run(shlex.split(args, comments=True))
        self.modules.reload()
        
    def do_permissions(self, args):
        """
        usage: permissions
        
        Prints out the permissions granted to the agent being used in this session.
        """
        
        if self.has_context():
            self.stdout.write("Has ApplicationContext: YES\n")
            self.stdout.write("Available Permissions:\n")
            for permission in sorted(self.permissions()):
                if permission not in ["GET_CONTEXT", "com.WithSecure.dz.permissions.GET_CONTEXT", "com.mwr.dz.permissions.GET_CONTEXT"]:
                    self.stdout.write(" - %s\n" % (permission))
        else:
            self.stdout.write("Has ApplicationContext: NO\n")
        
    def do_run(self, args):
        """
        usage: run MODULE [OPTIONS]

        To see the options for a particular module, run `help MODULE`.
        """
        argv = shlex.split(args, comments=True)

        if len(argv) == 1 and (argv[0] == "-h" or argv[0] == "--help"):
            self.do_help("run")
            return

        if len(argv) > 0:
            try:
                module = self.__module(argv[0])
                module.push_completer = self.__push_module_completer
                module.pop_completer = self.__pop_module_completer
                
                self.__module_pushed_completers = 0
            except KeyError as e:
                self.stderr.write("unknown module: %s\n" % str(e))
                return None

            try:
                print("Attempting to run shell module")
                module.run(argv[1:])
            except KeyboardInterrupt:
                self.stderr.write("\nCaught SIGINT. Interrupt again to terminate you session.\n")
            except Exception as e:
                self.handleException(e)
            
            while self.__module_pushed_completers > 0:
                self.__pop_module_completer()
        else:
            self.do_help("run")

    def complete_run(self, text, line, begidx, endidx):
        """
        Provides readline auto-completion for the `run` command.

        If auto-completion is requested on the first token after the 'run'
        command, we offer module names. Otherwise, we delegate to the complete()
        method defined on the specified module.
        """

        _line = re.match(r"(run\s+)([^\s]*)(\s*)", line)

        # figure out where the module name starts in the string
        cmdidx = len(_line.group(1))

        if begidx == cmdidx:
            # if we are trying to autocomplete the module name, offer modules as suggestions
            return self.completemodules(text)
        else:
            # otherwise, we are trying to autocomplete some options for the module, and should
            # defer to it
            offset = len(_line.group(0))
            # we pass over the arguments for autocompletion, but strip off the command and module
            # name for simplicity
            
            #return self.__module(_line.group(2)).complete(text, line, begidx, endidx)
            return self.__module(_line.group(2)).complete(text, line[offset:], begidx - offset, endidx - offset)

    def do_shell(self, args):
        """
        usage: `! [COMMAND]` or `shell [COMMAND]`

        Execute a Linux command in the context of drozer.

        If a COMMAND is specified, this is shorthand for `run shell.exec COMMAND`. Otherwise, it will launch an interactive shell.

        Example:

            dz> ! date
            Fri Dec 21 23:59:59 GMT 2012
            dz> ! cat /etc/hosts
            127.0.0.1  localhost

        The working directory of your shell will be the drozer Agent root folder.
        """

        if len(args) > 0:
            return self.do_run(".shell.exec \"%s\"" % args)
        else:
            return self.do_run(".shell.start")
    
    def help_intents(self):
        """
        An intent is an abstract description of an operation to be performed. It can be used with app.activity.start to launch an Activity, app.broadcast.send to send it to any interested BroadcastReceiver components, and app.service.start to communicate with a background Service.
        
        An Intent provides a facility for performing late runtime binding between the code in different applications. Its most significant use is in the launching of activities, where it can be thought of as the glue between activities. It is basically a passive data structure holding an abstract description of an action to be performed.
        
        
        Intent Structure
        ----------------
        The primary pieces of information in an intent are:
        
          action: the general action to be performed
          data: the data to operate on
        
        In addition to these primary attributes, there are a number of secondary attributes that you can also include with an intent:
        
          category: gives additional information about the action to execute
          type: specifies an explicit MIME type (a MIME type) of the data
          component: specifies an explicit component class
          extras: a bundle of any additional information

        Put together, the set of actions, data types, categories, and extra data defines a language for the system allowing for the expression of phrases such as "call john smith's cell". As applications are added to the system, they can extend this language by adding new actions, types, and categories, or they can modify the behavior of existing phrases by supplying their own activities that handle them.


        Intent Formulation
        ------------------
        In drozer, intents are formulated using a set of command-line options. Some of these set a simple String in the Intent:
        
          --action ACTION
          --category CATEGORY
          --component PACKAGE COMPONENT
          --data-uri URI
          --flags FLAG [FLAG ...]
          --mimetype TYPE
        
        When specifying a component, the fully-qualified name of both the package and component must be used, for example to specify the BrowserActivity within the com.android.browser package:
        
          --component com.android.browser com.android.browser.BrowserActivity
          
        Intents can carry messages or commands inside of them in the form of extras. Applications may want to pass additional information inside of the intents they send to one another, possibly containing the data to perform a task on, or any other user-defined task to initiate from the received data.
        
        Passing the extras is a little more complex. You need to tell drozer the data type, key and value:
          
          --extra TYPE KEY VALUE
        
        drozer supports a few common types:
        
          boolean
          byte
          bytearray
          char
          double
          float
          integer
          short
          string
          parcelable(sort of)

        Bytearray intent extras can be specified as strings, base64, or hex representations, e.g.:

          --extra bytearray someKey "a very fun string"
          --extra bytearray someKey base64(c3VwZXIgZnVuIGJhc2U2NCBzdHJpbmc=)
          --extra bytearray someKey hex(616e2045585452454d454c592066756e2068657820737472696e67)

        When crafting a parcelable intent extra, the following data types are fully supported:

          Content provider URIs
          Website URIs
          Intents

        For Content provider URIs, use the standard 'content://' format of URIs

          --extra parcelable yaycontentyay content://settings/secure

        For Website URIs, use either 'http://' or 'https://' format of URIs:

          --extra parcelable yaywebsiteyay http://www.withsecure.com

        For Intents, use the 'intent://' format of URI:

          --extra parcelable yayintentyay intent://host.com?queryparameter=value#Intent;component=targetPackage/targetComponent;action=action;category=category;type=type;identifier=identifier;launchFlags=launchFlags;scheme=scheme;sourceBounds=sourceBounds;S.extraString=value;B.extraBoolean=value;b.extraByte=value;c.extraChar=value;d.extraDouble=value;i.extraInt=value;f.extraFloat=value;l.extraLong=value;s.extraShort=value;end;
        
        """
        
        self.stdout.write(wrap(textwrap.dedent(self.help_intents.__doc__).strip() + "\n\n", console.get_size()[0]))
    
    def has_context(self):
        if self.__has_context == None:
            self.__has_context = not self.reflector.resolve("com.WithSecure.dz.Agent").getContext() == None
            
        return self.__has_context == True
    
    def permissions(self):
        """
        Retrieves the set of permissions that we have in this session.
        """
        
        if self.__permissions == None and self.has_context():
            pm = self.reflector.resolve("android.content.pm.PackageManager")
            packageName = str(self.context().getPackageName())
            packageManager = self.context().getPackageManager()
            
            package = packageManager.getPackageInfo(packageName, pm.GET_PERMISSIONS)
            self.__permissions = []
            if package.requestedPermissions != None:
                requestedPermissions = map(lambda p: str(p), package.requestedPermissions)
                
                for permission in requestedPermissions:
                    #Check for PERMISSION_GRANTED
                    if (packageManager.checkPermission(str(permission), packageName) == pm.PERMISSION_GRANTED):
                        self.__permissions.append(str(permission))
            
            self.__permissions.append("com.WithSecure.dz.permissions.GET_CONTEXT")
            self.__permissions.append("com.mwr.dz.permissions.GET_CONTEXT")
            self.__permissions.append("GET_CONTEXT")
        elif self.__permissions == None:
            self.__permissions = []
        
        return self.__permissions

    def preloop(self):
        cmd.Cmd.preloop(self)

        #should we wish to change the prompt :D
        if not self.has_context():
            self.prompt = self.prompt.replace(">","-limited>")

        if(self.__onecmd):
            return

    def sendAndReceive(self, message):
        """
        Delivers a message to the Agent, and returns the response.

        If the send operation times out, or the response indicates a fatal error,
        an error message is displayed and the console terminates with a status
        code of -1.
        """

        try:
            message = self.__server.sendAndReceive(message.setSessionId(self.__session_id))
        except ConnectionError:
            self.stderr.write("We lost your drozer session.\n\n")
            self.stderr.write("For some reason the mobile Agent has stopped responding. You will need to restart it, and try again.\n\n")

            sys.exit(1)

        if message and message.type == Message.REFLECTION_RESPONSE and message.reflection_response.status == Message.ReflectionResponse.FATAL:
            self.stderr.write("We lost your drozer session.\n\n")
            self.stderr.write("The mobile Agent did not like the last message you sent it. It has terminated your session.\n\n")
            self.stderr.write("You will need to reconnect, and may need to restart the mobile Agent.\n\n")

            sys.exit(2)

        return message

    def __load_variables(self):
        """
        Load extra variables, specified in the .drozer_config file.
        """
        
        for key in Configuration.get_all_keys("vars"):
            self.variables[key] = Configuration.get("vars", key)
        
    def __module(self, key):
        """
        Gets a module instance, by identifier, and initialises it with the
        required session parameters.
        """

        module = None

        try:
            module = self.modules.get(self.__module_name(key))
        except KeyError:
            pass

        if module == None:
            try:
                module = self.modules.get(key)
            except KeyError:
                pass

        if module == None:
            raise KeyError(key)
        else:
            return module(self)

    def __module_name(self, key):
        """
        Decodes a full module identifier, given a user's input.

        This helps to find modules after the user has changed namespace.
        """

        if key.startswith("."):
            return key[1:]
        elif self.__base == "":
            return key
        else:
            return self.__base + key

    def __namespaces(self, global_scope=False):
        """
        Gets a full list of all namespace identifiers, either globally or in
        the current namespace scope.
        """

        if global_scope:
            modules = self.modules.all(permissions=self.permissions(), prefix=None)
        else:
            self.modules.all(permissions=self.permissions(), prefix=self.__base)
        
        return set(map(lambda m: self.__module("." + m).namespace(), modules))
    
    def __push_module_completer(self, completer, history_file=None):
        """
        Delegate, passed to the module, so it can add a new readline completer
        to the stack.
        """
        
        self.__module_pushed_completers += 1
        
        self.push_completer(completer, history_file)
    
    def __pop_module_completer(self):
        """
        Delegate, passed to the module, so it can add a remove a readline completer
        from the stack.
        """
        
        self.__module_pushed_completers -= 1
        
        self.pop_completer()
    
    def __print_banner(self):
        x = random.randint(0,100)
        if x == 69:
            self.__print_banner2()
        elif x == 42:
            self.__print_banner3()
        elif x == 84:
            self.__print_banner4()
        else:
            self.__print_banner1()

    def __print_banner1(self):
        print("            ..                    ..:."      )
        print("           ..o..                  .r.."      )
        print("            ..a..  . ....... .  ..nd"        )
        print("              ro..idsnemesisand..pr"         )
        print("              .otectorandroidsneme."         )
        print("           .,sisandprotectorandroids+."      )
        print("         ..nemesisandprotectorandroidsn:."   )
        print("        .emesisandprotectorandroidsnemes.."  )
        print("      ..isandp,..,rotecyayandro,..,idsnem."  )
        print("      .isisandp..rotectorandroid..snemisis." )
        print("      ,andprotectorandroidsnemisisandprotec.")
        print("     .torandroidsnemesisandprotectorandroid.")
        print("     .snemisisandprotectorandroidsnemesisan:")
        print("     .dprotectorandroidsnemesisandprotector.")
        print("")

    # You found the easter egg!
    # What you wanted a prize or something?
    def __print_banner2(self):
        print("                     ,  ,..,                 ")
        print("                    .........,.              ")
        print("                      ..........             ")
        print("         .      ...,*//*,....                ")
        print("       ,.##./androidsnemsisandp#,,           ")
        print("    ..(%#/rotectorandroidsnemesisa/.,.       ")
        print("   .(//*ndprotectorandroidsnemesis//%/*      ")
        print("  ,#//and@@@@/protector@@@@&androidsne,,     ")
        print(" .///mes@ .. @andprote@ .. @ctorandroid#.    ")
        print("  (snemsi@@@sand&&&yay&&@@@protectorandro,   ")
        print(" ..##idsn&&&&&&&&&&&&&&/emisisandprotector,, ")
        print(" ,.#&&&&&&&&&&&&&&&&&&&#androidsnemesisandp,.")
        print(",%&&&&&&&&&&&&&&&&&&&&%/rotectorandroidsneme,")
        print(".&&&&&&&&&&&&&&&&&&&&//sisandprotectorandro/,")
        print(" .*%&&&&&&&&&&&&&&&/idsnemesisandprotector(, ")
        print("    .,.,*/androidsnemesisandprotectorand(,,  ")
        print("     ,roidsnemesisandprotectorandroidsn/.    ")
        print("   .,emisisandprotectorandroidsnemsisan(...**")
        print("")

    # TODO replace this with pichu
    def __print_banner3(self):
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣷⠀⣀⣤⡆⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⣿⣿⡿⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣷⡖⠀⠀⠀")
        print("⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⡿⢛⣿⢿⣿⡟⠋⠀⠀⠀⠀")
        print("⣿⣿⣿⣶⣦⣄⡀⠀⠀⠀⠀⠀⠀⠀⠠⣾⣿⡿⠋⠀⠈⠀⢸⣿⡇⠀⠀⠀⠀⠀")
        print("⢻⣿⣿⣟⠻⣿⣿⣷⣦⣀⠀⠀⠀⠀⠀⠻⠉⠀⠀⠀⠀⠀⢸⣿⡇⠀⠀⠀⠀⠀")
        print("⢸⣿⣟⠿⠀⠀⠉⠛⢿⣿⡇⠀⠀⠀⠀⠈⡀⠀⠀⠀⠀⠀⣿⣿⠇⠀⠀⠀⠀⠀")
        print("⠀⣿⣿⡄⠀⠀⠀⠀⠀⠈⡇⢀⠠⠀⠀⠀⠁⠀⠀⡀⠀⠠⠟⠛⠀⠀⠀⠀⠀⠀")
        print("⠀⠸⣿⣷⡀⠀⠀⠀⠀⠀⠔⠁⠀⠀⠀⢀⢀⡀⠀⠈⠢⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⢻⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣴⣿⠀⠔⠀⡄⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠻⠿⠇⠒⠈⡄⠀⠀⠀⠀⠀⠀⠈⡉⠁⠀⠀⠀⠁⠀⠀⠄⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⡇⠀⡠⠴⠄⠀⢀⠔⠀⠀⠀⠄⠌⠀⠀⡁⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⢁⣀⡀⠀⡀⠙⠄⠀⢀⠀⣠⣾⠄⣤⠊⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⠄⡑⠁⠂⠀⣈⣥⣾⡿⢿⠀⠀⢄⠀⢀⣠⣤⣤⣴⣦")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⡀⠈⠀⠋⠿⠀⠀⠀⠄⠀⠌⣴⣿⣿⣿⣿⣿⣿")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠃⠀⠀⠀⠀⠀⠉⠀⠏⠀⠀⠈⠉⠙⠋")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡔⠈⠂⠄⠀⠀⠀⠀⡠⠀⠀⠀⠀⠀⠀⠀⠀")
        print("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠄⢀⣀⡰⠀⠂⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀")
        print("")

    def __print_banner4(self):
        if console.get_size()[0] < 100:
            self.__print_banner1()
            return

        print("                                                        ▓▓████████████░░▓▓██")
        print("            ~dozer~                                   ▓▓░░░░░░░░░░▒▒░░░░░░▒▒▓▓")
        print("                                                      ██▓▓████▓▓██████▓▓▓▓▓▓██")
        print("                                                      ██░░░░░░░░██▓▓██░░██▓▓██")
        print("                                                    ██░░░░░░░░██▓▓██░░░░██▓▓██")
        print("                                                    ██░░░░░░░░██▓▓██░░░░██▓▓██")
        print("                                                    ▓▓░░░░░░▒▒██▓▓██░░▒▒██▓▓▓▓")
        print("                            ▓▓▓▓▓▓                ▓▓▒▒░░░░▒▒██▓▓██▒▒▒▒▒▒██▒▒▓▓▓▓▓▓▓▓")
        print("                          ██░░  ██      ████      ██▒▒████████▓▓██▒▒▒▒▒▒▓▓▓▓▓▓██░░░░████████")
        print("                          ██  ░░████▓▓▓▓░░░░▓▓▓▓▓▓████░░░░░░░░██▒▒▒▒▒▒▓▓▓▓▓▓▓▓██░░░░░░▒▒░░▒▒██")
        print("                          ██  ░░██░░░░██░░░░░░████░░░░░░░░░░░░██▒▒▒▒██▓▓▓▓▓▓▓▓██░░░░░░░░░░░░██")
        print("                          ██  ░░░░▓▓████░░░░██░░░░░░░░░░▓▓██▓▓██▓▓▓▓████▓▓████░░░░░░░░░░░░░░██")
        print("                        ████░░░░░░██▒▒██░░██  ░░░░░░████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██")
        print("                      ▓▓░░██░░░░░░██▒▒▒▒██░░░░░░░░▓▓████▓▓▓▓▓▓▒▒▒▒░░░░░░░░░░░░░░▓▓██▓▓▒▒▓▓░░░░██")
        print("                    ██  ░░░░██░░░░██▒▒██  ░░░░░░██▒▒▒▒▒▒▒▒▒▒▒▒██▒▒▒▒░░░░░░░░░░██▓▓▒▒▒▒▒▒▒▒██░░██")
        print("                  ██  ░░░░▒▒▒▒██░░░░██  ░░░░░░██▒▒▒▒▒▒▓▓▓▓▓▓▓▓▒▒██▒▒▒▒▒▒▒▒▒▒░░██▓▓▓▓▓▓▓▓▓▓▒▒████")
        print("          ██▓▓██████████████████▓▓████░░░░░░▒▒██▒▒▒▒▓▓▓▓▓▓██▓▓▓▓██▒▒▒▒░░░░░░░░██▓▓▓▓████▓▓▓▓██")
        print("          ██░░▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▓▓░░▒▒██░░▒▒██▒▒▒▒▒▒▓▓██▒▒▒▒██▓▓▓▓██▒▒▒▒▒▒░░░░▓▓▓▓██▒▒▒▒██▓▓▓▓██")
        print("          ██░░▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▒▒▓▓░░▒▒▒▒██▒▒██▒▒▒▒▒▒▓▓██▒▒▒▒██▓▓▓▓██▒▒░░░░░░░░▓▓▓▓██▒▒▒▒██▓▓▓▓██")
        print("          ██░░▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓██░░▒▒▒▒██████▒▒▒▒▒▒▓▓██▒▒▒▒██▓▓▓▓██▒▒▒▒▒▒▒▒░░██▓▓██▒▒▒▒██▓▓▓▓██")
        print("        ██░░▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓██░░▒▒▒▒▒▒██  ██▒▒▒▒▓▓▓▓██▒▒░░██▓▓▓▓████░░░░░░░░██▓▓██▒▒░░██▓▓▓▓██")
        print("        ██░░▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓██░░▒▒▒▒▓▓██  ██▓▓▓▓▓▓▓▓██░░░░██▓▓▓▓██  ████████▓▓▓▓██░░░░██▓▓▓▓██")
        print("      ██░░▒▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓██░░▒▒▒▒▒▒▓▓██    ██▓▓▓▓▓▓▓▓████▓▓▓▓██        ██▓▓▓▓▓▓▓▓████▓▓▓▓██")
        print("  ████░░▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓██░░▒▒▒▒▒▒▒▒▓▓██    ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██        ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██")
        print("█░░░░░░░░░░░░▒▒▒▒▒▒░░░░░░░░▒▒▒▒▒▒▒▒▓▓██        ██▓▓▓▓▓▓▓▓▓▓▓▓██            ██▓▓▓▓▓▓▓▓▓▓▓▓██")
        print("█████████████████████████████████████            ████████████                ████████████")
        print("")

    def __setBase(self, base):
        """
        Changes the user's namespace.

        Changing to:

            'str' - selects the 'str' namespace, within the currently active
                    namespace
           '.str' - selects the 'str' namespace, in the root namespace
             '..' - goes back on namespace
               '' - goes back to the root namespace
        """

        if base == "":
            self.__base = base
        else:
            if base == "..":
                path = self.__base.split(".")

                try:
                    path.pop(-2)
                except IndexError:
                    pass

                target = ".".join(path)
            elif base.startswith("."):
                target = base[1:] + "."
            else:
                target = self.__base + base + "."

            if True in map(lambda m: m.startswith(target), self.modules.all(permissions=self.permissions())):
                self.__base = target
            else:
                self.stderr.write("no such namespace: %s\n"%base)

        if base == "":
            self.prompt = "dz> "
        else:
            self.prompt = "dz#{}> ".format(self.__base[0:len(self.__base)-1])

        return True

class DebugSession(Session):
    """
    DebugSession is a subclass of Session, which rewrites the default error
    handlers to print stacktrace information.
    """

    def __init__(self, server, session_id, arguments):
        Session.__init__(self, server, session_id, arguments)

        self.intro = "drozer Console (v%s debug mode)" % meta.version
        self.prompt = "dz> "
        
    def do_reload(self, args):
        """
        usage: reload
        
        Load a fresh copy of all modules from disk.
        """
        
        self.modules.reload()
        
        self.stdout.write("Done.\n\n")

    def handleException(self, e, shutup=False):
        """
        Invoked whenever an exception is triggered, to handle the
        throwable and display some information to the user.
        """
        self.stderr.write("exception in module: {}: {}\n".format(e.__class__.__name__, str(e)))
        self.stderr.write("%s\n"%traceback.format_exc())
