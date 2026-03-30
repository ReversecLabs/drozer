"""
Provides a handlful of utility methods to simplify setting up a logger.
"""

import logging
import sys

logger = logging.getLogger('drozer')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def addFileHandler(path):
    """
    Add a file handler to the default logger.
    """

    addHandler(logging.FileHandler(path))


def addHandler(handler):
    """
    Add a handler to the default logger, and set the format.
    """

    handler.setFormatter(formatter)
    logger.addHandler(handler)


def addStreamHandler():
    """
    Add a stream handler to the default logger.
    """

    addHandler(logging.StreamHandler(stream=sys.stdout))


def setLevel(level):
    """
    Change the logging level of the default logger.
    """

    logger.setLevel(level)
