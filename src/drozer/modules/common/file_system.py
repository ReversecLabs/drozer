import binascii
import os
import base64

from WithSecure.common.list import chunk

class FileSystem(object):
    """
    Utility methods for interacting with the Agent's file system.
    """

    def cacheDir(self):
        """
        Get the full path to the Agent's cache directory.
        """

        return str(self.getContext().getCacheDir().toString())

    def deleteFile(self, source):
        """
        Delete a file from the Agent's file system.
        """

        file_io = self.new("java.io.File", source)

        if (file_io.exists() == True):
            return file_io.delete()
        else:
            return None

    def downloadFile(self, source, destination, block_size=65536):
        """
        Copy a file from the Agent's file system to the local one.
        """

        data = self.readFile(source, block_size=block_size)

        if data:
            if (os.path.isdir(destination) == True):
                destination = os.path.sep.join([destination, source.split("/")[-1]])
                
            output = open(destination, 'wb')
            output.write(data)
            output.close()

            return len(data)
        else:
            return None
        
    def ensureDirectory(self, target):
        """
        Tests whether a directory exists, on the Agent's file system, and creates
        it if it does not.
        """

        if (self.isFile(target) == True):
            return False
        elif (self.isDirectory(target) == False):
            return self.new("java.io.File", target).mkdirs()
        else:
            return True

    def exists(self, target):
        """
        Test whether or not a file exists on the Agent's file system.
        """

        file_io = self.new("java.io.File", target)

        return file_io.exists()
    
    def isCommandInstalled(self, command):
        """
        Test whether a specified command binary is installed on the Agent.
        """

        return (self.exists("/system/bin/{}".format(command)) or self.exists("/system/xbin/{}".format(command))) == True

    def fileSize(self, source):
        """
        Get the size of a file on the Agent's file system.
        """

        file_io = self.new("java.io.File", source)

        if (file_io.exists() == True):
            return file_io.length()
        else:
            return None
    
    def format_file_size(self, size):
        """
        Return the size of a file in human-readable form (i.e., x KiB).
        """
        
        for x in ['bytes', 'KiB', 'MiB', 'GiB']:
            if (size < 1024.0 and size > -1024.0):
                if (x != "bytes"):
                    return "%.1f %s" % (size, x)
                else:
                    return "%d %s" % (size, x)
            
            size /= 1024.0
            
        return "%3.1f%s" % (size, 'TiB')

    def isDirectory(self, target):
        """
        Test whether a target exists, and is a directory.
        """
        
        file_io = self.new("java.io.File", target)
        
        return file_io.exists() and file_io.isDirectory()

    def isFile(self, target):
        """
        Test whether a target exists, and is a normal file.
        """
        
        file_io = self.new("java.io.File", target)
        
        return file_io.exists() and file_io.isFile()
        
    def listFiles(self, target):
        """
        Gets a list of all files in the folder target.
        """
        #TODO does not work past the first folder
        file_io = self.new("java.io.File", target)
        
        return ["%s%s" %(s, '/') if (file_io.isDirectory() == True) else s for s in file_io.list()]
        
    def md5sum(self, source):
        """
        Calculate the MD5 checksum of a file on the Agent's file system.
        """

        FileUtil = self.loadClass("common/FileUtil.apk", "FileUtil")

        file_io = self.new("java.io.File", source)

        if (file_io.exists() == True):
            return FileUtil.md5sum(file_io)
        else:
            return None

    def readFile(self, source, block_size=65536):
        """
        Read a file from the Agent's file system, and return the data.
        """

        ByteStreamReader = self.loadClass("common/ByteStreamReader.apk", "ByteStreamReader")

        file_io = self.new("java.io.File", source)

        if (file_io.exists() == True):
            file_stream = self.new("java.io.FileInputStream", file_io)

            data = b""
            
            while True:
                block = ByteStreamReader.read(file_stream, 0, block_size).base64_encode()
                
                if (len(block) > 0):
                    data += base64.b64decode(block)
                else:
                    return data
        else:
            return None

    def uploadFile(self, source, destination, block_size=65536):
        """
        Copy a file from the local file system to the Agent's.
        """
        
        if (self.isDirectory(destination) == True):
            destination = "/".join([destination, source.split(os.path.sep)[-1]])

        return self.writeFile(destination, open(source, 'rb').read(), block_size=block_size)
    
    def workingDir(self):
        """
        Get the full path to the Agent's working directory.
        """

        return self.variables['WD']

    def writeFile(self, destination, data, block_size=65536):
        """
        Write data into a file on the Agent's file system.
        """

        ByteStreamWriter = self.loadClass("common/ByteStreamWriter.apk", "ByteStreamWriter")

        file_io = self.new("java.io.File", destination)

        if (file_io.exists() != True):
            file_stream = self.new("java.io.FileOutputStream", destination)

            for c in chunk(data, block_size):
                ByteStreamWriter.writeHexStream(file_stream, binascii.hexlify(c).decode())

            file_stream.close()
            
            return len(data)
        else:
            return None
            
