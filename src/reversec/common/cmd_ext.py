import cmd
import os
from platform import platform
from drozer import meta

has_prompt_toolkit = False
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.history import FileHistory, InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.filters import has_completions as _has_completions
    has_prompt_toolkit = True
except ImportError:
    pass

import shlex
import sys
import textwrap

from reversec.common import system
from reversec.common.text import wrap


if has_prompt_toolkit:
    def _make_drozer_key_bindings():
        """
        Replaces prompt_toolkit's default Tab cycling behaviour with
        "apply and drill down":

        - When the completion menu is open, Tab commits the currently
          highlighted completion (or the first one if nothing is highlighted)
          and immediately applies it to the buffer.
        - For namespace completions (ending in '.'), complete_while_typing
          then refreshes the dropdown to the next level automatically.
        - For leaf completions the module name is filled in; Enter submits.
        - Arrow keys still navigate the menu without committing anything,
          so the user can pick a specific item before pressing Tab.
        - When the menu is not open, Tab opens it (default behaviour).

        Why not intercept Enter instead?  complete_while_typing re-runs the
        completer the instant Tab would apply a namespace, which creates a
        brand-new complete_state with nothing selected — so any Enter filter
        based on completion_is_selected is always False by the time the user
        presses Enter.  Making Tab do the work sidesteps this entirely.
        """
        kb = KeyBindings()

        @kb.add('tab', filter=_has_completions, eager=True)
        def _tab_apply_completion(event):
            buf = event.current_buffer
            cs = buf.complete_state
            if cs and cs.completions:
                comp = cs.current_completion or cs.completions[0]
                buf.apply_completion(comp)

        @kb.add('c-c', eager=True)
        def _ctrl_c_handler(event):
            if event.current_buffer.text:
                # Buffer has content: clear the line and stay in the session
                event.current_buffer.reset()
            else:
                # Empty buffer: exit (mirrors bash / most shell behaviour)
                event.app.exit(exception=KeyboardInterrupt())

        return kb

    _DROZER_KEY_BINDINGS = _make_drozer_key_bindings()

    class DrozerCompleter(Completer):
        """
        Bridges prompt_toolkit's Completer interface to the existing cmd-style
        complete_<command> / completenames dispatch chain.

        All the underlying completion methods (complete_run, complete_cd,
        completenames, ArgumentParserCompleter etc.) use the clean
        (text, line, begidx, endidx) signature with no readline dependency,
        so they plug straight in here.

        WORD=True is critical: it splits only on whitespace, so dotted module
        names like "app.package.info" are treated as a single token and passed
        intact to the underlying completion functions.
        """

        def __init__(self, cmd_instance):
            self._cmd = cmd_instance

        def get_completions(self, document, complete_event):
            text_before = document.text_before_cursor
            line = text_before.lstrip()
            stripped = len(text_before) - len(line)
            # WORD=True: only split on whitespace, so "app.package" stays whole
            text = document.get_word_before_cursor(WORD=True)
            begidx = len(text_before) - len(text) - stripped
            endidx = len(text_before) - stripped

            try:
                if begidx > 0:
                    # Output redirection: delegate to completefilename after ">"
                    if ">" in line and begidx > line.index(">"):
                        matches = self._cmd.completefilename(text, line, begidx, endidx) or []
                    else:
                        command = self._cmd.parseline(line)[0]
                        if not command:
                            compfunc = self._cmd.completedefault
                        else:
                            compfunc = getattr(self._cmd, 'complete_' + command,
                                               self._cmd.completedefault)
                        matches = compfunc(text, line, begidx, endidx) or []
                else:
                    matches = self._cmd.completenames(text, line, begidx, endidx) or []
            except Exception:
                return

            for m in matches:
                if m.endswith('.'):
                    # Namespace suggestion from completemodules: trailing dot signals
                    # "there are more levels below". Display without dot so the
                    # dropdown looks clean; insert WITH dot so the next completion
                    # call immediately shows the next level.
                    yield Completion(m, start_position=-len(text), display=m.rstrip('.'))
                elif m.endswith(os.path.sep):
                    # Filesystem directory
                    yield Completion(m, start_position=-len(text))
                else:
                    # Leaf module, command name, or flag: add trailing space
                    yield Completion(m.rstrip() + ' ', start_position=-len(text))

    class _ModuleCompleter(Completer):
        """
        Wraps a readline-style (text, state) -> str|None completer callable
        for use as a prompt_toolkit Completer. Used for module-provided
        completers pushed via push_completer().
        """

        def __init__(self, readline_fn):
            self._fn = readline_fn

        def get_completions(self, document, complete_event):
            text = document.get_word_before_cursor()
            state = 0
            while True:
                result = self._fn(text, state)
                if result is None:
                    break
                yield Completion(result, start_position=-len(text))
                state += 1


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

        # prompt_toolkit state
        self._pt_session = None
        self._pt_completer = None
        self._pt_completer_stack = []
        self._pt_history_stack = []

    def cmdloop(self, intro=None):
        """
        Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """
        self.preloop()

        if has_prompt_toolkit:
            history = FileHistory(self.history_file) if self.history_file else InMemoryHistory()
            self._pt_completer = DrozerCompleter(self)
            self._pt_session = PromptSession(history=history, key_bindings=_DROZER_KEY_BINDINGS)
            self._pt_history_stack = [self.history_file]
            self._pt_completer_stack = []

        try:
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            if has_prompt_toolkit and self._pt_session:
                                line = self._pt_session.prompt(
                                    self.prompt,
                                    completer=self._pt_completer,
                                    complete_while_typing=True,
                                    auto_suggest=AutoSuggestFromHistory(),
                                    bottom_toolbar=self._pt_bottom_toolbar,
                                )
                            else:
                                line = input(self.prompt)
                        except EOFError:
                            # Ctrl+D: exit the session cleanly
                            self.stdout.write('\n')
                            stop = True
                            break
                        except KeyboardInterrupt:
                            # Ctrl+C on empty buffer (non-empty is handled by
                            # the key binding, which clears the line in-place)
                            self.stdout.write('\n')
                            stop = True
                            break
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
                    if str(e) == "No closing quotation":
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

    def _pt_bottom_toolbar(self):
        """
        Returns contextual help for display in the prompt_toolkit bottom toolbar.
        Shows the usage line of the command currently being typed.
        """
        try:
            text = self._pt_session.app.current_buffer.text.lstrip()
        except AttributeError:
            return ""
        command = self.parseline(text)[0] if text else ""
        if not command:
            return ""
        try:
            raw_doc = (getattr(self, 'do_' + command).__doc__ or "").strip()
            usage = next((l.strip() for l in raw_doc.splitlines() if l.strip()), "")
            if usage:
                safe = usage.replace("<", "&lt;").replace(">", "&gt;")
                return HTML(f"<b>{command}</b> — {safe}")
        except AttributeError:
            pass
        return ""

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
                    print("It seems that you are running a drozer pre-release. Brilliant!\n\nPlease send any bugs, feature requests or other feedback to our GitHub project:\nhttps://github.com/ReversecLabs/drozer\n\nYour contributions help us to make drozer awesome.\n")
                elif meta.version < latest:
                    print("It seems that you are running an old version of drozer. drozer v%s was\nreleased on %s. We suggest that you update your copy to make sure that\nyou have the latest features and fixes.\n\nTo download the latest drozer visit:\nhttps://github.com/ReversecLabs/drozer/releases\n" % (latest, date))
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
                    print("It seems that you are running an old version of drozer-agent. drozer-agent v%s was\nreleased on %s. We suggest that you update your copy to make sure that\nyou have the latest features and fixes.\n\nTo download the latest drozer-agent visit:\nhttps://github.com/ReversecLabs/drozer-agent/releases\n" % (latestAgent, dateAgent))
        except Exception as e:
            self.handleException(e, shutup=True)
            pass

    def preloop(self):
        if self.intro:
            self.stdout.write(str(self.intro) + "\n")
        self.checkVer()

    def push_completer(self, completer, history_file=None):
        """
        Push a new completer (and optionally switch history file) onto the stack.
        Used by modules that need to temporarily override tab-completion.
        """
        if not has_prompt_toolkit or self._pt_session is None:
            return

        self._pt_completer_stack.append(self._pt_completer)
        self._pt_history_stack.append(history_file)

        if completer is self.complete:
            self._pt_completer = DrozerCompleter(self)
        else:
            self._pt_completer = _ModuleCompleter(completer)

        new_history = FileHistory(history_file) if history_file else InMemoryHistory()
        self._pt_session = PromptSession(history=new_history, key_bindings=_DROZER_KEY_BINDINGS)

    def pop_completer(self):
        """
        Restore the previous completer and history from the stack.
        """
        if not has_prompt_toolkit or not self._pt_completer_stack:
            return

        self._pt_completer = self._pt_completer_stack.pop()
        self._pt_history_stack.pop()

        prev_history_file = self._pt_history_stack[-1] if self._pt_history_stack else None
        history = FileHistory(prev_history_file) if prev_history_file else InMemoryHistory()
        self._pt_session = PromptSession(history=history, key_bindings=_DROZER_KEY_BINDINGS)

    def complete(self, text, state):
        """
        Stub kept for API compatibility with push_completer() callers that
        pass `self.complete` as the completer function. The actual completion
        work is done by DrozerCompleter when prompt_toolkit is active.
        """
        return None

    def __build_tee(self, console, destination):
        """
        Create a reversec.system.Tee object to be used by output redirection.
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
