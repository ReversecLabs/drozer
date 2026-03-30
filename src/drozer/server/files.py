import re

from reversec.common import fs

from drozer.server.receivers.http import HTTPResponse

import traceback

class FileProvider(object):
    
    def __init__(self, store={}):
        self.__store = store

    def add(self, path, resource):
        self.__store[path] = resource

    def count(self):
        return len(self.__store)
    
    def create(self, resource, body, magic=None, mimetype=None, multipart=None, custom_headers=None):
        if multipart == None:
            self.__store[resource] = InMemoryResource(resource, body, magic=magic, mimetype=mimetype, custom_headers=custom_headers)
            
            return self.__store[resource].getBody() == body
        else:
            self.__store[resource] = InMemoryMultipartResource(resource, body, boundary=multipart.split("=")[1], magic=magic, mimetype=mimetype, custom_headers=custom_headers)
            
            
            return self.__store[resource].valid()
        
    def delete(self, resource):
        del self.__store[resource]
        
    def get(self, resource):
        for key in self.__store:
            if re.match("^" + key  + "$", resource) != None:
                return self.__store[key]
        
        return ErrorResource(resource, 404, "The resource %s could not be found on this server.")
    
    def get_by_magic(self, magic):
        resources = filter(lambda r: self.__store[r].magic == magic, self.__store)
        
        if len(resources) == 1:
            return self.__store[resources[0]]
        else:
            return None
    
    def has_magic_for(self, magic):
        resources = list(filter(lambda r: self.__store[r].magic == magic, self.__store))

        if len(resources) == 1:
            return True
        else:
            return False
        
        
class Resource(object):
    
    def __init__(self, resource, magic=None, reserved=False, custom_headers=None):
        self.downloadCount = {}
        self.resource = resource
        self.reserved = reserved
        self.magic = magic
        self.custom_headers = custom_headers

    def download(self, path):
        if not path in self.downloadCount:
            self.downloadCount[path] = 1
        else:
            self.downloadCount[path] += 1
 
    def getBody(self):
        return None

    def getResponse(self, request):
        return None


class CreatedResource(Resource):
    
    def __init__(self, resource):
        Resource.__init__(self, resource, False)
        
        self.code = 201
        self.description = "Location: %s"
        self.resource = resource
    
    def getBody(self):
        return "<h1>%d %s</h1><p>%s</p><hr/><p>Web Server</p>" % (self.code, HTTPResponse(status=self.code).status_text(), self.description % self.resource)
    
    def getResponse(self, request):
        return HTTPResponse(status=self.code, headers={ "Location": self.resource }, body=self.getBody())
        
    
class ErrorResource(Resource):
    
    def __init__(self, resource, code, description):
        Resource.__init__(self, resource, False)
        
        self.code = code
        self.description = description
    
    def getBody(self):
        return "<h1>%d %s</h1><p>%s</p><hr/><p>Web Server</p>" % (self.code, HTTPResponse(status=self.code).status_text(), self.description % self.resource)
    
    def getResponse(self, request):
        return HTTPResponse(status=self.code, body=self.getBody())
        
        
class FileResource(Resource):
    
    def __init__(self, resource, path, magic=None, reserved=False, type="text/plain", custom_headers=None):
        Resource.__init__(self, resource, magic=magic, reserved=reserved, custom_headers=custom_headers)
        
        self.path = path
        self.type = type
    
    def getBody(self):
        return fs.read(self.path)
            
    def getResponse(self, request):
        response = HTTPResponse(status=200, body=self.getBody())
        response.headers["Content-Type"] = self.type
        
        return response

class InMemoryMultipartResource(Resource):
    
    def __init__(self, resource, body, boundary, magic=None, mimetype=None, custom_headers=None):
        Resource.__init__(self, resource, magic=magic, reserved=False, custom_headers=custom_headers)
        
        self.body = {}
        self.mimetype = mimetype
        self.__valid = False
        
        for part in re.split("^--" + boundary + "; ([^$]+)$", body):
            if part.strip() == "":
                continue
            
            self.body[part[0:part.find("\n")]]  = part[part.find("\n")+1:]
        
        self.__valid = len(self.body) > 0
    
    def getBody(self, user_agent):
        for k in self.body:
            if re.match(k, user_agent) != None:
                return self.body[k]
            
        return None
    
    def getResponse(self, request):
        headers = {}
        if self.mimetype != None:
            headers['Content-Type'] = self.mimetype
            
        body = self.getBody(request.headers['User-Agent'])

        headers = dict(headers.items() + self.custom_headers.items())
        
        if body != None:
            return HTTPResponse(status=200, headers=headers, body=body)
        else:
            return ErrorResource(request.resource, 404, "The resource %s could not be found on this server.").getResponse(request)
    
    def valid(self):
        return self.__valid
    
class InMemoryResource(Resource):
    
    def __init__(self, resource, body, magic=None, mimetype=None, custom_headers=None):
        Resource.__init__(self, resource, magic=magic, reserved=False, custom_headers=custom_headers)
        
        self.body = body
        self.mimetype = mimetype
    
    def getBody(self):
        return self.body
            
    def getResponse(self, request):
        headers = {}
        if self.mimetype != None:
            headers['Content-Type'] = self.mimetype

        # yaynoteyay
        # old code didn't combine dictionaries properly
        headers.update(self.custom_headers)
        
        return HTTPResponse(status=200, headers=headers, body=self.getBody())
   
class StatusResource(Resource):

    def __init__(self, resource, fileProvider):
        Resource.__init__(self, resource, False)

        self.__fileProvider = fileProvider

    def getBody(self, path):
        if path == "":
            return "This server has " + str(self.__fileProvider.count()) + " files."
        else:
            downloadCounts = self.__fileProvider.get(path).downloadCount

            if path in downloadCounts:
                return str(downloadCounts[path])
            else:
                return "0"

    def getResponse(self, request):
        return HTTPResponse(status=200, headers={}, body=self.getBody(request.resource[8:]))
 
