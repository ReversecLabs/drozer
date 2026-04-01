import socket
import ssl
import sys

from pysolar.api import Frame
from pysolar.api.transport.exceptions import ConnectionError
from pysolar.api.transport.transport import Transport

from drozer.ssl.provider import Provider  # TODO: eugh


class SocketTransport(Transport):

    def __init__(self, arguments, trust_callback=None):
        Transport.__init__(self)
        self.__socket = socket.socket()

        self.__debug = getattr(arguments, 'debug', False)
        endpoint = self.__getEndpoint(arguments)

        if arguments.ssl:
            provider = Provider()
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # TOFU handles trust via fingerprint callback
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            # Include AES-CBC ciphers for Android API 16-19 which lack GCM support
            context.set_ciphers("DEFAULT:!aNULL:!eNULL:!MD5")

            if self.__debug:
                sys.stderr.write("[TLS] Connecting to %s:%d\n" % endpoint)
                sys.stderr.write("[TLS] Protocol: TLS_CLIENT, verify_mode: CERT_NONE, min_version: TLSv1_2\n")

            self.__socket = context.wrap_socket(self.__socket, server_hostname=endpoint[0])

        self.setTimeout(90.0)

        try:
            self.__socket.connect(endpoint)
        except ssl.SSLError as e:
            if self.__debug:
                sys.stderr.write("[TLS] Handshake failed during connect: %s\n" % e)
            raise

        if arguments.ssl:
            if self.__debug:
                sys.stderr.write("[TLS] Handshake successful\n")
                sys.stderr.write("[TLS] Protocol: %s, Cipher: %s\n" % (
                    self.__socket.version(), self.__socket.cipher()))
                cert_der = self.__socket.getpeercert(True)
                sys.stderr.write("[TLS] Server cert DER length: %d bytes\n" % (len(cert_der) if cert_der else 0))

            trust_callback(provider, self.__socket.getpeercert(True), self.__socket.getpeername())

    def close(self):
        """
        Close the connection to the Server.
        """

        self.__socket.close()

    def receive(self):
        """
        Receive a Message from the Server.

        If not frame is available, None is returned.
        """

        try:
            frame = Frame.readFromSocket(self.__socket)
            if frame is not None:
                return frame.message()
            else:
                return None
        except socket.timeout as e:
            print("TimeoutError")
            raise ConnectionError(e)
        except ssl.SSLError as e:
            print("SSLError")
            raise ConnectionError(e)

    def send(self, message):
        """
        Send a Message to the Server.

        The Message is automatically assigned an identifier, and this is
        returned.
        """

        try:
            message_id = self.nextId()
            self.__socket.sendall(bytes(Frame.fromMessage(message.setId(message_id).build())))
            return message_id
        except socket.timeout as e:
            print("Funcopop Error")
            raise ConnectionError(e)
        except ssl.SSLError as e:
            print("SSL Error but lowsend")
            raise ConnectionError(e)
        except socket.error as e:
            print(e)
            raise ConnectionError(e)

    def sendAndReceive(self, message):
        """
        Send a Message to the Server, and wait for the response to be received.
        """
        message_id = self.send(message)
        while (True):
            response = self.receive()
            if response == None:
                raise ConnectionError(RuntimeError('Received an empty response from the Agent.'))
            elif response.id == message_id:
                return response

    def setTimeout(self, timeout):
        """
        Change the read timeout on the socket.
        """

        self.__socket.settimeout(timeout)

    def __getEndpoint(self, arguments):
        """
        Decode the Server endpoint parameters, from an ArgumentParser arguments
        object with a server member.

        This extracts the hostname and port, assigning a default if they are
        not provided.
        """

        if arguments.server != None:
            endpoint = arguments.server
        else:
            endpoint = ":".join([self.DefaultHost, str(self.DefaultPort)])

        if ":" in endpoint:
            host, port = endpoint.split(":")
        else:
            host = endpoint
            port = self.DefaultPort

        return (host, int(port))
