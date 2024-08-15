import itertools

from WithSecure.common.list import flatten

from drozer.modules import base

class ModuleCollection(object):
    
    def __init__(self, loader):
        self.__base = base.Module
        self.__loader = loader
        
    def all(self, contains=None, permissions=None, prefix=None,exploit=None, module_type="drozer"):
        """
        Loads all modules from the specified module repositories, and returns a
        collection of module identifiers.
        """

        modules = self.__loader.all(self.__base)
        modules = filter(lambda m: self.get(m).module_type == module_type, modules)

        if contains != None:
            modules = filter(lambda m: m.find(contains.lower()) >= 0, modules)
        if permissions != None:
            p = set(permissions)
            modules = filter(lambda m: set(self.get(m).permissions).issubset(p), modules)
        if prefix != None:
            modules = filter(lambda m: m.startswith(prefix), modules)
        if module_type =="payload" and exploit is not None:
            modules = filter(lambda m: m in self.get(exploit).payloads, modules)
            
        return modules

    def contributors(self):
        """
        Returns a list of module contributors, ordered by the number of modules
        they have authored (in descending order).
        """
        
        contributors = map(lambda m: self.get(m).author, self.all())
        contribution = [(c[0], len(list(c[1]))) for c in itertools.groupby(sorted(flatten(contributors)))]
        
        return map(lambda c: c[0], sorted(contribution, key=lambda c: -c[1]))
        
    def get(self, key):
        """
        Gets a module implementation, given its identifier.
        """

        return self.__loader.get(self.__base, key)
    
    def reload(self):
        """
        Reload all modules.
        """
        
        self.__loader.reload()
        
