import argparse
import textwrap

from pysolar.reflection.types import ReflectedType

from reversec.common import argparse_completer, console
from reversec.common.text import wrap

class Module(object):
    """
    Module is the base class for all drozer Modules.

    It provides base services, including initializing your module and access to
    the reflector.
    """

    name = "drozer Module"
    description = ""
    examples = ""
    author = "Unspecified"
    date = "1970-01-01"
    license = "Unspecified"
    path = []
    permissions = []
    module_type = "drozer"
    
    push_completer = None
    pop_completer = None

    __klasses = {}

    def __init__(self, session):
        if self.module_type == "drozer":
            self.modules = session.modules
            self.reflector = session.reflector
            self.stdout = session.stdout
            self.stderr = session.stderr
            self.variables = session.variables
        
        self.usage = Usage(self)

    def add_arguments(self, parser):
        """
        Stub Method: override this in a module to add command-line options to the
        internal ArgumentParser instance.
        """

        pass

    def arg(self, native, obj_type=None):
        """
        Utility method to build a ReflectedType from a native value.

        This should be used to force an object to assume a particular data type
        in Java.
        """
        
        return ReflectedType.fromNative(native, reflector=self.reflector, obj_type=obj_type)
    
    @classmethod
    def cache_klass(cls, klass, ref):
        """
        Store a reflected Class reference in the cache of classes.
        """
        
        Module.__klasses[klass] = ref
    
    @classmethod
    def cached_klass(cls, klass):
        """
        True, if there is a reflected Class reference stored in the cache of classes.
        """
        
        return klass in Module.__klasses

    def clearObjectStore(self):
        """
        Removes all stored objects from the remote ObjectStore.

        This invalidates all cached object references.
        """

        Module.__klasses = {}

        self.reflector.deleteAll()

    def complete(self, text, line, begidx, endidx):
        """
        Intercept all readline completion requests for argument strings, and delegate
        them to the ArgumentParserCompleter to get suitable suggestions.
        """
        return argparse_completer.ArgumentParserCompleter(self.__prepare_parser(), self).get_suggestions(text, line, begidx, endidx, offs=0)

    @classmethod
    def fqmn(cls):
        """
        Gets the fully-qualified module name, i.e., '.full.path.to.my.module'
        """

        return ".".join(cls.path + [cls.__name__.lower()])
    
    @classmethod
    def get_cached_klass(cls, klass):
        """
        Retrieve a reflected class reference from the cache of classes.
        """
        
        return Module.__klasses[klass]
    
    def get_completion_suggestions(self, action, text, line, **kwargs):
        """
        Stub Method: invoked during completion of module arguments, to allow the module
        to provide suggestions.
        """
        pass

    def getContext(self):
        """
        Gets the context of the running Agent application.
        """

        return self.klass('com.reversec.dz.Agent').getContext()
    
    def has_context(self):
        """
        Test if Context is available to this module.
        """
        
        return not self.getContext() == None

    def klass(self, class_name):
        """
        Resolves a class name, and returns an object reference for the class.
        """

        if not Module.cached_klass(class_name):
            Module.cache_klass(class_name, self.reflector.resolve(class_name))
        
        return Module.get_cached_klass(class_name)

    @classmethod
    def namespace(cls):
        """
        Get the namespace of the module, i.e., 'full.path.to.my' without '.module'
        """

        return ".".join(cls.path)

    def new(self, class_or_class_name, *args):
        """
        Instantiate a Java class, either by name or with a class reference.
        """

        if(isinstance(class_or_class_name, ReflectedType)):
            klass = class_or_class_name
        else:
            klass = self.klass(class_or_class_name)

        return self.reflector.construct(klass, *map(lambda arg: self.arg(arg), args))

    def null_complete(self, text, state):
        return None
        
    def run(self, args):
        """
        Entry point for running a module.

        This method prepare the ArgumentParser object, before invoking the
        custom execute() method, and cleaning up instantiated objects.
        """

        parser = self.__prepare_parser()

        parser.description = self.usage.formatted_description()
        parser.usage = self.usage.formatted_usage(parser)

        if "-h" in args or "--help" in args:
            return parser.print_help()
        else:
            arguments = parser.parse_args(args)
            
            if hasattr(self, 'execute'):
                result = self.execute(arguments)
            else:
                self.stderr.write("drozer doesn't know how to do that.\n")
                self.stderr.write("The %s module does not define an execute() method.\n\n" % self.fqmn())
                
                result = None
                
            self.clearObjectStore()

            return result

    def __parse_error(self, message):
        """
        Error handler for the ArgumentParser instance, to override its default
        behaviour, and escalate the error to a point where we can handle it
        properly.
        """

        raise Exception(message)
    
    def __prepare_parser(self):
        """
        Build an argparse.ArgumentParser for this Module.
        """
        
        parser = argparse.ArgumentParser(add_help=False, formatter_class=argparse.RawTextHelpFormatter)

        parser.error = self.__parse_error

        parser.add_argument("-h", "--help", action="store_true", dest="help", default=False)

        self.add_arguments(parser)
        return parser
        

class Usage(object):
    
    def __init__(self, module):
        self.module = module.__class__
    
    def authors(self):
        """
        Returns a string containing the module authors, joined with ", " if
        there is a list provided.
        """
        
        if isinstance(self.module.author, str):
            return self.module.author
        else:
            return ", ".join(self.module.author)
        
    def description(self):
        """
        Returns a cleaned up version of the module description, which removes
        any leading indentation.
        """
        
        return textwrap.dedent(self.module.description).strip()
        
    def examples(self):
        """
        Returns a cleaned up version of the module examples, which removes any
        leading indentation.
        """
        
        return textwrap.dedent(self.module.examples).strip()
    
    def formatted_description(self):
        """
        Build a formatted description of a module, including the description,
        usage information, examples and other metadata.
        """

        description = self.description() + "\n\n" +\
                        (self.has_examples() and "Examples:\n" + self.examples() + "\n\n" or "") +\
                        "Last Modified: " + self.module.date + "\n" +\
                        "Credit: " + self.authors() + "\n" +\
                        "License: " + self.module.license + "\n\n"

        return wrap(description, width=console.get_size()[0])
    
    def formatted_usage(self, parser):
        """
        Get usage information about the Module.
        """

        return "run {} {}\n\n".format(self.module.fqmn(), " ".join(parser.format_usage().split(" ")[2:]))
        
    def has_examples(self):
        """
        True, if this Usage has some examples. Otherwise, False.
        """
        
        return self.examples() != ""
    
