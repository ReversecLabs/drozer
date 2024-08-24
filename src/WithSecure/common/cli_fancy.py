import os
from WithSecure.common import cli
import readchar
from ansi import *


class OT:
    def __init__(self, string, children=None):
        if children is None:
            children = []
        self.string = string
        self.children = list(children)


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

    # Levenshtein string distance calculator
    # modified to assign 0 cost to appending or prepending to string a
    # seems to underestimate cost oops
    # TODO: On second thoughts this might not be the best approach, lev may work with longer a strings but may need to use a diffrent algo for short strings

    @staticmethod
    def lev(a, b):
        len_a, len_b = len(a), len(b)
        if len_a == 0:
            return len_b
        if len_b == 0:
            return len_a

        a = a.lower()
        b = b.lower()

        dist_m = [[0] * (len_b + 1) for _ in range(len_a + 1)]

        for itr_a in range(1, len_a + 1):
            dist_m[itr_a][0] = itr_a
        for itr_b in range(1, len_b + 1):
            dist_m[0][itr_b] = 0 if itr_b <= len_b else itr_b  # No cost for insertions at the start of s1

        for itr_a in range(1, len_a + 1):
            for itr_b in range(1, len_b + 1):
                if a[itr_a - 1] == b[itr_b - 1]:
                    dist_m[itr_a][itr_b] = dist_m[itr_a - 1][itr_b - 1]
                else:
                    ins_cost = (0 if itr_a == len_a or itr_a == 1 else 1)  # Free if at start or end of s1
                    dist_m[itr_a][itr_b] = min(
                        dist_m[itr_a - 1][itr_b] + 1,         # Deletion
                        dist_m[itr_a][itr_b - 1] + ins_cost,  # Insertion,
                        dist_m[itr_a - 1][itr_b - 1] + 1      # Substitution
                    )

        if len_a <= len_b:
            return min(dist_m[len_a][len_a:len_b + 1])
        else:
            return dist_m[len_a][len_b]

    """
    finds all options in the options tree that begins with the given string
    """

    @staticmethod
    def __matches(options, string):  # not super efficient but was easy to write
        def __impl(_segments, _option, _built, _valid):
            if len(_segments) == 1:  # base case, last segment
                if _segments[0] == _option.string:
                    for _child in _option.children:  # show only children if segment matches exactly
                        _valid.append((' '.join(_built + [_option.string, _child.string]), 0))
                elif _segments[0] == "":
                    valid.append((' '.join(_built + [_option.string]), 0))
                else:
                    _valid.append((' '.join(_built + [_option.string]),
                                   FancyBase.lev(_segments[0], _option.string)))
                return

            if _option.string != _segments[0]:  # option body does must match non-last segment
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
        valid.sort(key=lambda x: x[1])
        return list(map(lambda x: x[0],
                        filter(lambda x: x[1] < 4,  # max lev distance before the option is not suggested
                               valid)))

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
        if os.name == 'nt':  # fix ansi if we are running on Windows
            # TODO: detect if windows version does not support ansi flag and fall back to base choose
            from ctypes import windll
            k = windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)

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

        FancyBase.__print_init(prompt, max_options)
        matching_options = list(map(lambda x: x.string, options))
        FancyBase.__print("", matching_options, max_options, 0, cursor_x)

        stringbuilder = ""
        selected_line = 0
        max_line = min(max_options, len(matching_options))
        virtual_space = False

        while True:
            print('', end='', flush=True)
            char = readchar.readkey()

            if char == readchar.key.ENTER:
                if selected_line == 0:
                    FancyBase.__print__cleanup(stringbuilder, max_options, cursor_x)
                    return stringbuilder
                else:
                    FancyBase.__print__cleanup(matching_options[selected_line - 1], max_options, cursor_x)
                    return matching_options[selected_line - 1]

            if char == readchar.key.BACKSPACE and len(stringbuilder) > 0:
                virtual_space = False
                stringbuilder = stringbuilder[:-1]
            elif char.isprintable():
                if virtual_space:
                    virtual_space = False
                    if char != " ":
                        stringbuilder += " "
                stringbuilder += char
            elif char == readchar.key.UP and selected_line > 0:
                selected_line -= 1
            elif char == readchar.key.DOWN and selected_line < max_line:
                selected_line += 1
            elif char == readchar.key.TAB and max_line > 0:
                virtual_space = True
                stringbuilder = matching_options[max(0, selected_line - 1)]
                selected_line = 0
            elif char == readchar.key.CTRL_W:
                space_index = stringbuilder.rfind(' ')
                selected_line = 0
                if space_index == -1:
                    virtual_space = False
                    stringbuilder = ""
                else:
                    stringbuilder = stringbuilder[:space_index]

            matching_options = FancyBase.__matches(options, stringbuilder if not virtual_space else stringbuilder + " ")

            max_line = min(max_options, len(matching_options))
            if selected_line > max_line:
                selected_line = max_line

            FancyBase.__print(stringbuilder, matching_options, max_options, selected_line, cursor_x)
