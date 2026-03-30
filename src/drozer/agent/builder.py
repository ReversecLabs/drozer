import os
import platform

from reversec.common import command_wrapper

from drozer.configuration import Configuration


class Packager(command_wrapper.Wrapper):
    __aapt = Configuration.library("aapt")
    __aapt_osx = Configuration.library("aapt-osx")
    __aapt_exe = Configuration.library("aapt.exe")
    __apk_tool = Configuration.library("apktool.jar")
    __certificate = Configuration.library("certificate.pem")
    __key = Configuration.library("key.pk8")
    __java = Configuration.executable("java")
    __sign_apk = Configuration.library("signapk.jar")

    __endpoint = "endpoint.txt"
    __manifest = "AndroidManifest.xml"
    __apktool_yml = "apktool.yml"

    def __init__(self):
        self.__wd = self._get_wd()

    def apk_path(self, signed=True):
        if signed:
            return os.path.join(self.__wd, "agent.apk")
        else:
            return os.path.join(self.__wd, "agent-unsigned.apk")

    def endpoint_path(self):
        return os.path.join(self.__wd, "agent", "res", "raw", self.__endpoint)

    def manifest_path(self):
        return os.path.join(self.__wd, "agent", self.__manifest)

    def apktool_yml_path(self):
        return os.path.join(self.__wd, "agent", self.__apktool_yml)

    def package(self):
        platform_name = platform.system()

        if platform_name == "Darwin":
            aapt = self.__aapt_osx
        elif platform_name == "Windows":
            aapt = self.__aapt_exe
        else:
            aapt = self.__aapt

        if self._execute(
                [self.__java, "-jar", self.__apk_tool, "build", self.source_dir(), "-o", self.apk_path(False)]) != 0:
            raise RuntimeError("could not repack the agent sources")
        if self._execute([self.__java, "-jar", self.__sign_apk, self.__certificate, self.__key, self.apk_path(False),
                          self.apk_path(True)]) != 0:
            raise RuntimeError("could not sign the agent package")

        return os.path.join(self.__wd, "agent.apk")

    def source_dir(self):
        return os.path.join(self.__wd, "agent")

    def unpack(self, name):
        if self._execute([self.__java, "-jar", self.__apk_tool, "decode", Configuration.library(name + ".apk"), 
                          "-o", self.source_dir()]) != 0:
            raise RuntimeError("could not unpack " + name)
