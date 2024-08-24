import os
from pathlib import Path
import platform
import yaml
import shutil
import tempfile

from WithSecure.common import command_wrapper
from drozer.configuration import Configuration
from drozer.agent import manifest


class Packager(command_wrapper.Wrapper):
    __apk_tool = Configuration.library("apktool.jar")
    __certificate = Configuration.library("certificate.pem")
    __key = Configuration.library("key.pk8")
    __java = Configuration.executable("java")
    __sign_apk = Configuration.library("apksigner.jar")

    __endpoint = "config.txt"
    __manifest = "AndroidManifest.xml"
    __apktool_yml = "apktool.yml"
    __aapt = Configuration.library("aapt")
    __zipalign = Configuration.library("zipalign")

    def __init__(self):
        self.__wd = tempfile.TemporaryDirectory()

        self.__manifest_file = None
        self.__config_file = None
        self.__apktool_file = None

    @classmethod
    def init_from_folder(cls, folder_path):
        p = Packager()
        print("copying files to working directory, this may take some time...")
        shutil.copytree(folder_path, p.source_dir())
        p._init_components()
        return p
        
    @classmethod
    def init_from_apk(cls, apk_path):
        p = Packager()
        cls.unpack_apk(apk_path, p.source_dir())
        p._init_components()
        return p

    def __enter__(self):
        return self
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.__wd.cleanup()

    def _init_components(self):
        self.__manifest_file = manifest.Manifest(self.manifest_path())
        self.__config_file = manifest.Endpoint(self.endpoint_path())
        with open(self.apktool_yml_path(), 'r') as file:
            self.__apktool_file = yaml.safe_load(file)

    def close(self):
        self.__wd.cleanup()

    def _working_dir(self):
        return Path(self.__wd.name)

    def source_dir(self):
        return os.path.join(self._working_dir(), "agent")
    
    def apk_path(self, name):
        return os.path.join(self._working_dir(), name + ".apk")

    def endpoint_path(self):
        return os.path.join(self.source_dir(), "res", "raw", self.__endpoint)

    def manifest_path(self):
        return os.path.join(self.source_dir(), self.__manifest)

    def apktool_yml_path(self):
        return os.path.join(self.source_dir(), self.__apktool_yml)

    def get_config_file(self):
        return self.__config_file

    def get_manifest_file(self):
        return self.__manifest_file

    def get_apktool_file(self):
        return self.__apktool_file

    def rename_package(self, name):
        app_name = "com.withsecure." + name

        self.__apktool_file["packageInfo"]["renameManifestPackage"] = app_name
        self.__manifest_file.set_name(name)

    def package(self):
        with open(self.apktool_yml_path(), 'w') as file:
            yaml.dump(self.__apktool_file, file)
        self.__manifest_file.write()
        self.__config_file.write()

        if self._execute([self.__java, "-jar", self.__apk_tool, "build",
                          self.source_dir(), "-o", self.apk_path("agent-unsigned")]) != 0:
            raise RuntimeError("could not repack the agent sources")

        if self._execute([self.__zipalign, "4", self.apk_path("agent-unsigned"),
                          self.apk_path("agent-unsigned-aligned")]) != 0:
            raise RuntimeError("Could not align apk")

        if self._execute([self.__java, "-jar", self.__sign_apk, "sign", "-key", self.__key, "-cert", self.__certificate,
                          "--in", self.apk_path("agent-unsigned-aligned"), "--out", self.apk_path("agent")]) != 0:
            raise RuntimeError("could not sign the agent package")

        return self.apk_path("agent")

    """
    Depreciated
    use init_from_apk() instead to ensure Packager object is always in a valid state
    """
    def unpack(self, name):
        apk_path = Configuration.library(name + ".apk")
        if apk_path is None:
            raise RuntimeError("could not locate " + name + ".apk in library")
        
        self.unpack_apk(apk_path, self.source_dir())
        self._init_components()

    @classmethod
    def unpack_apk(cls, in_path, out_path):
        if cls._execute([cls.__java, "-jar", cls.__apk_tool, "decode", in_path,
                         "-o", out_path]) != 0:
            raise RuntimeError("could not unpack " + in_path)
