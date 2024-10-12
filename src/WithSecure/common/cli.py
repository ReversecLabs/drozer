import argparse
import sys
import textwrap

from WithSecure.common import console

class Base(object):
    """
    cli.Base provides a simple command-line environment, where numerous different
    commands can be invoked.
    """

    exit_on_error = True

    def __init__(self, add_help=True):
        doc_text = textwrap.dedent(self.__doc__).strip().split("\n")

        self._parser = argparse.ArgumentParser(add_help=add_help, description="\n".join(doc_text[1:]),
                                               usage=doc_text[0])
        self._parser.add_argument("command", default=None, help="the command to execute")

        self._parser.epilog = "available commands:\n%s" % self.__get_commands_help()
        self._parser.error = self.__parse_error
        self._parser.formatter_class = argparse.RawDescriptionHelpFormatter

    def ask(self, prompt):
        """
        Ask the user a question, and collect a single line as input.
        """

        return input(prompt)

    def choose(self, prompt, options):
        """
        Ask the user to select from a list of options. 
        """

        while (True):
            selection = self.ask("%s [%s] " % (prompt, "".join(options)))

            if selection in options:
                return selection

    def confirm(self, prompt):
        """
        Ask the user to confirm yes/no.
        """

        return self.choose(prompt, ["y", "n"])

    def parse_arguments(self, parser, arguments):
        return parser.parse_args(arguments)

    def parse_known_args(self, parser, arguments):
        parser_print_help = self._parser.print_help
        parser_exit = self._parser.exit
        self._parser.print_help = lambda: None
        self._parser.exit = lambda: None
        args, unknown = self._parser.parse_known_args(arguments)
        self._parser.print_help = parser_print_help
        self._parser.exit = parser_exit

        return args, unknown

    def prepare_argument_parser(self, argv):
        # try to find the command, before we invoke the parser so we can add additional arguments
        command_argv = [a for a in argv if "do_" + a in self.__commands()]

        if len(command_argv) == 1 and hasattr(self, "args_for_" + command_argv[0]):
            getattr(self, "args_for_" + command_argv[0])()
        if hasattr(self, "before_parse_args"):
            self.before_parse_args(argv)

    def run(self, argv=None):
        """
        Run is the main entry point of the console, called by the runtime. It
        parses the command-line arguments, and invokes an appropriate handler.
        """

        if argv is None:
            argv = []

        self.prepare_argument_parser(argv)
        # parse argv into arguments using the generated ArgumentParser
        arguments = self.parse_arguments(self._parser, argv)

        try:
            self.__invoke_command(arguments)
        except UsageError as e:
            self.__show_usage(e.message)
        except Exception as e:
            self.handle_error(e)

    def do_commands(self, arguments):
        """shows a list of all console commands"""

        print("usage:", self.__doc__.strip(), end="\n")
        print("available commands:")
        print(self.__get_commands_help())

    def handle_error(self, throwable):
        """default error handler: shows an exception message, before terminating"""

        sys.stderr.write("%s\n\n" % throwable)
        sys.exit(-1)

    def __commands(self):
        """
        Get a list of supported commands to console, by searching for any
        method beginning with do_.
        """

        return [f for f in dir(self) if f.startswith("do_") and getattr(self, f).__doc__ is not None]

    def __get_commands_help(self):
        """
        Produce a piece of text, containing the available commands, and their short
        description.
        """

        commands = {}

        for command in self.__commands():
            commands[command.replace("do_", "").replace("_", "-")] = getattr(self, command).__doc__.strip()

        return console.format_dict(commands, left_margin=2)

    def __invoke_command(self, arguments):
        """
        Execute a console command, given the command-line arguments.
        """

        try:
            command = arguments.command.replace("-", "_")

            if "do_" + command in dir(self):
                getattr(self, "do_" + command)(arguments)
            else:
                raise UsageError("unknown command: " + command)
        except IndexError:
            raise UsageError("incorrect usage")

    def __parse_error(self, message):
        self.__show_usage(message)

        if self.exit_on_error:
            sys.exit(-1)

    def __show_usage(self, message):
        """
        Print usage information.
        """
        if message is not None:
            print("error:", message, end="\n")

        print(self._parser.format_help())


class UsageError(Exception):
    def __init__(self, *args: object):
        super().__init__(args)
        self.message = None

    """
    UsageError exception is thrown if an invalid set of parameters is passed
    to a console method, through __invokeCommand().
    """

    pass
