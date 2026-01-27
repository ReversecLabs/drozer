#!/usr/bin/env python

import logging
import sys

from reversec.common import logger

from drozer.ssl import SSLManager

logger.setLevel(logging.DEBUG)
logger.addStreamHandler()

SSLManager().run(sys.argv[2::])
    
