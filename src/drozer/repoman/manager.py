from reversec.common import cli, console, text

from drozer.repoman.installer import ModuleInstaller
from drozer.repoman.remotes import Remote, NetworkException, UnknownRemote
from drozer.repoman.repositories import Repository, NotEmptyException, UnknownRepository
import os

class ModuleManager(cli.Base):
    """
    module [COMMAND]
    
    Run the drozer Module and Repository Manager.

    The Repository Manager handles drozer Modules and Module Repositories.
    """
    
    exit_on_error = False

    def __init__(self):
        cli.Base.__init__(self, add_help=False)
        
        self._parser.add_argument("-h", "--help", action="store_true", dest="help", default=False)
        self._parser.add_argument("-d", "--descriptions", action="store_true", default=False, help="include descriptions when searching modules (search only)")
        self._parser.add_argument("options", nargs="+", default="")
        self._parser.add_argument("-f", "--force", action="store_true", default=False, help="force install modules from the repositories (install only)")

        self._parser.error = self.__parse_error
        
    def do_install(self, arguments):
        """install a new module"""
        
        repository = self.__choose_repo()
        
        if repository != None:
            installer = ModuleInstaller(repository)
            modules = installer.install(arguments.options, arguments.force)
                        
            print("Successfully installed %d modules, %d already installed." % (len(modules['success']), len(modules['existing'])))
            if len(modules['fail']) > 0:
                print("Failed to install %d modules:" % len(modules['fail']))
                for module in modules['fail']:
                    print("  %s" % module)
                    print("    %s" % modules['fail'][module])
            print("\n")
        
    def do_remote(self, arguments):
        """manage the source repositories, from which you install modules"""
        
        RemoteManager().run(arguments.options)
        
    def do_repository(self, arguments):
        """manage module repositories, on your local system"""
        
        RepositoryManager().run(arguments.options)
        
    def do_search(self, arguments):
        """search for modules"""

        self.__search_remotes(len(arguments.options) > 0 and arguments.options[0] or "", arguments.descriptions)

    def get_completion_suggestions(self, action, text, **kwargs):
        return []


    def run(self, argv=None):
        """
        Run is the main entry point of the console, called by the runtime. It
        parses the command-line arguments, and invokes an appropriate handler.
        """

        if argv == None:
            argv = []

        arguments = self._parser.parse_args(argv)

        if arguments.help or arguments.command == None:
            self._parser.print_help()
        else:
            try:
                self._Base__invoke_command(arguments)
            except cli.UsageError:
                self._parser.print_help()
    
    def __choose_repo(self):
        """
        Return the path of a repository, either the only repo or presenting the user
        with a choice.
        """
        
        repositories = list(Repository.all())
        
        if len(repositories) == 1:
            return repositories[0]
        elif len(repositories) == 0:
            print("You do not have a drozer Module Repository.")
            if self.confirm("Would you like to create one?") == "y":
                while True:
                    path = self.ask("Path to new repository: ")
                    
                    try:
                        path = os.path.abspath(path)
                        Repository.create(path)
                        
                        print("Initialised repository at %s.\n" % path)
                        
                        return list(Repository.all())[0]
                    except NotEmptyException:
                        print("The target (%s) already exists.\n" % path)
                
                return None
            else:
                return None
        else:
            print("You have %d drozer Module Repositories. Which would you like to install into?\n" % len(repositories))
            for i in range(len(repositories)):
                print("  %5d  %s" % (i+1, repositories[i]))
            print()
            
            while(True):
                print("repo>")
                try:
                    idx = int(input().strip())
                
                    if idx >= 1 and idx <= len(repositories):
                        print()
                        
                        return repositories[idx-1]
                    else:
                        raise ValueError(idx)
                except ValueError:
                    print("Not a valid selection. Please enter a number between 1 and %d." % len(repositories))
    
    def __parse_error(self, message):
        """
        Silently swallow parse errors.
        """
        
        pass
    
    def __search_remotes(self, term, include_descriptions=False):
        """
        Search for modules, on remote repositories.
        """
        
        installer = ModuleInstaller(None)

        try:
            modules = installer.search_index(term)
            
            if len(modules) > 0:
                for module in modules:
                    print(module)
                    
                    if include_descriptions:
                        if module.description != None:
                            print("%s\n" % text.indent(text.wrap(module.description, console.get_size()[0] - 4), "    "))
                        else:
                            print(text.indent("No description given.\n", "    "))
                print()
            else:
                print("No modules found.\n")
        except NetworkException:
            print("There was a problem accessing one-or-more of the remote repositories.\n\nMake sure that you have a working network connection.\n")


