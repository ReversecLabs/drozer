import configparser
import os
import platform
import sys
import pathlib

from WithSecure.common import system

class Configuration(object):
    """
    Configuration provides a wrapper around a user's drozer configuration, stored
    in their home directory as .drozer_config.
    """
    
    __config = None
    ws_dz_agent_url = "https://github.com/WithSecureLabs/drozer-agent/releases/"
    
    @classmethod
    def executable(cls, name):
        """
        Fetch an executable, could be bundled in the lib, specified in the configuration, or attempt to find it on the PATH
        """
        
  

        #check the library
        path = cls.library(name)

        #is the required exe available on the PATH?
        if path == None and cls.get("executables", name) == None:
            path = system.which(name)
        
        if path == None:
            path = cls.get("executables", name)
        
        if path == None or path == "":
            sys.stderr.write("Could not find %s. Please ensure that it is installed and on your PATH.\n\nIf this "
                             "error persists, specify the path in the ~/.drozer_config file:\n\n    [executables]\n  "
                             "  %s = %s\n" % (name, name, platform.system() == "Windows" and "C:\\path\\to\\" + name
                                              or "/path/to/" + name))
            
        return path
    
    @classmethod
    def delete(cls, section, key):
        """
        Removes a key from the configuration, and persists the change to disk.
        """
        
        cls.__ensure_config()
        
        cls.__config.remove_option(section, key)
        cls.__config.write(open(cls.path(), 'w'))
    
    @classmethod
    def get(cls, section, key):
        """
        Returns a single configuration value.
        """
        
        cls.__ensure_config()
        
        try:
            if cls.__config.has_section(section):
                return cls.__config.get(section, key)
            else:
                return None
        except configparser.NoOptionError:
            return None
    
    @classmethod
    def get_all_keys(cls, section):
        """
        Returns all keys from a section of the configuration file.
        """
        
        cls.__ensure_config()
        
        if cls.__config.has_section(section):
            return cls.__config.options(section)
        else:
            return []
        
    @classmethod
    def get_all_values(cls, section):
        """
        Returns all values from a section of the configuration file.
        """
        
        cls.__ensure_config()
        
        if cls.__config.has_section(section):
            return list(map(lambda k: cls.__config.get(section, k), cls.__config.options(section)))
        else:
            return []
        
    @classmethod
    def has_section(cls, section):
        """
        Test whether or not a configuration file has a particular section.
        """
        
        cls.__ensure_config()
        
        return cls.__config.has_section(section)

    @classmethod
    def library_path(cls):
        """
        Returns the path to the drozer Library
        """
        return os.path.join(os.path.dirname(__file__), "lib")
    
    @classmethod
    def library(cls, name):
        """
        Returns the path to a drozer Library file
        Library search order is
            1) lib/name
            2) lib/platform/name
            3) lib/platform/name.*
        """
        
        file_path = os.path.join(cls.library_path(), name)
        if os.path.exists(file_path):
            return file_path

        file_path = os.path.join(cls.library_path(), platform.system(), name)
        if os.path.exists(file_path):
            return file_path

        dir_path = pathlib.Path(os.path.join(cls.library_path(), platform.system()))
        return next(dir_path.glob(f"{name}.*"), None)
        
    @classmethod
    def path(cls):
        """
        Returns the path to the configuration file.
        """
        
        if os.path.exists(os.path.sep.join([".", ".drozer_config"])):
            return os.path.sep.join([".", ".drozer_config"])
        else:
            return os.path.sep.join([os.path.expanduser("~"), ".drozer_config"])
    
    @classmethod
    def set(cls, section, key, value):
        """
        Sets a key in the configuration (creating it if it does not exist), and persists
        the change to disk.
        """
        
        cls.__ensure_config()
        
        if not cls.__config.has_section(section):
            cls.__config.add_section(section)
        
        cls.__config.set(section, key, value)
        cls.__config.write(open(cls.path(), 'w'))
        
    @classmethod
    def __ensure_config(cls):
        """
        Loads the configuration from file, if it has not already been loaded.
        """
        
        if cls.__config == None:
            cls.__config = configparser.ConfigParser()
            cls.__config.optionxform = lambda optionstr: optionstr.replace(":", "|")
            
            if os.path.exists(cls.path()):
                cls.__config.read(cls.path())
                
