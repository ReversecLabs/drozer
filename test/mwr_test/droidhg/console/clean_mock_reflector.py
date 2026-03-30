
class MockReflector():

    def __init__(self):
        self.cache_delete_valid = [MockFile("thisisdex.dex"), MockFile("thisisapk.apk"), MockFile(".dex"), MockFile(".apk"), MockFile("dex"), MockFile("apk"), MockFile("somefile"), MockFile("fakedex.dexz"), MockFile("fakeapk.apkz")]
        self.klass = MockKlass(self.cache_delete_valid)
    
    def resolve(self,klass='com.reversec.droidhg.Agent'):
        return self.klass


class MockKlass:

    def __init__(self, cache):
        self.context = MockContext(cache)

    def getContext(self):
        return self.context

class MockContext:
        
    def __init__(self, cache):
        self.cache = MockCache(cache)

    def getCacheDir(self):
        return self.cache

class MockCache:

    def __init__(self, cache):
        self.files = cache

    def listFiles(self):
        if self.files is None:
            return []
        else:    
            return self.files


class MockFile:
        
    def __init__(self, name):
        self.name = name

    def toString(self):
        return self.name

    def delete(self):
        self.name = "---"



