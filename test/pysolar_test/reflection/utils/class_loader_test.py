import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../src'))

from pysolar.reflection.utils.class_loader import ClassLoader


class ClassLoaderTest(unittest.TestCase):
    """Test cases for ClassLoader error handling and messaging"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_construct = Mock()
        self.mock_system_class_loader = Mock()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_missing_apk_file_error_message(self):
        """Test that missing APK file produces helpful error message"""
        loader = ClassLoader(
            "nonexistent/test.apk",
            "/tmp/cache",
            self.mock_construct,
            self.mock_system_class_loader,
            relative_to=self.test_dir
        )

        # Set up mock paths
        loader.android_path = lambda: "/path/to/android.jar"
        loader.dx_path = lambda: "/path/to/d8"
        loader.javac_path = lambda: "/path/to/javac"

        with self.assertRaises(RuntimeError) as context:
            loader.getClassLoader()

        error_msg = str(context.exception)
        self.assertIn("drozer could not find or compile", error_msg)
        self.assertIn("Extension library:", error_msg)
        self.assertIn("File Resolution:", error_msg)
        self.assertIn("Possible Solutions:", error_msg)

    def test_error_message_includes_file_paths(self):
        """Test that error message includes diagnostic file path information"""
        loader = ClassLoader(
            "test/missing.apk",
            "/tmp/cache",
            self.mock_construct,
            self.mock_system_class_loader,
            relative_to=self.test_dir
        )

        loader.android_path = lambda: "/path/to/android.jar"
        loader.dx_path = lambda: "/path/to/d8"
        loader.javac_path = lambda: "/path/to/javac"

        with self.assertRaises(RuntimeError) as context:
            loader.getClassLoader()

        error_msg = str(context.exception)
        self.assertIn("Expected APK:", error_msg)
        self.assertIn("APK exists:", error_msg)
        self.assertIn("Java source:", error_msg)
        self.assertIn("Java exists:", error_msg)

    def test_error_message_includes_build_error(self):
        """Test that compilation errors are included in error message"""
        # Create a java file
        java_file = os.path.join(self.test_dir, "Test.java")
        with open(java_file, 'w') as f:
            f.write("public class Test {}")

        loader = ClassLoader(
            "Test.apk",
            "/tmp/cache",
            self.mock_construct,
            self.mock_system_class_loader,
            relative_to=self.test_dir
        )

        # Mock paths that will fail
        loader.android_path = lambda: None  # This will trigger an error
        loader.dx_path = lambda: "/path/to/d8"
        loader.javac_path = lambda: "/path/to/javac"

        with self.assertRaises(RuntimeError) as context:
            loader.getClassLoader()

        error_msg = str(context.exception)
        # Should include either the build error or the SDK error
        self.assertTrue(
            "Build Error:" in error_msg or "SDK is not defined" in error_msg
        )

    def test_successful_load_with_existing_apk(self):
        """Test that loading succeeds when APK exists"""
        # Create a dummy APK file
        apk_file = os.path.join(self.test_dir, "Test.apk")
        with open(apk_file, 'wb') as f:
            f.write(b"fake apk content")

        # Mock the construct method to return appropriate mocks
        mock_file = Mock()
        mock_file.exists.return_value = False  # Force re-upload

        mock_file_stream = Mock()

        def construct_side_effect(class_name, *args):
            if class_name == 'java.io.File':
                return mock_file
            elif class_name == 'java.io.FileOutputStream':
                return mock_file_stream
            elif class_name == 'dalvik.system.DexClassLoader':
                return Mock()  # Return a mock class loader
            return Mock()

        self.mock_construct.side_effect = construct_side_effect

        loader = ClassLoader(
            "Test.apk",
            "/tmp/cache",
            self.mock_construct,
            self.mock_system_class_loader,
            relative_to=self.test_dir
        )

        # Should not raise an exception
        try:
            result = loader.getClassLoader()
            self.assertIsNotNone(result)
        except RuntimeError as e:
            self.fail(f"Should not raise RuntimeError when APK exists: {e}")

    def test_debug_info_populated(self):
        """Test that debug info is populated during file resolution"""
        loader = ClassLoader(
            "test.apk",
            "/tmp/cache",
            self.mock_construct,
            self.mock_system_class_loader,
            relative_to=self.test_dir
        )

        loader.android_path = lambda: "/path/to/android.jar"
        loader.dx_path = lambda: "/path/to/d8"
        loader.javac_path = lambda: "/path/to/javac"

        try:
            loader.getClassLoader()
        except RuntimeError:
            pass  # Expected to fail

        # Check that debug info was populated
        self.assertIn('apk_path', loader._debug_info)
        self.assertIn('java_path', loader._debug_info)
        self.assertIn('apk_exists', loader._debug_info)
        self.assertIn('java_exists', loader._debug_info)

    def test_non_apk_source_passes_through(self):
        """Test that non-APK sources are passed through directly"""
        mock_file = Mock()
        mock_file.exists.return_value = False
        mock_file_stream = Mock()
        mock_class_loader = Mock()

        def construct_side_effect(class_name, *args):
            if class_name == 'java.io.File':
                return mock_file
            elif class_name == 'java.io.FileOutputStream':
                return mock_file_stream
            elif class_name == 'dalvik.system.DexClassLoader':
                return mock_class_loader
            return Mock()

        self.mock_construct.side_effect = construct_side_effect

        # Pass binary data directly (not an APK file)
        binary_source = b"direct binary data"

        loader = ClassLoader(
            binary_source,
            "/tmp/cache",
            self.mock_construct,
            self.mock_system_class_loader
        )

        # Should handle binary data without error
        result = loader.getClassLoader()
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
