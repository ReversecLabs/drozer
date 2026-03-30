"""
A library of text handling functions.
"""
from functools import reduce


def indent(text, prefix):
    """
    Add prefix to the beginning of all lines in text.
    """

    return "\n".join(map(lambda l: "%s%s" % (prefix, l), text.split("\n")))


def wrap(text, width=80):
    """
    A word-wrap function that preserves existing line breaks and most spaces in
    the text.

    Expects that existing line breaks are posix newlines (\n).
    
    Author: Mike Brown
    Source: http://code.activestate.com/recipes/148061-one-liner-word-wrap-function/
    """

    return reduce(lambda line, word: '%s%s%s' % (line, ' \n'[(len(line) - line.rfind('\n') - 1 + len(word.split('\n', 1)[0]) >= width)], word), text.split(' '))
