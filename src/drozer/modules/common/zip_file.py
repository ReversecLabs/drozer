from drozer.modules.common import loader

class ZipFile(loader.ClassLoader):
    """
    Utility methods for interacting with zipped archive files.
    """

    def extractFromZip(self, target, source, destination):
        """
        Extract a file (target) from a zipped archive (source) and save it to
        the file system (destination).
        """
        try:
            ZipUtil = self.loadClass("common/ZipUtil.apk", "ZipUtil")
        except Exception as e:
            print("\n\n--ERROR--  zip_file.py error: %s\n\n" % e)


        return ZipUtil.unzip(target, source, destination)
