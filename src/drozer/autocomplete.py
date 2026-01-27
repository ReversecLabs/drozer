#!/usr/bin/env python

import sys
import os
import distro

if distro.id() in ["Fedora", "CentOS Linux"]:
    os.putenv("TERM", "vt100")

from reversec.common import argparse_completer

from drozer.console import Console
from drozer.exploit.manager import ExploitManager
from drozer.payload.manager import PayloadManager
from drozer.server import Server
from drozer.ssl import SSLManager
from drozer.repoman import ModuleManager


class ArgumentSuggestor(object):

    def get_completion_suggestions(self, action, text, **kwargs):
        return []


def main():
    words = sys.argv[1:-1]
    offset = int(sys.argv[-1])

    if offset == len(words):
        words.append("")

    word = words[offset]

    begidx = len(" ".join(words))
    endidx = begidx + len(word)

    providers = {"console": Console, "exploit": ExploitManager, "module": ModuleManager, "payload": PayloadManager,
                 "server": Server, "ssl": SSLManager}

    if offset == 1:
        # we are selecting the drozer sub-program
        print("agent console exploit module payload server ssl")
    elif offset == 2:
        # we are selecting the command
        print(" ".join(map(lambda c: c.replace("do_", ""), providers[words[1]]()._Base__commands())))
    else:
        # we are typing arguments to a command
        provider = providers[words[1]]()
        provider._parser.error = lambda x: None
        provider.prepare_argument_parser(words[2:])

        print(" ".join(argparse_completer \
                       .ArgumentParserCompleter(provider._parser, provider) \
                       .get_suggestions(word, " ".join(words), begidx, endidx, offs=2)))
