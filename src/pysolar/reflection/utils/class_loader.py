import binascii
import hashlib
import os
import sys

from pysolar.reflection.exceptions import ReflectionException
from pysolar.reflection.types.reflected_primitive import ReflectedPrimitive
from pysolar.reflection.utils import ClassBuilder
from WithSecure.common import fs

import codecs

class ClassLoader(object):
    """
    Provides utility methods for loading Java source code from the local
    system into the running Dalvik VM, using the reflection API.
    """

    def __init__(self, source_or_relative_path, cache_path, construct, system_class_loader, relative_to=None):
        self.source_or_relative_path = source_or_relative_path

        self.android_path = None
        self.cache_path = cache_path
        self.construct = construct
        self.dx_path = None
        self.javac_path = None
        self.relative_to=relative_to
        self.system_class_loader = system_class_loader
        self._debug_info = {}  # Store debug information for error messages

    def loadClass(self, klass):
        return self.getClassLoader().loadClass(klass);

    def getClassLoader(self):
        """
        Gets a DexClassLoader on the agent, given compiled source or an apk
        file from the local system.
        """

        self.source = self.__get_source(self.source_or_relative_path, relative_to=self.relative_to)

        if self.source != None:
            file_path = "/".join([self.cache_path, self.__get_cached_apk_name()])

            file_io = self.construct('java.io.File', file_path)

            if not self.__verify_file(file_io, self.source):
                # yaynoteyay
                # the old code used `ord()` to convert characters to their unicode counterpart, but i guess in python3 `i` is already a unicode character?
                # so removed `ord()` functions
                source_data = [ReflectedPrimitive("byte", (i if i < 128 else i - 0x100), reflector=None) for i in self.source]
                file_stream = self.construct("java.io.FileOutputStream", file_path)
                file_stream.write(source_data, 0, len(source_data))
                file_stream.close()
            return self.construct('dalvik.system.DexClassLoader', file_path, self.cache_path, None, self.system_class_loader)
        else:
            # Provide detailed error message with diagnostic information
            error_msg = self.__build_error_message()
            raise RuntimeError(error_msg)

    def __build_error_message(self):
        """
        Build a detailed error message with diagnostic information to help users
        troubleshoot extension library loading issues.
        """
        msg_parts = [
            "\n" + "="*80,
            "ERROR: drozer could not find or compile a required extension library",
            "="*80,
            "",
            "Extension library: {}".format(self.source_or_relative_path),
        ]

        # Add file path diagnostics
        if 'apk_path' in self._debug_info:
            msg_parts.extend([
                "",
                "File Resolution:",
                "  Expected APK: {}".format(self._debug_info['apk_path']),
                "  APK exists: {}".format(self._debug_info.get('apk_exists', 'Unknown')),
                "  Java source: {}".format(self._debug_info['java_path']),
                "  Java exists: {}".format(self._debug_info.get('java_exists', 'Unknown')),
            ])

        # Add build error if compilation was attempted
        if 'build_error' in self._debug_info:
            msg_parts.extend([
                "",
                "Build Error:",
                "  {}".format(self._debug_info['build_error']),
            ])

        # Add possible solutions
        msg_parts.extend([
            "",
            "Possible Solutions:",
            "  1. Ensure drozer was installed correctly:",
            "     pip install --force-reinstall drozer",
            "",
            "  2. If installing from source, ensure build dependencies are available:",
            "     - Java Development Kit (JDK) 11 or greater",
            "     - javac must be on your PATH",
            "     - d8 tool must be available",
            "     - ANDROID_SDK environment variable set (or android.jar in drozer/lib)",
            "",
            "  3. Run setup manually to build APKs:",
            "     cd drozer-source-directory",
            "     python setup.py build",
            "",
            "  4. Check that extension APK files exist in:",
            "     drozer/modules/common/*.apk",
            "",
            "="*80,
        ])

        return "\n".join(msg_parts)

    def __get_cached_apk_name(self):
        """
        Calculate a unique name for the cached APK file, based on the content
        of the library file.
        """

        # yaynoteyay
        # md5().digest() returns bytes instead of hex
        # aded decode() function to make it return a string and concat with ".apk"
        return binascii.hexlify(hashlib.md5(self.source).digest()).decode() + ".apk"

    def __get_source(self, source_or_relative_path, relative_to=None):
        """
        Get source, either from an apk file or passed directly.
        """

        source = None

        if isinstance(source_or_relative_path, (str, bytes)) and (source_or_relative_path.endswith(b".apk") if isinstance(source_or_relative_path, bytes) else source_or_relative_path.endswith(".apk")):
            if relative_to == None:
                relative_to = os.path.join(os.path.dirname(__file__), "..")
            elif relative_to.find(".py") >= 0 or relative_to.find(".pyc") >= 0:
                relative_to = os.path.dirname(relative_to)

            apk_path = os.path.join(relative_to, *source_or_relative_path.split("/"))
            java_path = apk_path.replace(".apk", ".java")

            # Store diagnostic information
            self._debug_info['apk_path'] = apk_path
            self._debug_info['java_path'] = java_path
            self._debug_info['apk_exists'] = os.path.exists(apk_path)
            self._debug_info['java_exists'] = os.path.exists(java_path)

            if os.path.exists(apk_path):
                source = fs.read(apk_path)
            elif os.path.exists(java_path):
                try:
                    source = ClassBuilder(java_path, self.dx_path(), self.javac_path(), self.android_path()).build()
                except Exception as e:
                    self._debug_info['build_error'] = str(e)
                    # Re-raise the exception to be caught by getClassLoader
                    raise
        else:
            source = source_or_relative_path

        return source

    def __verify_file(self, remote, local_data):
        """
        checks the hash value of the requested apk to the one already present on the agent
        """

        # yaynoteyay
        # changed `not remote.exists()` to `remote.exists() == False`
        if (remote == None) or (remote.exists() == False) or (local_data == None):
            """
            no file present on the agent
            """
            return False

        remote_hash = ""
        try:
            remote_verify = self.construct("com.WithSecure.dz.util.Verify")
            remote_hash = remote_verify.md5sum(remote)
        except ReflectionException:
            return True

        local_hash = hashlib.md5(local_data).hexdigest()

        return remote_hash == local_hash
