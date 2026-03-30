#!/usr/bin/env python

import logging
import sys

from reversec.common import logger

from drozer.agent.manager import AgentManager

logger.setLevel(logging.DEBUG)
logger.addStreamHandler()

AgentManager().run(sys.argv[2::])
