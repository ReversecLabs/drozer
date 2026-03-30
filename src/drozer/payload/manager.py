import sys

from reversec.common import cli, console

from drozer.payload import builder

class PayloadManager(cli.Base):
    """
    drozer payload COMMAND [OPTIONS]
    
    A utility for crafting payloads to deliver drozer onto an Android device.
    """
    
    def __init__(self):
        cli.Base.__init__(self)

        self.builder = builder.Builder()
    
    def args_for_build(self):
        self._parser.add_argument("module", help="specify the payload module to use")
        self._parser.add_argument("--format", choices=builder.Formats, default=builder.Formats[0], help="specify the format for the payload (Raw bytes, Unicode or heX string)")
        self._parser.add_argument("--server", default=None, metavar="HOST[:PORT]", help="specify the address and port of the drozer server")
        
    def do_build(self, arguments):
        """build a payload"""
        
        print(self.builder.build(arguments.module, arguments))

    def args_for_info(self):
        self._parser.add_argument("module", help="specify the payload module to use")
        
    def do_info(self, arguments):
        """prints information about a payload module"""
        
        module = self.builder.module(arguments.module)
        
        print(module.usage.formatted_description())
        
    def do_list(self, arguments):
        """list the available payload modules"""
        
        sys.stdout.write(console.format_dict(dict(map(lambda m: [m, self.builder.module(m).name], self.builder.modules()))) + "\n")
        
    def before_parse_args(self, argv):
        """
        Allow payload modules to add additional arguments.
        """
        
        args, unknown = self.parse_known_args(self._parser, argv)
        
        if hasattr(args, 'module') and args.module != None and args.module != "":
            self.builder.module(args.module).add_arguments(self._parser)
        
    def get_completion_suggestions(self, action, text, line, **kwargs):
        if action.dest == "module":
            return self.builder.modules()
        elif action.dest == "server":
            return ["localhost:31415"]
