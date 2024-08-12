import os
from WithSecure.common import cli
import readchar
from ansi import *


class OT:
    def __init__(self, string, children=None):
        if children is None:
            children = []
        self.string = string
        self.children = children


class FancyBase(cli.Base):
    def __init__(self, add_help=True):
        cli.Base.__init__(self, add_help=add_help)

    @staticmethod
    def __ansi_print(*args, end=''):
        print(*args, sep='', end=end)

    @staticmethod
    def __print_init(prompt, max_options):
        print('\n' * max_options, end='')
        FancyBase.__ansi_print(cursor.prev_line(max_options), prompt)

    @staticmethod
    def __print(input_str, options, max_options, selected_line, offset_x):
        for i in range(max_options):
            FancyBase.__ansi_print(cursor.next_line(1), cursor.erase_line(0))
            if i < len(options):
                if i + 1 == selected_line:
                    FancyBase.__ansi_print(color.fg.blue, '-', cursor.goto_x(offset_x + 1), options[i],
                                           color.fx.reset)
                else:
                    FancyBase.__ansi_print(cursor.goto_x(offset_x + 1), options[i])

        FancyBase.__ansi_print(cursor.prev_line(max_options), cursor.goto_x(offset_x + 1), cursor.erase_line(0),
                               input_str)
        # printing built string last ensures that cursor is left at correct pos

    @staticmethod
    def __print__cleanup(input_str, max_options, offset_x):
        for i in range(max_options):
            FancyBase.__ansi_print(cursor.next_line(1), cursor.erase_line(2))

        FancyBase.__ansi_print(cursor.prev_line(max_options), cursor.goto_x(offset_x + 1), cursor.erase_line(0),
                               input_str, end='\n')

    """
    finds all options in the options tree that begins with the given string
    """
    @staticmethod
    def __matches(options, string):  # not super efficient but was easy to write
        def __impl(_segments, _option, _built, _valid):
            if len(_segments) == 1:  # base case, last segment
                if _option.string == _segments[0]:
                    for _child in _option.children:  # show only children if segment matches exactly
                        _valid.append(' '.join(_built + [_option.string, _child.string]))
                elif _option.string.startswith(_segments[0]):
                    _valid.append(' '.join(_built + [_option.string]))
                return

            if _option.string != _segments[0]:  # option body does not match non-last segment
                return

            if len(_option.children) == 0:
                return

            _built.append(_option.string)
            for _child in _option.children:
                __impl(_segments[1:], _child, _built, _valid)
            _built.pop()

        segments = string.split(' ')
        valid = []
        for option in options:
            __impl(segments, option, [], valid)
        return valid

    @staticmethod
    def __strict_match(options, string):
        def __impl(_segments, _option):
            if _option.string != _segments[0]:
                return False

            if len(_option.children) == 0 and len(_segments) == 1:
                return True

            if len(_option.children) == 0 or len(_segments) == 1:
                return False

            return any(map(lambda x: __impl(_segments[1:], x), _option.children))

        segments = string.split(' ')
        for option in options:
            if __impl(segments, option):
                return True
        return False

    @staticmethod
    def choose_fill(options, strict=False, head=None, prompt="> ", max_options=5):
        if head is not None:
            print(head)

        while True:
            choice = FancyBase.__choose_fill_impl(options, prompt, max_options)

            if not strict or FancyBase.__strict_match(options, choice):
                return choice

            print("input was not recognised")

    @staticmethod
    def __choose_fill_impl(options, prompt, max_options):
        cursor_x = len(prompt)

        if os.name == 'nt':  # fix ansi if we are running on Windows
            # TODO: detect if windows version does not support ansi flag and fall back to base choose
            from ctypes import windll
            k = windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)

        FancyBase.__print_init(prompt, max_options)
        matching_options = list(map(lambda x: x.string, options))
        FancyBase.__print("", matching_options, max_options, 0, cursor_x)

        stringbuilder = ""
        selected_line = 0
        max_line = min(max_options, len(matching_options))

        while True:
            print('', end='', flush=True)
            char = readchar.readkey()

            if char == readchar.key.ENTER or char == readchar.key.ENTER_2:
                if selected_line == 0:
                    FancyBase.__print__cleanup(stringbuilder, max_options, cursor_x)
                    return stringbuilder
                else:
                    FancyBase.__print__cleanup(matching_options[selected_line-1], max_options, cursor_x)
                    return matching_options[selected_line-1]

            if char == readchar.key.BACKSPACE and len(stringbuilder) > 0:
                stringbuilder = stringbuilder[:-1]
            elif char.isprintable():
                stringbuilder += char
            elif char == readchar.key.UP and selected_line > 0:
                selected_line -= 1
            elif char == readchar.key.DOWN and selected_line < max_line:
                selected_line += 1
            elif char == readchar.key.TAB and max_line > 0:
                stringbuilder = matching_options[max(0, selected_line-1)]
                selected_line = 0
            elif char == readchar.key.CTRL_W:
                space_index = stringbuilder.rfind(' ')
                selected_line = 0
                if space_index == -1:
                    stringbuilder = ""
                else:
                    stringbuilder = stringbuilder[:space_index]

            matching_options = FancyBase.__matches(options, stringbuilder)

            max_line = min(max_options, len(matching_options))
            if selected_line > max_line:
                selected_line = max_line

            FancyBase.__print(stringbuilder, matching_options, max_options, selected_line, cursor_x)
