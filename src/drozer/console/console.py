import getpass
import sys
import warnings
import traceback

from pysolar.api.protobuf_pb2 import Message
from pysolar.api.transport.exceptions import ConnectionError
from pysolar.reflection import ReflectionException

from reversec.common import cli, path_completion

from drozer import meta
from drozer.api.formatters import SystemResponseFormatter
from drozer.connector import ServerConnector
from drozer.console.session import Session, DebugSession

class Console(cli.Base):
    """
    drozer console [OPTIONS] COMMAND
    
    Starts a new drozer Console to interact with an Agent.

    The drozer Console connects to an Agent and allows you to interact with the
    system from the context of the agent application on the device. The console
    can connect directly to an agent, if its embedded server is enabled, or through
    a drozer Server that the agent is connected to.
    """

    def __init__(self):
        cli.Base.__init__(self)
        
        self._parser.add_argument("device", default=None, nargs='?', help="the unique identifier of the Agent to connect to")
        self._parser.add_argument("--server", default=None, metavar="HOST[:PORT]", help="specify the address and port of the drozer server")
        self._parser.add_argument("--ssl", action="store_true", default=False, help="connect with TLS (this is the default)")
        self._parser.add_argument("--no-ssl", action="store_true", default=False, help="disable TLS and connect with plain TCP")
        self._parser.add_argument("--accept-certificate", action="store_true", default=False, help="accept any SSL certificate with a valid trust chain")
        self._parser.add_argument("--verify-tls", action="store_true", default=False, help="manually verify the TLS certificate fingerprint on first connect")
        self._parser.add_argument("--debug", action="store_true", default=False, help="enable debug mode")
        self._parser.add_argument("--no-color", action="store_true", default=False, help="disable syntax highlighting in drozer output")
        self._parser.add_argument("--password", nargs="?", const=True, default=None, metavar="PASSWORD",
                                  help="provide a password (interactive prompt if no value given)")
        self._parser.add_argument("--no-password", action="store_true", default=False, help="connect without a password prompt")
        self._parser.add_argument("-c", "--command", default=None, dest="onecmd", help="specify a single command to run in the session")
        self._parser.add_argument("-f", "--file", default=[], help="source file", nargs="*")
        
        self.__accept_certificate = False
        self.__verify_tls = False
        self.__tls_security_phrase = None
        self.__server = None
        
    def do_connect(self, arguments):
        """starts a new session with a device"""

        # Password handling: default is interactive prompt (user can just hit Enter
        # for no password). --password VALUE provides it inline. --no-password skips.
        if arguments.no_password:
            password = None
        elif arguments.password is True:
            # --password with no value: interactive prompt
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                password = getpass.getpass()
        elif arguments.password is not None:
            # --password VALUE: inline
            password = arguments.password
        else:
            # No flag at all: prompt (Enter for no password)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                password = getpass.getpass("Password (leave blank if none): ")
            if password == "":
                password = None

        # TLS is the default. --no-ssl is required to explicitly disable it.
        if not arguments.no_ssl:
            arguments.ssl = True

        if not arguments.ssl:
            sys.stderr.write("Warning: connecting without TLS. Traffic is unencrypted.\n\n")

        server = self.__getServerConnector(arguments)
        device = self.__get_device(arguments)
        response = server.startSession(device, password)
        if response.type == Message.SYSTEM_RESPONSE and\
            response.system_response.status == Message.SystemResponse.SUCCESS:
            session_id = response.system_response.session_id
            session = None
            try:
                if(arguments.debug):
                    session = DebugSession(server, session_id, arguments)
                else:
                    session = Session(server, session_id, arguments)
                if self.__tls_security_phrase:
                    session.intro += "\nTLS security phrase: %s  -- verify this matches the agent" % self.__tls_security_phrase
                if len(arguments.file) > 0:
                    print("Length is above 0")
                    session.do_load(" ".join(arguments.file))
                    session.do_exit("")
                elif arguments.onecmd != None:
                    session.onecmd(arguments.onecmd)
                    session.do_exit("")
                else:
                    session.cmdloop()
            except KeyboardInterrupt:
                print("Caught SIGINT, terminating your session.")
            except ReflectionException as e:
                if("cannot resolve com.reversec.dz.Agent" in str(e)):
                    sys.stderr.write("It seems that you are running an unsupported version of drozer-agent. Please update your copy.\n\nTo download the latest drozer-agent visit:\nhttps://github.com/ReversecLabs/drozer-agent/releases\n")
                if(arguments.debug):
                    self.handleException(e, arguments, session)
            except Exception as e:
                self.handleException(e, arguments, session)
            finally:
                if session is not None:
                    session.do_exit("")
                return
                
            self.__getServerConnector(arguments).close()
        else:
            self.handle_error(RuntimeError(response.system_response.error_message), fatal=True)

    def handleException(self, e, arguments=None, session=None):
        # session might not exist here, so let's accept some code duplication
        if session is not None:
            session.handleException(e)
        elif(arguments.debug):
            sys.stderr.write("exception in: {}: {}\n".format(e.__class__.__name__, str(e)))
            sys.stderr.write("%s\n"%traceback.format_exc())
        else:
            sys.stderr.write("Exception occured: %s\n" % str(e))

    def do_devices(self, arguments):
        """lists all devices bound to the drozer server"""
        response = self.__getServerConnector(arguments).listDevices()

        print(SystemResponseFormatter.format(response))

        self.__getServerConnector(arguments).close()

    def do_disconnect(self, arguments):
        """disconnects a drozer session"""

        response = self.__getServerConnector(arguments).stopSession(arguments.device)

        print(SystemResponseFormatter.format(response))
        
        self.__getServerConnector(arguments).close()
        
    def do_version(self, arguments):
        """display the installed drozer version"""
        
        meta.print_version()
        
    def get_completion_suggestions(self, action, text, line, **kwargs):
        if action.dest == "server":
            return ["localhost:31415"]
        elif action.dest == "file":
            return path_completion.complete(text)
        elif action.dest == "device":
            return None
        elif action.dest == "onecmd":
            return None
        
    def handle_error(self, throwable, fatal=False):
        """error handler: shows an exception message, before terminating"""
        
        if str(throwable) == "connection reset by peer":
            sys.stderr.write("The drozer Server is not available. Please double check the address and port.\n\n")
        elif str(throwable) == "'NoneType' object has no attribute 'id'":
            sys.stderr.write("Expected a response from the server, but there was none.\nThe server may be unavailable, or may be expecting you to connect using SSL.\n\n")
        elif isinstance(throwable, ConnectionError) or fatal == True:
            sys.stderr.write("There was a problem connecting to the drozer Server.\n\n")
            sys.stderr.write("Things to check:\n\n")
            sys.stderr.write(" - is the drozer Server running?\n")
            sys.stderr.write(" - have you set up appropriate adb port forwards?\n")
            sys.stderr.write(" - have you specified the correct hostname and port with --server?\n")
            sys.stderr.write(" - is the agent not using TLS? (use --no-ssl only if you're sure)\n")
            sys.stderr.write(" - is the agent protected with a password?\n\n")
            if(hasattr(throwable, 'cause')):
                sys.stderr.write("Debug Information:\n")
                sys.stderr.write("%s\n\n" % str(throwable.cause))
            
            sys.exit(1)
        else:
            cli.Base.handle_error(self, throwable)
    
    def parse_arguments(self, parser, arguments):
        parsed_arguments = parser.parse_args(arguments)

        if parsed_arguments.accept_certificate:
            self.__accept_certificate = True
        if parsed_arguments.verify_tls:
            self.__verify_tls = True

        return parsed_arguments

    def __get_device(self, arguments):
        """
        Determines which device to request after connecting to the server.
        """
        if arguments.device == None:
            devices = self.__getServerConnector(arguments).listDevices().system_response.devices

            if len(devices) == 1:
                device = devices[0].id

                print("Selecting %s (%s %s %s)\n" % (devices[0].id, devices[0].manufacturer, devices[0].model, devices[0].software))
                return device
            elif len(devices) == 0:
                print("No devices available.\n")

                sys.exit(-1)
            else:
                print("More than one device available. Please specify the target device ID.\n")

                sys.exit(-1)
        else:
            return arguments.device

    def __getServerConnector(self, arguments):
        """
        Get a Server object which provides a connection to the selected server.
        """

        if self.__server is None:
            self.__server = ServerConnector(arguments, self.__manage_trust)

        return self.__server
    
    def __manage_trust(self, provider, certificate, peer):
        """
        Callback, invoked when connecting to a server with SSL, to manage the trust
        relationship with that server based on SSL certificates.
        """

        trust_status = provider.trusted(certificate, peer)
        phrase = provider.security_phrase(certificate)

        if trust_status == 0:
            # Known and matches — trusted, nothing to do.
            self.__tls_security_phrase = phrase
            return

        if trust_status == -2:
            # Certificate CHANGED — always warn, possible MITM.
            sys.stderr.write("\n!! WARNING: TLS certificate has CHANGED for %s:%d !!\n" % peer)
            sys.stderr.write("!! This could indicate a man-in-the-middle attack. !!\n\n")
            sys.stderr.write("Previous fingerprint: %s\n" % provider.trusted_certificate_for(peer))
            sys.stderr.write("Current fingerprint:  %s\n" % provider.digest(certificate))
            if phrase:
                sys.stderr.write("Current security phrase: %s\n" % phrase)
            sys.stderr.write("\nVerify this matches the phrase shown on the device.\n")

            while True:
                sys.stderr.write("Accept the new certificate? [yna] ")
                selection = input().strip().lower()
                if selection == "n":
                    sys.exit(-2)
                elif selection == "y":
                    self.__tls_security_phrase = phrase
                    return
                elif selection == "a":
                    provider.trust(certificate, peer)
                    self.__tls_security_phrase = phrase
                    return

        # trust_status == -1: new/unknown certificate
        if self.__verify_tls:
            # Manual verification mode — interactive prompt.
            print("\ndrozer has established an SSL Connection to %s:%d." % peer)
            print("The server has provided an SSL Certificate with the SHA-256 Fingerprint:")
            print("%s" % provider.digest(certificate))
            if phrase:
                print("Security phrase: %s" % phrase)
            print("\nVerify this matches the phrase shown on the device.")

            while True:
                print("Do you want to accept this certificate? [yna] ")
                selection = input().strip().lower()
                if selection == "n":
                    sys.exit(-2)
                elif selection == "y":
                    self.__tls_security_phrase = phrase
                    return
                elif selection == "a":
                    print("Adding certificate to known hosts.\n")
                    provider.trust(certificate, peer)
                    self.__tls_security_phrase = phrase
                    return
        else:
            # Default: auto-accept and remember. Print phrase after session starts.
            provider.trust(certificate, peer)
            self.__tls_security_phrase = phrase
