import platform
import re


class StreamWrapper(object):
    """
    StreamWrapper provides a generalised wrapper around an output stream.
    """

    def __init__(self, stream):
        self.stream = stream

    def close(self):
        """
        Wraps stream#close().
        """

        self.stream.close()

    def flush(self):
        """
        Wraps stream#flush().
        """

        self.stream.flush()

    def write(self, text):
        """
        Wraps stream#write().
        """

        self.stream.write(text)


class ColouredStream(StreamWrapper):
    """
    ColouredStream is a wrapper around a stream, that processes colour meta-
    data tags (like [color green]green[/color]) and inserts appropriate control
    sequences to colour the output.
    """

    def __init__(self, stream):
        StreamWrapper.__init__(self, stream)

        self.os = platform.system()

    def write(self, text):
        """
        Wraps stream#write().

        Before passing the given text to the stream#write() command, it is
        processed to replace the colour tags with appropriate control
        codes.
        """

        if self.os == 'Linux' or self.os == 'Darwin' or self.os.startswith('CYGWIN'):
            self.stream.write(format_colors(text))
        else:
            self.stream.write(remove_colors(text))


class DecolouredStream(StreamWrapper):
    """
    DecolouredStream is a wrapper around a stream, that processes colour meta-
    data tags (like [color green]green[/color]) and removes them.

    This provides a handy solution to avoid writing colour codes into files.
    """

    def __init__(self, stream):
        StreamWrapper.__init__(self, stream)

    def write(self, text):
        """
        Wraps stream#write().

        Before passing the given text to the stream#write() command, it is
        processed to remove the colour tags.
        """

        self.stream.write(remove_colors(text))


Colors = {"blue": "\033[94m",
          "end": "\033[0m",
          "green": "\033[92m",
          "purple": "\033[95m",
          "red": "\033[91m",
          "yellow": "\033[93m"}


def format_colors(text):
    """
    Inserts *nix colour sequences into a string.

    Parses a string, and replaces colour tags ([color xxx]xxx[/color]) with
    the appropriate control sequence.
    """

    def replace_color(m):
        """
        Callback function, to replace a colour tag with its content and a
        suitable escape sequence to change colour.
        """

        return "%s%s%s" % (Colors[m.group(1)], m.group(2), Colors['end'])

    text = re.sub("\[color\s*([a-z]+)\](.*?)\[\/color\]", replace_color, text)

    return text


def remove_colors(text):
    """
    Removes colour tags ([color xxx]xxx[/color]) from a string.
    """

    def remove_color(m):
        """
        Callback function, to replace a colour tag with its content.
        """

        return "%s" % (m.group(2))

    text = re.sub("\[color\s*([a-z]+)\](.*?)\[\/color\]", remove_color, text)

    return text
