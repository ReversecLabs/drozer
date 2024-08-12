from xml.etree import ElementTree as xml

class Endpoint(object):
    
    def __init__(self, path):
        self.__path = path

        with open(self.__path, 'w+') as file:
            lines = file.readlines()
        self.data = dict(map(lambda x: x.split(":"), filter(lambda p: p.find(":") > -1, lines)))
    
    def put_server(self, server):
        if isinstance(server, tuple):
            self.data["host"], self.data["self.port"] = server
        else:
            if server.find(":") > -1:
                self.data["host"], self.data["self.port"] = server.split(":")
            else:
                self.data["host"] = server

    def put(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data[key]
    
    def write(self):
        with open(self.__path, 'w') as file:
            file.write("drozer Config\n")
            for key, value in self.data.items():
                file.write(f"{key}:{value}\n")


class Manifest(object):
    
    def __init__(self, path):
        self.__path = path

        with open(self.__path, 'r') as file:
            self.__doc = xml.fromstring(file.read())
    
    def add_permission(self, name):
        node = xml.Element('uses-permission')
        node.attrib["ns0:name"] = name
        
        self.__doc.insert(len(list(self.__doc)) - 1, node)

    def define_permission(self, name, protectionLevel):
        node = xml.Element('permission')
        node.attrib["ns0:name"] = name
        node.attrib["ns0:protectionLevel"] = protectionLevel
        
        self.__doc.insert(len(list(self.__doc)) - 1, node)
        
    def permissions(self):
        return list(map(lambda x: x.attrib['{http://schemas.android.com/apk/res/android}name'],
                        self.__doc.findall('uses-permission')))

    def write(self):
        xml.ElementTree(self.__doc).write(self.__path)

    def version(self):
        return self.__doc.attrib['{http://schemas.android.com/apk/res/android}versionName']

    def tree(self):
        return self.__doc
