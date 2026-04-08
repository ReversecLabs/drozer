import socket
import traceback

from pysolar.api.builders import SystemRequestFactory
from pysolar.api.transport import SocketTransport
from pysolar.api.transport.exceptions import ConnectionError

class ServerConnector(SocketTransport):
    """
    The Server model represents a connection between a Console and a drozer
    Server (or embedded Agent Server).

    The model is responsible for establishing the connection, and sending and
    receiving Frames on the wire.
    """

    DefaultHost = "127.0.0.1"
    DefaultPort = 31415
    
    def __init__(self, arguments, trust_callback=None):
        try:
            SocketTransport.__init__(self, arguments, trust_callback)
        except socket.error as e:
            if getattr(arguments, 'debug', False):
                traceback.print_exc()
            print("Socket Error")
            raise ConnectionError(e)
        except socket.timeout as e:
            if getattr(arguments, 'debug', False):
                traceback.print_exc()
            print("Other Socket Timout")
            raise ConnectionError(e)

    def listDevices(self):
        """
        Get a list of Devices boud to the Server.
        """

        try:
            datum = self.sendAndReceive(SystemRequestFactory.listDevices())
            return datum
        except RuntimeError as e:
            if str(e) == 'Received an empty response from the Agent. This normally means the remote service has crashed.':
                raise ConnectionError(e)
            else:
                raise

    def listSessions(self):
        """
        Get a list of active sessions on the Server.
        """

        try:
            return self.sendAndReceive(SystemRequestFactory.listSessions())
        except RuntimeError as e:
            if str(e) == 'Received an empty response from the Agent. This normally means the remote service has crashed.':
                raise ConnectionError(e)
            else:
                raise

    def startSession(self, device_id, password):
        """
        Start a new Session with a Device known to the Server.
        """

        try:
            return self.sendAndReceive(SystemRequestFactory.startSession(device_id).setPassword(password))
        except RuntimeError as e:
            if str(e) == 'Received an empty response from the Agent. This normally means the remote service has crashed.':
                raise ConnectionError(e)
            else:
                raise

    def stopSession(self, session_id):
        """
        Stop an active Session, known to the Server.
        """
        
        self.setTimeout(1.0)

        return self.sendAndReceive(SystemRequestFactory.stopSessionId(session_id))
        