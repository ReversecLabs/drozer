"""
Programmatic API for drozer

This module provides a programmatic interface to drozer for running modules
and capturing their output in Python scripts without using the interactive console.

Example usage:
    ```python
    from drozer.api import ProgrammaticSession
    from drozer.connector import ServerConnector

    # Connect to drozer server
    server = ServerConnector()
    server.connect(host="localhost", port=31415)

    # Start session with device
    response = server.startSession("device_id", password=None)
    session_id = response.system_response.session_id

    # Create programmatic session
    session = ProgrammaticSession(server, session_id)

    # Run a module and get results
    result = session.run_module("app.package.list", ["-f", "browser"])

    if result.success:
        print("Packages found:")
        print(result.output)
    else:
        print("Error:", result.errors)

    # Cleanup
    session.close()
    server.close()
    ```
"""

import shlex
import sys
import traceback
from io import StringIO
from typing import List, Union, Optional, Any

from drozer.console.session import Session


class ModuleResult:
    """
    Represents the result of a module execution.

    Attributes:
        output (str): Captured stdout from the module
        errors (str): Captured stderr from the module
        return_value (Any): The value returned by the module's execute() method
        exception (Exception): Any exception raised during execution, or None
        success (bool): True if execution completed without exceptions
    """

    def __init__(self, output: str, errors: str, return_value: Any = None,
                 exception: Optional[Exception] = None):
        """
        Initialize a ModuleResult.

        Args:
            output: Captured stdout content
            errors: Captured stderr content
            return_value: Value returned by module execution
            exception: Exception if execution failed, None otherwise
        """
        self.output = output
        self.errors = errors
        self.return_value = return_value
        self.exception = exception

    @property
    def success(self) -> bool:
        """Returns True if module executed without exceptions."""
        return self.exception is None

    def __repr__(self) -> str:
        return (f"ModuleResult(success={self.success}, "
                f"output_length={len(self.output)}, "
                f"errors_length={len(self.errors)})")


class ProgrammaticSession:
    """
    A programmatic interface to drozer for running modules and capturing output.

    This class wraps the interactive Session class to provide a clean API for
    running drozer modules from Python scripts.

    Example:
        ```python
        from drozer.api import ProgrammaticSession
        from drozer.connector import ServerConnector
        from pysolar.api.protobuf_pb2 import Message

        # Setup connection
        server = ServerConnector()
        server.connect(host="localhost", port=31415)

        # Start session
        response = server.startSession("device_id", password=None)
        session_id = response.system_response.session_id

        # Create programmatic session
        session = ProgrammaticSession(server, session_id)

        # Run module
        result = session.run_module("app.package.list", "-f browser")
        print(result.output)

        # Cleanup
        session.close()
        ```
    """

    def __init__(self, server, session_id, arguments=None):
        """
        Initialize a ProgrammaticSession.

        Args:
            server: Server connector instance
            session_id: Session ID from server.startSession()
            arguments: Optional arguments object (defaults to sensible settings)
        """
        # Create default arguments if not provided
        if arguments is None:
            arguments = self._create_default_arguments()

        # Create internal session
        self._session = Session(server, session_id, arguments)
        self._server = server
        self._session_id = session_id

    @staticmethod
    def _create_default_arguments():
        """Create default arguments for programmatic use."""
        class DefaultArguments:
            no_color = True  # Disable color codes in output
            onecmd = None    # Not running single command mode

        return DefaultArguments()

    def run_module(self, module_name: str,
                   args: Union[str, List[str]] = None) -> ModuleResult:
        """
        Run a drozer module and capture its output.

        Args:
            module_name: Full module name (e.g., "app.package.list")
            args: Module arguments, either as a string or list of strings
                  Examples:
                    - "-f browser"
                    - ["-f", "browser"]
                    - []

        Returns:
            ModuleResult: Object containing output, errors, return value, and success status

        Example:
            ```python
            # List packages containing "browser"
            result = session.run_module("app.package.list", ["-f", "browser"])

            # Get package info
            result = session.run_module("app.package.info",
                                       ["-a", "com.android.browser"])

            # Attack surface analysis
            result = session.run_module("app.package.attacksurface",
                                       "com.android.browser")
            ```
        """
        # Parse arguments if provided as string
        if args is None:
            args_list = []
        elif isinstance(args, str):
            args_list = shlex.split(args, comments=True)
        else:
            args_list = args

        # Capture stdout and stderr
        old_stdout = self._session.stdout
        old_stderr = self._session.stderr
        captured_stdout = StringIO()
        captured_stderr = StringIO()

        # Replace session streams
        self._session.stdout = captured_stdout
        self._session.stderr = captured_stderr

        return_value = None
        exception = None

        try:
            # Get the module
            module_class = self._session.modules.get(module_name)
            module_instance = module_class(self._session)

            # Run the module
            return_value = module_instance.run(args_list)

        except KeyError as e:
            # Module not found
            exception = e
            captured_stderr.write(f"Unknown module: {module_name}\n")

        except Exception as e:
            # Any other exception during execution
            exception = e
            captured_stderr.write(f"Exception in {module_name}: {e.__class__.__name__}: {str(e)}\n")
            captured_stderr.write(traceback.format_exc())

        finally:
            # Restore original streams
            self._session.stdout = old_stdout
            self._session.stderr = old_stderr

        # Get captured output
        output = captured_stdout.getvalue()
        errors = captured_stderr.getvalue()

        return ModuleResult(
            output=output,
            errors=errors,
            return_value=return_value,
            exception=exception
        )

    def list_modules(self, filter: Optional[str] = None) -> List[str]:
        """
        List available modules.

        Args:
            filter: Optional filter string to search for in module names

        Returns:
            List of module names

        Example:
            ```python
            # List all modules
            all_modules = session.list_modules()

            # List only package-related modules
            pkg_modules = session.list_modules("package")
            ```
        """
        if filter:
            return list(self._session.modules.all(contains=filter))
        else:
            return list(self._session.modules.all())

    def has_context(self) -> bool:
        """
        Check if the session has application context.

        Returns:
            bool: True if session has context, False otherwise
        """
        return self._session.has_context()

    def permissions(self) -> List[str]:
        """
        Get available permissions in this session.

        Returns:
            List of permission strings
        """
        return self._session.permissions()

    def close(self):
        """
        Close the session and cleanup resources.

        This should be called when you're done with the session.

        Example:
            ```python
            try:
                result = session.run_module("app.package.list")
                print(result.output)
            finally:
                session.close()
            ```
        """
        # Exit the session properly
        self._session.do_exit("")


# Export public API
__all__ = ['ProgrammaticSession', 'ModuleResult']
