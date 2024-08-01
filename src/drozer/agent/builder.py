import os
import platform

from WithSecure.common import command_wrapper

from drozer.configuration import Configuration


class Packager(command_wrapper.Wrapper):
    __apk_tool = Configuration.library("apktool.jar")
    __certificate = Configuration.library("certificate.pem")
    __key = Configuration.library("key.pk8")
    __java = Configuration.executable("java")
    __sign_apk = Configuration.library("apksigner.jar")

    __endpoint = "endpoint.txt"
    __manifest = "AndroidManifest.xml"
    __apktool_yml = "apktool.yml"

    def __init__(self):
        self.__wd = self._get_wd()

        match(platform.system()):
            case "Darwin":
                self.__aapt = Configuration.library("aapt-osx")

            case "Windows":
                self.__aapt = Configuration.library("aapt.exe")
                self.__zipalign = Configuration.library("zipalign.exe")
            case _:
                self.__aapt = Configuration.library("aapt")

    def apk_path(self, name):
        return os.path.join(self.__wd, name + ".apk")

    def endpoint_path(self):
        return os.path.join(self.__wd, "agent", "res", "raw", self.__endpoint)

    def manifest_path(self):
        return os.path.join(self.__wd, "agent", self.__manifest)

    def apktool_yml_path(self):
        return os.path.join(self.__wd, "agent", self.__apktool_yml)

    def package(self):
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

    def source_dir(self):
        return os.path.join(self.__wd, "agent")

    def unpack(self, name):
        apk_path = Configuration.library(name + ".apk")
        if apk_path is None:
            raise RuntimeError("could not locate " + name + ".apk")

        if self._execute([self.__java, "-jar", self.__apk_tool, "decode", apk_path,
                          "-o", self.source_dir()]) != 0:
            raise RuntimeError("could not unpack " + name)
