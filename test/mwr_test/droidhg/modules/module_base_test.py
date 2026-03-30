import argparse
import functools
import sys
import unittest

from mwr.cinnibar.reflection.types import ReflectedObject, ReflectedType

from mwr.droidhg.modules import Module
from mwr_test.mocks.session import MockSession

class ModuleTestCase(unittest.TestCase):

    class MockModule(Module):

        name = "Mock Module"
        description = "Mock Module"
        examples = ""
        author = "@mwrlabs"
        date = "2012-12-21"
        license = "Don't Use It"
        path = ["an", "example"]

        def __init__(self, *args, **kwargs):
            Module.__init__(self, *args, **kwargs)

            self.add_arguments_with = None
            self.execute_with = None

        def add_arguments(self, parser):
            self.add_arguments_with = parser

        def execute(self, arguments):
            self.execute_with = arguments

    class MockModuleLoader:

        def __init__(self, module=None):
            self.module = module

        def all(self, base, permissions):
            return ["an.example.module", "an.other.module", "module.in.other.namespace"]

        def get(self, base, key):
            return self.module

    class MockReflector:

        def __init__(self):
            self.constructed = None
            self.deleted_all = False
            self.get_property_returns = None
            self.gotten_property = None
            self.invoked = None
            self.resolve_returns = None
            self.resolved = None

        def construct(self, klass):
            self.constructed = klass

        def deleteAll(self):
            self.deleted_all = True
        
        def getProperty(self, ref, property_name):
            self.gotten_property = (ref, property_name)

            if self.get_property_returns == None:
                return functools.partial(self._invoker, property_name)
            else:
                return self.get_property_returns

        def invoke(self, ref, method_name):
            self.invoked = (ref, method_name)

        def resolve(self, class_name):
            self.resolved = class_name

            return self.resolve_returns

        def _invoker(self, method_name, *args, **kwargs):
            return self.invoke(self, method_name)


    def testItShouldListAllFromTheModuleLoader(self):
        Module._Module__loader = ModuleTestCase.MockModuleLoader()

        assert Module.all() == ["an.example.module", "an.other.module", "module.in.other.namespace"]

    def testItShouldCalculateAModulesFQMN(self):
        assert ModuleTestCase.MockModule(MockSession(None)).fqmn() == "an.example.mockmodule"

    def testItShouldGetAModuleFromTheModuleLoader(self):
        Module._Module__loader = ModuleTestCase.MockModuleLoader()
        
        assert Module.get("an.example.module") == None

    def testItShouldReturnNoneIfTheModuleLoaderHasNoModule(self):
        Module._Module__loader = ModuleTestCase.MockModuleLoader("aModule")
        
        assert Module.get("an.example.module") == "aModule"

    def testItShouldCalculateAModulesNamespace(self):
        assert ModuleTestCase.MockModule(MockSession(None)).namespace() == "an.example"

    def testItShouldBuildAReflectedType(self):
        reflector = ModuleTestCase.MockReflector()
        assert isinstance(ModuleTestCase.MockModule(MockSession(reflector)).arg(5), ReflectedType)

    def testItShouldClearTheObjectStore(self):
        reflector = ModuleTestCase.MockReflector()
        ModuleTestCase.MockModule(MockSession(reflector)).clearObjectStore()

        assert reflector.deleted_all

    def testItShouldGetTheAgentContext(self):
        reflector = ModuleTestCase.MockReflector()
        reflector.resolve_returns = ReflectedObject(999, reflector=reflector)

        ModuleTestCase.MockModule(MockSession(reflector)).getContext()

        assert reflector.resolved == "com.reversec.droidhg.Agent"
        assert reflector.invoked[1] == "getContext"

    def testItShouldResolveAKlass(self):
        reflector = ModuleTestCase.MockReflector()
        ModuleTestCase.MockModule(MockSession(reflector)).klass("java.lang.String")

        assert reflector.resolved == "java.lang.String"

    def testItShouldInstantiateANewObject(self):
        reflector = ModuleTestCase.MockReflector()
        reflector.resolve_returns = "<class java.util.Random>"

        ModuleTestCase.MockModule(MockSession(reflector)).new("java.util.Random")

        assert reflector.constructed == "<class java.util.Random>"

    def testItShouldCallAddArgumentsWhenRunning(self):
        reflector = ModuleTestCase.MockReflector()
        module = ModuleTestCase.MockModule(MockSession(reflector))
        module.run([])

        assert isinstance(module.add_arguments_with, argparse.ArgumentParser)

    def testItShouldCallExecuteWhenRunning(self):
        reflector = ModuleTestCase.MockReflector()
        module = ModuleTestCase.MockModule(MockSession(reflector))
        module.run([])

        assert isinstance(module.execute_with, argparse.Namespace)

    def testItShouldInterceptARequestForUsageInformation(self):
        reflector = ModuleTestCase.MockReflector()
        module = ModuleTestCase.MockModule(MockSession(reflector))
        module.run(["-h"])

        assert module.add_arguments_with != None
        assert module.execute_with == None

    def testItShouldCleanUpTheObjectStoreAfterRunning(self):
        reflector = ModuleTestCase.MockReflector()
        module = ModuleTestCase.MockModule(MockSession(reflector))
        module.run([])

        assert reflector.deleted_all


def ModuleTestSuite():
    suite = unittest.TestSuite()

    suite.addTest(ModuleTestCase("testItShouldListAllFromTheModuleLoader"))
    suite.addTest(ModuleTestCase("testItShouldCalculateAModulesFQMN"))
    suite.addTest(ModuleTestCase("testItShouldGetAModuleFromTheModuleLoader"))
    suite.addTest(ModuleTestCase("testItShouldReturnNoneIfTheModuleLoaderHasNoModule"))
    suite.addTest(ModuleTestCase("testItShouldCalculateAModulesNamespace"))
    suite.addTest(ModuleTestCase("testItShouldBuildAReflectedType"))
    suite.addTest(ModuleTestCase("testItShouldClearTheObjectStore"))
    suite.addTest(ModuleTestCase("testItShouldGetTheAgentContext"))
    suite.addTest(ModuleTestCase("testItShouldResolveAKlass"))
    suite.addTest(ModuleTestCase("testItShouldInstantiateANewObject"))
    suite.addTest(ModuleTestCase("testItShouldCallAddArgumentsWhenRunning"))
    suite.addTest(ModuleTestCase("testItShouldCallExecuteWhenRunning"))
    suite.addTest(ModuleTestCase("testItShouldInterceptARequestForUsageInformation"))
    suite.addTest(ModuleTestCase("testItShouldCleanUpTheObjectStoreAfterRunning"))

    return suite
  
if __name__ == "__main__":
    unittest.TextTestRunner().run(ModuleTestSuite())