class RemoteManager(cli.Base):
    """
    module remote [COMMAND] [OPTIONS]
    
    Run the remote part of the drozer Module and Repository Manager.
    """
    
    exit_on_error = False

    def __init__(self):
        cli.Base.__init__(self, add_help=False)
        
        self._parser.add_argument("-h", "--help", action="store_true", dest="help", default=False)
        self._parser.add_argument("options", nargs='*')
        
        self._parser.error = self.__parse_error
        
    def do_add(self, arguments):
        """add a new remote module repository"""
        
        if len(arguments.options) == 1:
            url = arguments.options[0]

            Remote.create(url)
            
            print("Added remote: %s.\n" % url)
        else:
            print("usage: drozer module remote create http://path.to.repository/\n")
    
    def do_remove(self, arguments):
        """remove a remote module repository"""
        
        if len(arguments.options) == 1:
            url = arguments.options[0]
            
            try:
                Remote.delete(url)
                
                print("Removed remove %s.\n" % url)
            except UnknownRemote:
                print("The target (%s) is not a remote module repository.\n" % url)
        else:
            print("usage: drozer module remote delete http://path.to.repository/\n")
        
    def do_list(self, arguments):
        """shows a list of all remotes"""
        
        print("Remote repositories:")
        for url in Remote.all():
            print("  %s" % url)

            try:
                Remote(url).download("INDEX.xml")
            except NetworkException:
                print("    INACCESSIBLE")
        print()

    def run(self, argv=None):
        """
        Run is the main entry point of the console, called by the runtime. It
        parses the command-line arguments, and invokes an appropriate handler.
        """

        if argv == None:
            argv = []

        arguments = self._parser.parse_args(argv)

        if arguments.help or arguments.command == None:
            self._parser.print_help()
        else:
            try:
                self._Base__invoke_command(arguments)
            except cli.UsageError:
                self._parser.print_help()
    
    def __parse_error(self, message):
        """
        Silently swallow parse errors.
        """
        
        pass
                
        
class RepositoryManager(cli.Base):
    """
    module repository [COMMAND] [OPTIONS]
    
    Run the repository part of the drozer Module and Repository Manager.

    The Repository Manager handles drozer Modules and Module Repositories.
    """
    
    exit_on_error = False

    def __init__(self):
        cli.Base.__init__(self, add_help=False)
        
        self._parser.add_argument("-h", "--help", action="store_true", dest="help", default=False)
        self._parser.add_argument("options", nargs='*')
        
        self._parser.error = self.__parse_error
        
    def do_create(self, arguments):
        """create a new drozer module repository"""
        
        if len(arguments.options) == 1:
            path = arguments.options[0]
            path = os.path.abspath(path)
            
            try:
                Repository.create(path)
                
                print("Initialised repository at %s.\n" % path)
            except NotEmptyException:
                print("The target (%s) already exists.\n" % path)
        else:
            print("usage: drozer module repository create /path/to/repository\n")
    
    def do_delete(self, arguments):
        """remove a drozer module repository"""
        
        if len(arguments.options) == 1:
            path = arguments.options[0]
            path = os.path.abspath(path)
            
            try:
                Repository.delete(path)
                
                print("Removed repository at %s.\n" % path)
            except UnknownRepository:
                print("The target (%s) is not a drozer module repository.\n" % path)
        else:
            print("usage: drozer module repository delete /path/to/repository\n")
                
    def do_disable(self, arguments):
        """hide a Module repository, without deleting its contents"""
        
        if len(arguments.options) == 1:
            path = arguments.options[0]
            path = os.path.abspath(path)
            
            try:
                Repository.disable(path)
                
                print("Hidden repository at %s.\n" % path)
            except UnknownRepository:
                print("The target (%s) is not a drozer module repository.\n" % path)
        else:
            print("usage: drozer module repository disable /path/to/repository\n")
    
    def do_enable(self, arguments):
        """enable a previously disabled Module repository"""
        
        if len(arguments.options) == 1:
            path = arguments.options[0]
            path = os.path.abspath(path)
            
            try:
                Repository.enable(path)
                
                print("Enabled repository at %s.\n" % path)
            except UnknownRepository:
                print("The target (%s) is not a drozer module repository.\n" % path)
        else:
            print("usage: drozer module repository enable /path/to/repository\n")
        
    def do_list(self, arguments):
        """list all repositories, both local and remote"""
        
        self.__list_repositories()

    def run(self, argv=None):
        """
        Run is the main entry point of the console, called by the runtime. It
        parses the command-line arguments, and invokes an appropriate handler.
        """

        if argv == None:
            argv = []

        arguments = self._parser.parse_args(argv)

        if arguments.help or arguments.command == None:
            self._parser.print_help()
        else:
            try:
                self._Base__invoke_command(arguments)
            except cli.UsageError:
                self._parser.print_help()
        
    def __list_repositories(self):
        """
        Print a list of drozer Repositories (a) on the local system, and
        (b) registered as remotes.
        """
        
        print("Local repositories:")
        for repo in Repository.all():
            print("  %s" % repo)
        print()
    
    def __parse_error(self, message):
        """
        Silently swallow parse errors.
        """
        
        pass
        
