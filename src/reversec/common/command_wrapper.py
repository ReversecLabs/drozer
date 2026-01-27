import os
import platform
import tempfile


class Wrapper(object):

    def _execute(self, argv):
        if platform.system() != "Windows":
            return os.spawnve(os.P_WAIT, argv[0], argv, os.environ)
        else:
            return os.spawnve(os.P_WAIT, argv[0], [os.path.basename(argv[0])] + argv[1:], os.environ)

    def _get_wd(self):
        return tempfile.mkdtemp()
