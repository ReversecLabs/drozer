import binascii
import glob
import hashlib
import os
import subprocess

from sys import platform
from reversec.common import fs, system

class ClassBuilder(object):
    """
    ClassBuilder provides a wrapper around the process to build a Java source
    file for the Android platform.
    """
    
    def __init__(self, path, d8_path, javac_path, sdk_path):
        self.path = path
        
        self.d8 = d8_path
        self.javac = javac_path
        self.sdk_path = sdk_path
        
        self.__check_build_path_ready()
    
    def build(self):
        """
        Builds an APK file, from the specified path.
        """
        
        apk_path = self.__get_generated_apk_name()
        
        # if the apk file we are about to generate already exists, then we do
        # not need to compile it again
        if not os.path.exists(apk_path):
            # switch our working directory to the source directory
            os.chdir(os.path.dirname(self.path))
            # compile the java sources (%.java => %.class)
            if self.__execute(self.javac , "-cp", self.sdk_path, os.path.basename(self.path)):
                raise RuntimeError("Error whilst compiling the Java sources.")
            
            # collect any sub-classes that we generated
            sources = map(lambda p: os.path.basename(p), glob.glob(self.path.replace(".java", "$*.class")))
            # package the compiled bytecode into an apk file (%.class => %.apk)
            if self.__execute(self.d8, "--output", os.path.basename(apk_path), *([os.path.basename(self.path).replace(".java", ".class")] + sources)):
                raise RuntimeError("Error whilst building APK bundle.")
        
        # read the generated source file
        return fs.read(apk_path)
    
    def __check_build_path_ready(self):
        """
        Test if all elements of the build path have been properly initialised.
        """
        
        if self.sdk_path == None:
            raise RuntimeError("SDK is not defined. Please set SDK to the path to android.jar within the SDK.")
        if self.javac == None:
            raise RuntimeError("Could not find javac on your PATH.")
        if self.d8 == None:
            raise RuntimeError("Could not find d8 on your PATH.")
        
    def __execute(self, *argv):
        """
        Spawn a shell command
        """
        
        print(" ".join(argv))

        if platform == 'win32':
            subprocess.call(argv,shell=True,cwd=os.getcwd())
        else:
            subprocess.call(' '.join(argv),shell=True, cwd=os.getcwd())

    def __get_generated_apk_name(self):
        """
        Calculate a unique name for the generated APK file, based on the content
        of the source file.
        """
        
        return os.path.join(os.path.dirname(self.path), binascii.hexlify(hashlib.md5(self.__get_source()).digest()) + ".apk")
        
    def __get_source(self):
        """
        Retrieve the source code from the source file.
        """

        return fs.read(self.path)
        