from pysolar.reflection import ReflectionException

from drozer.modules.common import file_system, loader

class Shell(file_system.FileSystem, loader.ClassLoader):
    """
    Wrapper around the Android Shell, that allows commands to be executed.
    """

    def shellExec(self, command):
        """
        Execute a single Shell command on the Agent.
        """

        ShellWrapper = self.loadClass("common/ShellWrapper.apk", "ShellWrapper")

        return ShellWrapper.execute("%s; %s" % (self.__get_variables(), command))
    
    def shellStart(self, command=""):
        """
        Create an interactive Linux shell on the Agent, optionally passing the
        first command.
        """
        try:
            shell = self.new("com.WithSecure.jsolar.util.Shell")
            in_shell = True
        except ReflectionException as e:
            raise e

        if shell.valid():
            self.__send_variables(shell)
        else:
            in_shell = False
            self.stderr.write("Unable to connect to shell")             
        while in_shell:
            try:
                shell.write(command)
                response = shell.read()
                
                if not shell.valid():
                    in_shell = False
                    continue
                
                self.stdout.write(response.strip())
                self.stdout.write(shell.read().strip() + " ")
                command = input()
            except ReflectionException as e:
                if str(e.message) == "Broken pipe":
                    in_shell = False
                else:
                    raise
            
        shell.close()

    def isFindInstalled(self):
        """
        Test whether the find binary is installed on the Agent.
        """
        
        return self.isCommandInstalled('find')
            
    def __get_variables(self):
        return "; ".join(map(lambda k: "export %s=\"%s\"" % (k, self.variables[k]), self.variables))
        
    def __send_variables(self, shell):
        shell.write(self.__get_variables())

        if 'WD' in self.variables:
            shell.write("cd %s" % (self.variables['WD']))

        shell.read()
