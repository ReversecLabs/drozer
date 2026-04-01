from base64 import b64encode
from socket import socket
import ssl

from drozer.server.receivers.http import HTTPRequest, HTTPResponse
from drozer.ssl.provider import Provider

def delete(arguments, resource):
    sock = get_socket(arguments)
    
    request = HTTPRequest(verb="DELETE", resource=resource)
    
    request.writeTo(sock)
    response = HTTPResponse.readFrom(sock)
    
    if response:
        return response.status == 200
    else:
        return False

def get_socket(arguments):
    sock = socket()

    if hasattr(arguments, 'push_server') and arguments.push_server != None:
        target = arguments.push_server
    else:
        target = arguments.server
    hostname = target[0] if isinstance(target, tuple) else target.split(":")[0] if target else "127.0.0.1"

    if arguments.ssl:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        sock = context.wrap_socket(sock, server_hostname=hostname)

    sock.settimeout(5.0)
    sock.connect(target)
    
    return sock
    
def upload(arguments, resource, data, magic=None, mimetype=None, headers=None):
    sock = get_socket(arguments)
    
    request = HTTPRequest(verb="POST", resource=resource, headers=headers, body=data)
    if arguments.credentials != None:
        request.headers["Authorization"] = "Basic %s" % b64encode(":".join(arguments.credentials))
    request.headers["Content-Length"] = len(data)
    if mimetype != None:
        request.headers["Content-Type"] = mimetype
    if magic != None:
        request.headers["X-Drozer-Magic"] = magic
        
    request.writeTo(sock)
    response = HTTPResponse.readFrom(sock)

    return response.status == 201
