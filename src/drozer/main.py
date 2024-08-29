#!/usr/bin/env python
import importlib
import sys
import os
import distro

if distro.id() in ["fedora", "centos"]:
    os.putenv("TERM", "vt100")

Commands = {'agent': 'create custom drozer Agents',
            'console': 'start the drozer Console',
            'exploit': 'generate an exploit to deploy drozer',
            'module': 'manage drozer modules',
            'payload': 'generate payloads to deploy drozer',
            'server': 'start a drozer Server',
            'ssl': 'manage drozer SSL key material'}

USAGE = """
usage: drozer [COMMAND]

Run `drozer [COMMAND] --help` for more usage information.

Commands:
"""

def print_usage():
    print(USAGE)
    for command in Commands:
        print("  %15s  %s" % (command, Commands[command]))
    print("")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in Commands:
            __import__("drozer.cli.%s" % (sys.argv[1]))
        else:
            print("unknown command:", sys.argv[1])
            print_usage()
    else:
        print_usage()
