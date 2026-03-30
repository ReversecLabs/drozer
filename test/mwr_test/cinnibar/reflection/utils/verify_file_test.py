import unittest, md5

from mwr.cinnibar.reflection.utils import ClassLoader
from mwr.cinnibar.reflection import ReflectionException


class MockRemoteVerify():

    def __init__(self):
        pass

    def md5sum(self, fileObj):
        return md5.new(fileObj.data).digest().encode("hex")

class MockFileInputStream():
    
    def __init__(self, someobject):
        self.data = someobject.data
        self.pos = 0

    def read():
        if self.pos >= len(self.data):
            return -1
        else:
            returnVal = self.data[self.pos]
            self.pos += 1
            return returnVal

class MockFile():

    def __init__(self, data):
        self.data = data

    def exists(self):

        return self.data != None

    def length():
        return len(self.data)

class VerifyFileTestCase(unittest.TestCase):

    def remoteFunctionPresent(self):
        """
        Simulating construction of java objects. verify_file only uses the two methods below
        """
        
        def constructor(*args, **kwargs):
            if args[0] == "com.reversec.droidhg.util.Verify":
                return MockRemoteVerify()
            if args[0] == "java.io.FileInputStream":
                return MockFileInputStream(kwargs)
        
        return constructor
    
    def remoteFunctionNotPresent(self):
        """
        raises a reflection exception to simulate the method missing form the agent
        """

        def constructor(*args, **kwargs):
            if args[0] == "com.reversec.droidhg.util.Verify":
                raise ReflectionException
            if args[0] == "java.io.FileInputStream":
                return MockFileInputStream(kwargs)
            

    def setUp(self):
        self.constructor = self.remoteFunctionPresent()
        self.testObject = ClassLoader("", None, self.constructor, None)

        self.localMatches = "thisisafilethatwillbeusedinthehashing"
        self.remoteMatches = MockFile(self.localMatches)
        self.localNMatches = "thisisafilethatDOESNOTmatchtheremotehashfile"
        self.remoteNMatches = MockFile(self.localNMatches)

    def testRemoteNotPresentLocalNotPresent(self):
        
        self.assertFalse(self.testObject._ClassLoader__verify_file(None, None))

    def testRemotePresentLocalNotPresent(self):

        self.assertFalse(self.testObject._ClassLoader__verify_file(self.remoteMatches, None))

    def testRemoteNotPresentLocalPresent(self):

        self.assertFalse(self.testObject._ClassLoader__verify_file(None, self.localMatches))

    def testRemotePresentLocalPresent(self):

        self.assertTrue(self.testObject._ClassLoader__verify_file(self.remoteMatches, self.localMatches))

    def testRemoteDoesNotExistLocalNotPresent(self):

        self.assertFalse(self.testObject._ClassLoader__verify_file(MockFile(None), None))

    def testRemoteDoesNotExistLocalPresent(self):

        self.assertFalse(self.testObject._ClassLoader__verify_file(MockFile(None), self.localMatches))

    def testCanUseRemoteAgentAndLocalMatches(self):

        self.assertTrue(self.testObject._ClassLoader__verify_file(self.remoteMatches, self.localMatches))

    def testCanUseRemoteAgentAndLocalDoesNotMatch(self):
  
        self.assertFalse(self.testObject._ClassLoader__verify_file(self.remoteMatches, self.localNMatches))

    def testCannotUseRemoteAgentAndLocalMatches(self):

        self.testObject.constructor = self.remoteFunctionNotPresent()
        self.assertTrue(self.testObject._ClassLoader__verify_file(self.remoteMatches, self.localMatches))

    def testCannotUseRemoteAgentAndLocalDoesNotMatch(self):

        self.testObject.constructor = self.remoteFunctionNotPresent()
        self.assertFalse(self.testObject._ClassLoader__verify_file(self.remoteMatches, self.localNMatches))

def VerifyFileTestSuite():
    suite = unittest.TestSuite()

    suite.addTest(VerifyfileTestCase("testRemoteNotPresentLocalNotPresent"))
    suite.addTest(VerifyfileTestCase("testRemotePresentLocalNotPresent"))
    suite.addTest(VerifyfileTestCase("testRemoteNotPresentLocalPresent"))
    suite.addTest(VerifyfileTestCase("testRemotePresentLocalPresent"))
    suite.addTest(VerifyfileTestCase("testRemoteDoesNotExistLocalNotPresent"))
    suite.addTest(VerifyfileTestCase("testRemoteDoesNotExistLocalPresent"))
    suite.addTest(VerifyfileTestCase("testCanUseRemoteAgentAndLocalMatches"))
    suite.addTest(VerifyfileTestCase("testCanUseRemoteAgentAndLocalDoesNotMatch"))
    suite.addTest(VerifyfileTestCase("testCannotUseRemoteAgentAndLocalMatches"))
    suite.addTest(VerifyfileTestCase("testCannotUseRemoteAgentAndLocalDoesNotMatch"))

    return suite

if __name__ == "__main__":
    unittest.main()
            
            
