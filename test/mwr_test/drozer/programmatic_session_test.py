import unittest
from io import StringIO
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from drozer.api import ProgrammaticSession, ModuleResult
from drozer.modules import Module


class ProgrammaticSessionTestCase(unittest.TestCase):
    """
    Test cases for ProgrammaticSession API for running modules programmatically.
    """

    def setUp(self):
        """Set up mock server and session for testing"""
        self.mock_server = Mock()
        self.session_id = "test_session_123"  # Should be string, not bytes
        self.mock_arguments = Mock()
        self.mock_arguments.no_color = True
        self.mock_arguments.onecmd = None

    def test_run_module_returns_module_result(self):
        """Test that run_module returns a ModuleResult object"""
        with patch('drozer.api.Session') as MockSession:
            # Create a mock session instance
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)

            # Mock the module
            mock_module_class = Mock()
            mock_module_instance = Mock(spec=Module)
            mock_module_instance.run.return_value = "test_return_value"
            mock_module_class.return_value = mock_module_instance
            mock_session_instance.modules.get.return_value = mock_module_class

            result = session.run_module("app.package.list", ["-f", "browser"])

            self.assertIsInstance(result, ModuleResult)

    def test_run_module_captures_stdout(self):
        """Test that run_module captures module output"""
        with patch('drozer.api.Session') as MockSession:
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)

            # Create a module that writes to stdout
            class TestModule(Module):
                name = "Test Module"
                def __init__(self, sess):
                    # Store references to the mocked streams
                    self.stdout = sess.stdout
                    self.stderr = sess.stderr

                def run(self, arguments):
                    self.stdout.write("Test output\n")
                    return "test_return"

            mock_session_instance.modules.get.return_value = TestModule

            result = session.run_module("test.module", [])

            self.assertIn("Test output", result.output)
            self.assertEqual(result.return_value, "test_return")

    def test_run_module_captures_stderr(self):
        """Test that run_module captures module errors"""
        with patch('drozer.api.Session') as MockSession:
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)

            # Create a module that writes to stderr
            class TestModule(Module):
                name = "Test Module"
                def __init__(self, sess):
                    self.stdout = sess.stdout
                    self.stderr = sess.stderr

                def run(self, arguments):
                    self.stderr.write("Error message\n")
                    return None

            mock_session_instance.modules.get.return_value = TestModule

            result = session.run_module("test.module", [])

            self.assertIn("Error message", result.errors)

    def test_run_module_handles_exceptions(self):
        """Test that run_module handles exceptions gracefully"""
        with patch('drozer.api.Session') as MockSession:
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)

            # Create a module that raises an exception
            class TestModule(Module):
                name = "Test Module"
                def __init__(self, sess):
                    self.stdout = sess.stdout
                    self.stderr = sess.stderr

                def run(self, arguments):
                    raise ValueError("Test exception")

            mock_session_instance.modules.get.return_value = TestModule

            result = session.run_module("test.module", [])

            self.assertFalse(result.success)
            self.assertIsNotNone(result.exception)
            self.assertIn("ValueError", result.errors)

    def test_run_module_with_string_arguments(self):
        """Test that run_module accepts arguments as string"""
        with patch('drozer.api.Session') as MockSession:
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)

            # Mock the module
            mock_module_class = Mock()
            mock_module_instance = Mock(spec=Module)
            mock_module_instance.run.return_value = None
            mock_module_class.return_value = mock_module_instance
            mock_session_instance.modules.get.return_value = mock_module_class

            # Should accept string arguments
            result = session.run_module("app.package.list", "-f browser")

            self.assertIsInstance(result, ModuleResult)
            # Verify module.run was called with parsed arguments
            mock_module_instance.run.assert_called_once()
            # Check that arguments were split correctly
            call_args = mock_module_instance.run.call_args[0][0]
            self.assertEqual(call_args, ["-f", "browser"])

    def test_module_result_success_property(self):
        """Test ModuleResult success property"""
        # Successful result
        result = ModuleResult(
            output="Success output",
            errors="",
            return_value="result",
            exception=None
        )
        self.assertTrue(result.success)

        # Failed result with exception
        result_failed = ModuleResult(
            output="",
            errors="Error occurred",
            return_value=None,
            exception=Exception("Test error")
        )
        self.assertFalse(result_failed.success)

    def test_run_module_unknown_module(self):
        """Test running a module that doesn't exist"""
        with patch('drozer.api.Session') as MockSession:
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)

            # Mock modules.get to raise KeyError for unknown module
            mock_session_instance.modules.get.side_effect = KeyError("unknown.module")

            result = session.run_module("unknown.module", [])

            self.assertFalse(result.success)
            self.assertIsNotNone(result.exception)
            self.assertIn("Unknown module", result.errors)

    def test_list_modules_no_filter(self):
        """Test listing all modules without filter"""
        with patch('drozer.api.Session') as MockSession:
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            mock_session_instance.modules.all.return_value = ['module1', 'module2', 'module3']
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)
            modules = session.list_modules()

            self.assertEqual(modules, ['module1', 'module2', 'module3'])
            mock_session_instance.modules.all.assert_called_once_with()

    def test_list_modules_with_filter(self):
        """Test listing modules with filter"""
        with patch('drozer.api.Session') as MockSession:
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            mock_session_instance.modules.all.return_value = ['app.package.list', 'app.package.info']
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)
            modules = session.list_modules("package")

            self.assertEqual(modules, ['app.package.list', 'app.package.info'])
            mock_session_instance.modules.all.assert_called_once_with(contains="package")

    def test_has_context(self):
        """Test has_context method"""
        with patch('drozer.api.Session') as MockSession:
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            mock_session_instance.has_context.return_value = True
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)
            result = session.has_context()

            self.assertTrue(result)
            mock_session_instance.has_context.assert_called_once()

    def test_permissions(self):
        """Test permissions method"""
        with patch('drozer.api.Session') as MockSession:
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            mock_session_instance.permissions.return_value = ['perm1', 'perm2']
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)
            perms = session.permissions()

            self.assertEqual(perms, ['perm1', 'perm2'])
            mock_session_instance.permissions.assert_called_once()

    def test_close(self):
        """Test close method"""
        with patch('drozer.api.Session') as MockSession:
            mock_session_instance = Mock()
            mock_session_instance.stdout = StringIO()
            mock_session_instance.stderr = StringIO()
            mock_session_instance.modules = Mock()
            mock_session_instance.do_exit = Mock()
            MockSession.return_value = mock_session_instance

            session = ProgrammaticSession(self.mock_server, self.session_id, self.mock_arguments)
            session.close()

            mock_session_instance.do_exit.assert_called_once_with("")


if __name__ == '__main__':
    unittest.main()
