#!/usr/bin/env python

import logging
import sys

from reversec.common import logger

from drozer.payload.manager import PayloadManager

logger.setLevel(logging.DEBUG)
logger.addStreamHandler()

PayloadManager().run(sys.argv[2::])
