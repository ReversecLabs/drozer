from reversec.common.twisted import StreamReceiver

class HttpReceiver(StreamReceiver):
    """
    Reads HTTP messages from a StreamReceiver.
    """
    
    def __init__(self, *args, **kwargs):
        pass

    def connectionMade(self):
        StreamReceiver.connectionMade(self)

    def buildMessage(self):
        """
        Attempts to read an HTTP Request from the stream.
        """
        
        return HTTPRequest.readFrom(self.stream)

    def streamReceived(self):
        """
        Called whenever the StreamReceiver is updated. Attempts to read a request from the stream
        returns the message if it receives one
        """
        
        message = self.buildMessage()

        if message is not None:
            self.requestReceived(message)
            

class HTTPMessage:

    crlf = "\r\n"
    version = "HTTP/1.1"
    
    def __init__(self, headers=None, body=None):
        """
        Create an HTTP Message
        """        
        
        self.headers = headers
        self.body = body
        
        if self.headers == None:
            self.headers = {}
    
    def format_headers(self):
        return "\r\n".join(map(lambda k: "%s: %s" % (k,self.headers[k]), self.headers))


class HTTPRequest(HTTPMessage):
    
    def __init__(self, verb="GET", resource="/", version="HTTP/1.1", headers=None, body=None):
        HTTPMessage.__init__(self, headers, body)
        
        self.resource = resource
        self.verb = verb
        self.version = version
    
    def isValid(self):
        return self.path in ["GET", "POST"] and self.version in ["HTTP/1.0", "HTTP/1.1"] 

    @classmethod
    def readHeaders(cls, stream):
        """
        Read the HTTP headers (terminated by a double-CRLF)
        """
        headers = b""
        
        bytes_read = 0
        while bytes_read != -1:
            pLength = len(headers)
            headers += stream.read(1)
            bytes_read = (len(headers) - pLength) -1
            # yaynoteyay
            # original code didn't escape backslashes, and didn't end with a single quote
            if str(headers).endswith("\\r\\n\\r\\n'"):
                return headers
            
        return None

    @classmethod
    def processHeader(cls, request):
        headers = []
        
        # yaynoteyay
        # original code didn't escape backslashes
        lines = str(request.strip()).rsplit("\\r\\n")
        if len(lines) < 1:
            return None
        
        # extract the verb, resource and version from the first line        
        verb, resource, version = cls.processRequest(lines[0])
        # then parse the remainder of the request for headers
        for line in lines[1:]:
            headers.append(line.split(": "))
        
        # formulate an HTTP message
        return HTTPRequest(verb, resource, version, dict(headers), None)
    
    @classmethod
    def processRequest(cls, line):
        """
        Read an HTTP request.
        """
        
        slice1 = line.index(" ")
        slice2 = line.rindex(" ")
        
        # yaynoteyay
        # the verb still contained `b'` at the beginning since the line was originally a byte thingy
        # so gotta remove `b'` from the beginning of the verb
        return (line[0:slice1].split("'")[1], line[slice1+1:slice2], line[slice2+1:])

    @classmethod
    def contentPresent(cls, message):
        """
        get the length of the body
        returns -1 if not present
        """
        for header in message.headers:
            if header[0] == "Content-Length":
                try:
                    return int(header[1])
                except ValueError: 
                    return -1
        return -1

    @classmethod
    def readFrom(cls, stream):
        """
        Try to read HTTP Requests from the stream.
        """

        position = stream.tell()
        message = None
        header = HTTPRequest.readHeaders(stream)
        
        if header == None:
            stream.seek(position)
        else:
            message = HTTPRequest.processHeader(header)

        if message == None:
            return None
        else:
            if "Content-Length" in message.headers:
                length = int(message.headers["Content-Length"])
                if length > 0:
                    body = stream.read(length)
                    if len(body) >= length:
                        message.body = body
                    else:
                        stream.seek(position)
                        
                        return None
            return message
    
    def writeTo(self, socket):
        request_data = str(self)
        sent = 0
        
        while sent < len(request_data):
            sent += socket.send(request_data[sent:])
        
        return sent
    
    def __str__(self):
        return "%s %s %s\r\n%s\r\n\r\n%s" % (self.verb, self.resource, self.version, self.format_headers(), self.body)


class HTTPResponse(HTTPMessage):
    
    def __init__(self, status=200, version="HTTP/1.1", headers=None, body=""):
        HTTPMessage.__init__(self, headers, body)
        
        self.status = status
        
        if "Content-Length" not in self.headers:
            self.headers["Content-Length"] = len(body)
    
    @classmethod
    def parse(cls, message):
        lines = message.split("\r\n")
        
        version, status = cls.processResponse(lines[0])
        headers = cls.processHeaders(lines[1:lines.index("")])
        body = "\r\n".join(lines[lines.index("")+1:])
        
        return HTTPResponse(status, version, headers, body)
    
    @classmethod
    def processHeaders(cls, lines):
        """
        Read headers from an HTTP response.
        """
        
        return dict(map(lambda l: [l[0:l.index(": ")], l[l.index(": ")+2:]], lines))
    
    @classmethod
    def processResponse(cls, line):
        """
        Read an HTTP response.
        """
        
        slices = line.split(" ")
        
        return (slices[0], int(slices[1]))
    
    @classmethod
    def readFrom(cls, socket):
        """
        Try to read an HTTP Response from a Socket
        """
        
        resp = ""
        
        while resp.find("\r\n\r\n") == -1:
            resp += socket.recv(10)
            
            if len(resp) == 0:
                return None
        
        return HTTPResponse.parse(resp)
    
    def status_text(self):
        return { 100: "Continue",
                 101: "Switching Protocols",
                 200: "OK",
                 201: "Created",
                 202: "Accepted",
                 203: "Non-Authoritative Information",
                 204: "No Content",
                 205: "Reset Content",
                 206: "Partial Content",
                 300: "Multiple Choices",
                 301: "Moved Permanently",
                 302: "Found",
                 303: "See Other",
                 304: "Not Modified",
                 305: "Use Proxy",
                 307: "Temporary Redirect",
                 400: "Bad Request",
                 401: "Unauthorized",
                 402: "Payment Required",
                 403: "Forbidden",
                 404: "Not Found",
                 405: "Method Not Allowed",
                 406: "Not Acceptable",
                 407: "Proxy Authentication Required",
                 408: "Request Timeout",
                 409: "Conflict",
                 410: "Gone",
                 411: "Length Required",
                 412: "Precondition Failed",
                 413: "Request Entity Too Large",
                 414: "Request-URI Too Long",
                 415: "Unsupported Media Type",
                 416: "Requested Range Not Satisfiable",
                 417: "Expectation Failed",
                 418: "I'm a teapot",
                 500: "Internal Server Error",
                 501: "Not Implemented",
                 502: "Bad Gateway",
                 503: "Service Unavailable",
                 504: "Gateway Timeout",
                 505: "HTTP Version Not Supported" }[self.status]
    
    def __str__(self):
        if self.body == None:
            return "%s %d %s\r\n%s\r\n\r\n" % (self.version, self.status, self.status_text(), self.format_headers())
        else:
            return "%s %d %s\r\n%s\r\n\r\n%s" % (self.version, self.status, self.status_text(), self.format_headers(), self.body)
        
