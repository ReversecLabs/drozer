import cmd
import os
from platform import platform
from drozer import meta

# readline works on linux/mac
# pyreadline3 works on windows
# or alternatively if you have none of those that's also fine, you just won't get tab-complete
has_readline = False
try:
    import readline
    has_readline = True
except ModuleNotFoundError:
    try:
        from pyreadline3 import Readline as readline
        has_readline = True
    except:
        pass

import shlex
import sys
import textwrap

from WithSecure.common import system
from WithSecure.common.text import wrap


class Cmd(cmd.Cmd):
    """
    An extension to cmd.Cmd to provide some advanced functionality. Including:

    - aliases for commands;
    - bash-style special variables;
    - history file support;
    - output redirection to file; and
    - separate output and error streams.

    Also overwrite some default prompts, to make a more user-friendly
    output.
    """

    def __init__(self):
        cmd.Cmd.__init__(self)

        self.__completer_stack = []
        self.__history_stack = []
        self.__output_redirected = None

        self.aliases = {}
        self.doc_header = "Commands:"
        self.doc_leader = wrap(textwrap.dedent(self.__class__.__doc__))
        self.history_file = None
        self.ruler = " "
        self.stdout = self.stdout
        self.stderr = sys.stderr
        self.variables = {}

    def cmdloop(self, intro=None):
        """
        Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """
        self.preloop()
        if self.use_rawinput and self.completekey:
            self.push_completer(self.complete, self.history_file)
        try:
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            line = input(self.prompt)
                        except EOFError:
                            line = 'EOF'
                    else:
                        self.stdout.write(self.prompt)
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')

                try:
                    line = self.precmd(line)
                    stop = self.onecmd(line)
                    stop = self.postcmd(stop, line)
                except ValueError as e:
                    if e.message == "No closing quotation":
                        self.stderr.write(
                            "Failed to parse your command, because there were unmatched quotation marks.\n")
                        self.stderr.write(
                            "Did you want a single ' or \"? You need to escape it (\\' or \\\") or surround it with "
                            "the other type of quotation marks (\"'\" or '\"').\n\n")
                    else:
                        raise
            self.postloop()
        except Exception as e:
            print("Loop exception")
            self.handleException(e)
            pass

        finally:
            if self.use_rawinput and self.completekey:
                self.pop_completer()

    def complete(self, text, state):
        """
        Return the next possible completion for 'text'.

        If a command has not been entered, then complete against command list.
        Otherwise, try to call complete_<command> to get list of completions.
        """

        if state == 0:
            if has_readline:
                origline = readline.get_line_buffer()
                line = origline.lstrip()
                stripped = len(origline) - len(line)
                begidx = readline.get_begidx() - stripped
                endidx = readline.get_endidx() - stripped

                if begidx > 0:
                    if ">" in line and begidx > line.index(">"):
                        self.completion_matches = self.completefilename(text, line, begidx, endidx)
                        return self.completion_matches[0]

                    command = self.parseline(line)[0]
                    if command == '':
                        compfunc = self.completedefault
                    else:
                        try:
                            compfunc = getattr(self, 'complete_' + command)
                        except AttributeError:
                            compfunc = self.completedefault
                else:
                    compfunc = self.completenames

                matches = compfunc(text, line, begidx, endidx)
                if len(matches) == 1 and matches[0].endswith(os.path.sep):
                    self.completion_matches = matches
                else:
                    self.completion_matches = list(map(lambda s: s + " ", matches))

        try:
            return self.completion_matches[state]
        except IndexError:
            return None
        except TypeError:
            return None

    #TODO implement
    def completefilename(self, text, line, begidx, endidx):
        """
        Placeholder for a filename autocompletion method, that is invoked by
        the runtime when providing an argument for output redirection.
        """

        pass

    def default(self, line):
        """
        Override the default handler (i.e., no command matched) so we can add
        support for aliases.
        """

        argv = shlex.split(line)

        if argv[0] in self.aliases:
            getattr(self, "do_" + self.aliases[argv[0]])(" ".join(argv[1:]))
        else:
            cmd.Cmd.default(self, line)

    def do_echo(self, arguments):
        """
        usage: echo LINE
        
        Prints out how a line will be processed at runtime, performing all variable substitutions.
        
        Example:
        
            dz> set P=com.example.app
            dz> echo run app.package.info -a $P
            run app.package.info com.example.app
        """

        print(self.__do_substitutions(arguments))

    def do_env(self, arguments):
        """
        usage: env

        Prints out all environment variables, that can be used to substitute values in commands, and are passed into the Android shell
        """

        for key in self.variables:
            print("%s=%s" % (key, self.variables[key]), end="\n")

    def do_set(self, arguments):
        """
        usage: set NAME=VALUE [NAME=VALUE ...]
        
        Sets one-or-more variables, that can be used to set values in subsequent commands.
        
        Example:
        
            dz> set P=com.example.app
            dz> run app.package.info -a $P
        """

        for kv in shlex.split(arguments):
            if "=" in kv:
                key, value = kv.split("=", 1)
                self.variables[key] = value

    def do_unset(self, arguments):
        """
        usage: unset NAME [NAME ...]
        
        Removes one-or-more values previously stored in variables.
        """

        for key in shlex.split(arguments):
            if key in self.variables:
                del self.variables[key]

    def emptyline(self):
        """
        Replace the default emptyline handler, it makes more sense to do nothing
        than to repeat the last command.
        """

        pass

    def handleException(self, e, shutup=False):
        """
        Default exception handler, writes the message to stderr.
        """
        if(shutup):
            return
        self.stderr.write("Exception occured: %s\n" % str(e))

    def postcmd(self, stop, line):
        """
        Remove output redirection when a command has finished executing.
        """

        if self.__output_redirected != None:
            tee = self.stdout
            self.stdout = self.__output_redirected

            self.__output_redirected = None

            del (tee)

        return stop

    def precmd(self, line):
        """
        Process a command before it executes: perform variable substitutions and
        set up any output redirection.
        """

        # perform Bash-style substitutions
        line = self.__do_substitutions(line)

        parsed_line = shlex.split(line)
        # perform output stream redirection (as in the `tee` command)
        if ">" in parsed_line or ">>" in parsed_line:
            line = self.__redirect_output(line)

        return line

    def checkVer(self):
        # check for new console versions
        try:
            latest, date = meta.latest_version()
            if latest is not None:
                if meta.version > latest:
                    print("It seems that you are running a drozer pre-release. Brilliant!\n\nPlease send any bugs, feature requests or other feedback to our GitHub project:\nhttps://github.com/WithSecureLabs/drozer\n\nYour contributions help us to make drozer awesome.\n")
                elif meta.version < latest:
                    print("It seems that you are running an old version of drozer. drozer v%s was\nreleased on %s. We suggest that you update your copy to make sure that\nyou have the latest features and fixes.\n\nTo download the latest drozer visit:\nhttps://github.com/WithSecureLabs/drozer/releases\n" % (latest, date))
        except Exception as e:
            #silence this exception unless in debug mode
            self.handleException(e, shutup=True)
            pass
        # check for new agent versions
        try:
            context = self.context()
            packageManager = context.getPackageManager()
            agentVersion = meta.Version(packageManager.getPackageInfo(context.getPackageName(), packageManager.GET_META_DATA).versionName)
            latestAgent, dateAgent = meta.latest_agent_version()
            if latestAgent is not None:
                if agentVersion < latestAgent:
                    print("It seems that you are running an old version of drozer-agent. drozer-agent v%s was\nreleased on %s. We suggest that you update your copy to make sure that\nyou have the latest features and fixes.\n\nTo download the latest drozer-agent visit:\nhttps://github.com/WithSecureLabs/drozer-agent/releases\n" % (latestAgent, dateAgent))
        except Exception as e:
            self.handleException(e, shutup=True)
            pass

    def preloop(self):
        if self.intro:
            self.stdout.write(str(self.intro) + "\n")
        self.checkVer()

    def push_completer(self, completer, history_file=None):
        if has_readline:
            self.__completer_stack.append(readline.get_completer())
            readline.set_completer(completer)
            readline.set_completer_delims(readline.get_completer_delims().replace("/", ""))

            if len(self.__history_stack) > 0 and self.__history_stack[-1]:
                readline.write_history_file(self.__history_stack[-1])

            self.__history_stack.append(history_file)
            readline.clear_history()
            if history_file is not None and os.path.exists(history_file):
                try:
                    # In macOS, this line causes a `[Errno 1] Operation not permitted` if there is a `~/.drozer_history`
                    readline.read_history_file(history_file)
                except IOError as e:
                    if "darwin" in platform().lower() and str(e).strip() == "[Errno 1] Operation not permitted":
                        print
                        "Could not access the history file..."
                    else:
                        raise e

            readline.parse_and_bind(self.completekey + ": complete")

    def pop_completer(self):
        if has_readline:
            if self.__history_stack[-1] != None:
                readline.write_history_file(self.__history_stack.pop())
            else:
                self.__history_stack.pop()

            readline.clear_history()
            if len(self.__history_stack) > 0 and self.__history_stack[-1]:
                readline.read_history_file(self.__history_stack[-1])

            readline.set_completer(self.__completer_stack.pop())

    def __build_tee(self, console, destination):
        """
        Create a WithSecure.system.Tee object to be used by output redirection.
        """

        if destination[0] == ">":
            destination = destination[1:]
            mode = 'a'
        else:
            mode = 'w'

        return system.Tee(console, destination.strip(), mode)

    def __do_substitutions(self, line):
        """
        Perform substitution of Bash-style variables.
        """

        # len(argv) ends up < 1 if line is blank, will cause an exception if not checked
        if not line:
            return ""

            # perform any arbitrary variable substitutions, from the dictionary
        for name in self.variables:
            line = line.replace("$%s" % name, self.variables[name])

        # perform special variable substitutions, referencing the previous command
        if line.find("!!") >= 0 or line.find("!$") >= 0 or line.find("!^") >= 0 or line.find("!*") >= 0:
            line = self.__do_last_command_substitutions(line)

        return line

    def __do_last_command_substitutions(self, line):
        if self.lastcmd != "":
            argv = shlex.split(self.lastcmd)

            line = line.replace("!!", self.lastcmd)
            line = line.replace("!$", argv[-1])
            line = line.replace("!^", argv[1])
            line = line.replace("!*", " ".join(argv[1:]))

            return line
        else:
            self.stderr.write("no previous command\n")

            return ""

    def __redirect_output(self, line):
        """
        Set up output redirection, by building a Tee between stdout and the
        specified file.
        """

        (line, destination) = line.rsplit(">", 1)

        if len(destination) > 0:
            try:
                self.__output_redirected = self.stdout
                self.stdout = self.__build_tee(self.stdout, destination)
            except IOError as e:
                self.stderr.write("Error processing your redirection target: " + e.strerror + ".e\n")
                return ""
        else:
            self.stderr.write("No redirection target specified.\n")
            return ""

        return line
