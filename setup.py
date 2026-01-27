import sys
from fnmatch import fnmatch
import os
from shutil import which
import setuptools
from subprocess import run


def clear_apks():
    pwd = os.path.join('src', 'drozer', 'modules')

    for root, dirnames, filenames in os.walk(pwd):
        for filename in filenames:
            if fnmatch(filename, "*.class") or \
                    fnmatch(filename, "*.apk") or \
                    fnmatch(filename, "*.zip"):
                os.remove(os.path.join(root, filename))


def make_apks():
    pwd = os.path.join('src', 'drozer', 'modules')

    if 'ANDROID_SDK' not in os.environ:
        # raise Exception("ANDROID_SDK environment variable not set")
        sdk = os.path.join('src', 'drozer', 'lib', 'android.jar')
        sdk = os.path.abspath(sdk)
    else:
        sdk = os.environ['ANDROID_SDK']

    if 'D8' not in os.environ:
        # raise Exception("D8 environment variable not set")
        d8 = os.path.join('src', 'drozer', 'lib', 'd8')
        d8 += '.bat' if sys.platform == 'win32' else ''
        d8 = os.path.abspath(d8)
    else:
        d8 = os.environ['D8']

    if which('javac') is None:
        raise Exception("javac not installed, unable to compile APKs")

    # If apks exist, delete them and generate new ones
    clear_apks()

    # Generate apks
    for root, _, filenames in os.walk(pwd):
        for filename in filenames:
            if fnmatch(filename, "*.java"):
                # Compile java
                javac_cmd = ['javac', '-cp', sdk, filename]

                # Build apk
                basename, _ = filename.split('.')
                d8_cmd = [d8, '--output', basename + '.zip', basename + '*.class', '--lib', sdk]

                run(' '.join(javac_cmd), shell=True, cwd=root)
                run(' '.join(d8_cmd), shell=True, cwd=root)

                os.rename(os.path.join(root, basename + '.zip'), os.path.join(root, basename + '.apk'))


def get_package_data():
    data = {"": []}
    pwd = os.path.join('src', 'drozer')

    # Make sure we build apks before generating a package
    make_apks()

    for root, _, filenames in os.walk(pwd):
        for filename in filenames:
            if not fnmatch(filename, "*.class") or fnmatch(filename, "*.pyc"):
                data[""].append(os.path.join(root, filename)[11:])
    return data


setuptools.setup(package_data=get_package_data())
