"""
A library of fileystem functions.
"""

import hashlib

# yay note yay
# most of the time, we should be reading bytes
# but lets give an option to read `str`
def read(path, type='rb'):
    """
    Utility method to read a file from the filesystem into a string.
    """

    try:
        # yaynoteyay
        # for some reason, this thing isn't loading .apk files
        '''
        f = open(path, 'rb')
        line = data = f.read()

        while line != "":
            line = f.read()

            data += line

        f.close()

        return data
        '''

        with open(path, type) as file:
            binary_data = file.read()
        file.close()
        return binary_data
    except IOError:
        return None


def touch(path):
    """
    Utility method to touch a file on the filesystem.
    """

    open(path, 'w').close()


def write(path, data):
    """
    Utility method to write a string into a filesystem file.
    """

    try:
        f = open(path, 'wb')
        f.write(data)
        f.close()

        return len(data)
    except IOError:
        return None


def md5sum(path):
    """
    Utility method to get the md5sum of a file on the filesystem
    """

    try:
        f = open(path, 'rb')
        line = data = f.read()

        while line != "":
            line = f.read()

            data += line

        f.close()
        return hashlib.md5(data).hexdigest()
    except IOError:
        return None


def sha1sum(path):
    """
    Utility method to get the md5sum of a file on the filesystem
    """

    try:
        f = open(path, 'rb')
        line = data = f.read()

        while line != "":
            line = f.read()

            data += line

        f.close()
        return hashlib.sha1(data).hexdigest()
    except IOError:
        return None

