import os
import platform
import struct

from WithSecure.common import text


# Utility methods for calculating the size of a console.
#
# src: http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python

def format_dict(values, left_margin=0):
    width = {'gutter': 2, 'left_margin': left_margin, 'total': get_size()[0] - left_margin}
    width['key'] = min([max([len(k) for k in values.keys()] + [0]), width['total'] / 3])
    width['value'] = width['total'] - (width['gutter'] + width['key'])

    template_key_only = "%%%ds%%-%ds\n" % (width['left_margin'], width['key'])
    template = "%%%ds%%-%ds%%%ds%%-%ds\n" % (width['left_margin'], width['key'], width['gutter'], width['value'])

    keys = sorted(values.keys())

    formatted = ""

    for key in keys:
        value = text.wrap(values[key], width['value']).split("\n")

        if len(key) > width['key']:
            formatted += template_key_only % ("", key)
            formatted += template % ("", "", "", value.pop(0))
        else:
            formatted += template % ("", key, "", value.pop(0))

        for line in value:
            formatted += template % ("", "", "", line)

    return formatted


def get_size():
    """
    Attempt to discover the dimensions of a terminal window.
    """

    platf = platform.system()
    dimension = None

    if platf == 'Windows':
        dimension = _get_size_windows()

        if dimension is None:
            dimension = _get_size_tput()
    elif platf == 'Linux' or platf == 'Darwin' or platf.startswith('CYGWIN'):
        dimension = _get_size_linux()

    if dimension is None:
        dimension = (80, 25)

    return dimension


def _get_size_windows():
    """
    Attempt to discover the dimensions of a terminal window, on Windows.
    """

    res = None

    try:
        from ctypes import create_string_buffer, windll

        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    except:
        return None

    if res:
        # This appears to be some windows magic, fuck if I know
        data = struct.unpack("hhhhHhhhhhh", csbi.raw)

        cols = data[7] - data[5] + 1
        rows = data[8] - data[6] + 1

        return cols, rows
    else:
        return None


def _get_size_tput():
    """
    Attempt to discover the dimensions of a terminal window, through tput.
    """

    try:
        import subprocess

        proc = subprocess.Popen(["tput", "cols"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        output = proc.communicate(input=None)
        cols = int(output[0])
        proc = subprocess.Popen(["tput", "lines"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        output = proc.communicate(input=None)
        rows = int(output[0])

        return cols, rows
    except:
        return None


def _get_size_linux():
    """
    Attempt to discover the dimensions of a terminal window, on Linux.
    """

    def ioctl_GWINSZ(fd):
        """
        Attempt to discover the dimensions of a terminal window, using IOCTL.
        """

        try:
            import fcntl, termios

            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return None

        return cr

    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)

    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            env = os.environ
            cr = (env['LINES'], env['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])
