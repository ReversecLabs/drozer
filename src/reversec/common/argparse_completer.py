import argparse
import re

from WithSecure.common import path_completion


class ArgumentParserCompleter(object):
    """
    The ArgumentParserCompleter reads the configuration from a argparse.ArgumentParser
    instance, and uses it to provide completion suggestions to readline.
    
    Where possible, APC generates the suggestions itself (such as option flags, local
    files and choices). If this isn't possibleit defers to a suggestion provider, giving
    it the argparse 'action' it is trying to offer a suggestion for, the position of the
    suggestion (if the action accepts more than one) and the text entered so far. 
    """

    def __init__(self, parser, provider):
        self.parser = parser
        self.provider = provider

    def get_suggestions(self, text, line, begidx, endidx, offs=0):
        """
        readline should immediately defer to get_suggestions() when its completer is
        invoked. get_suggestions() accepts the arguments available to readline at
        this point, and converts them into a list() of suggestions.
        """
        real_offset, text, words, word = self.__get_additional_metadata(text, line, begidx, endidx)

        suggestions = []

        pos_actions = self.__get_positional_actions()
        offset = word - offs
        if pos_actions is not None and (offset < len(pos_actions)):
            suggestions.extend(filter(lambda s: s.startswith(text),
                                      self.__get_suggestions_for(self.__get_positional_action(offset), text, line)))
        else:
            offer_flags = True

            # find the last option flag in the line, if there was one
            flag, value_index = self.__get_flag_metadata(words, word)
            # if we found a previous flag, we try to offer suggestions for it
            if flag is not None:
                action = self.__get_action(flag)

                if action is not None:
                    _suggestions, offer_flags = self.__offer_action_suggestions(action, value_index, text, line)

                    suggestions.extend(filter(lambda s: s.startswith(text), _suggestions))

            # if we could be trying to type an option flag, add them to the
            # suggestions
            if offer_flags:
                suggestions.extend(map(lambda os: os[begidx - real_offset:],
                                       filter(lambda s: s.startswith(text), self.__offer_flag_suggestions())))

        return suggestions

    def __get_action(self, flag):
        """
        Retrieve an action from the option parser, given a flag.
        """

        option_tuples = self.parser._get_option_tuples(flag)

        if len(option_tuples) == 1:
            return option_tuples[0][0]
        # TODO: if there are multiple option_tuples we need to do something,
        # probably look for an exact match in option_strings

    def __get_additional_metadata(self, text, line, begidx, endidx):
        """
        Calculate some additional information about the context we are trying to
        complete. We convert the readline arguments into:
        
         - the index where the current symbol really starts (readline ignores '-'es
           for some reason);
         - the extended version of text, including any '-'es;
         - a list of the tokens in line; and
         - the index of our current token in the list of tokens.
        """
        i = begidx
        # for some reason, readline strips any dashes from the start of text
        # before we get it; so we must rewind the line a little to make sure we
        # have collected them
        while i > 0 and line[i - 1] == "-":
            text = "-" + text
            i -= 1

        split_line = [s for s in re.split("((?<!\\\\)\\s)", line)]
        # identify the unique tokens in the command-so-far
        words = [s for s in split_line if s != " "]
        # identify which word we are trying to complete
        word = len([x.start() for x in re.finditer("((?<!\\\\)\\s)", line[:begidx])])

        # TODO: this isn't a very good representation, multiple spaces between
        # adjacent words would f*** it up, as would escaped spaces and such

        return (i, text, words, word)

    def __get_flag_metadata(self, words, word):
        """
        Calculate some additional information about flags. We find the last flag
        token before the current token and calculate our offset from it (in terms
        of tokens).
        """

        flags = self.__get_flags(words, word)

        if len(flags) > 0:
            flag_word = flags[-1]
            flag_index = len(words) - words[-1::-1].index(flag_word) - 1
            value_index = word - flag_index - 1

            return (flag_word, value_index)
        else:
            return (None, None)

    def __get_flags(self, words, word):
        """
        Filter the list of tokens to include only those that are flags.
        """

        return filter(lambda w: w.startswith("-"), words[0:word])

    def __get_positional_action(self, word):
        """
        Fetch the argparse.Action object corresponding to the word-th positional
        argument.
        """
        if len(self.parser._positionals._group_actions) == 0:
            return None

        # if self.parser._positionals._group_actions[0].dest != "command":
        #    word = word-1

        return self.parser._positionals._group_actions[word]

    def __get_positional_actions(self):
        """
        Fetch argparse.Action objects for each of the positional arguments.
        """

        pos = (self.parser._positionals._group_actions)
        filter(lambda p: p.dest != "command" and p.required, pos)
        return pos

    def __get_suggestions_for(self, action, text, line, **kwargs):
        """
        Calculate suggestions for a particular action, given some initial text.
        Where possible, this method provides the suggestions itself, otherwise
        it defers to the suggestion provider.
        """
        if action.choices != None:  # this is pick-from-a-list
            suggestions = action.choices
        elif isinstance(action.type, argparse.FileType):  # this is local path completion
            suggestions = path_completion.complete(text)
        else:  # we don't know, defer to the provider
            suggestions = self.provider.get_completion_suggestions(action, text, line, **kwargs)

        if suggestions != None:
            return suggestions
        else:
            return []

    def __offer_action_suggestions(self, action, value_index, text, line):
        """
        __offer_action_suggestions() works out the suggestions to give for an action,
        and whether or not it is valid to suggest a flag at this point.
        """

        nargs = action.nargs
        # if nargs is None, we assume the default: 1
        if nargs == None:
            nargs = 1

        # depending on the nargs we are expecting, we need to behave slightly
        # differently
        if nargs == "+":
            if value_index == 0:
                # we are completing the first element of an unbounded, but required list
                return (self.__get_suggestions_for(action, text, line, idx=value_index), False)
            else:
                # we are completing the nth element of an unbounded, but required list
                return (self.__get_suggestions_for(action, text, line, idx=value_index), True)
        elif nargs == "*":
            # we are completing the nth element of an unbounded list
            return (self.__get_suggestions_for(action, text, line, idx=value_index), True)
        elif nargs == "?" and value_index == 0:
            # we are completing an optional value
            return (self.__get_suggestions_for(action), True)
        else:
            if value_index < nargs:
                # we are completing the value_index-th element of an fixed list
                return (self.__get_suggestions_for(action, text, line, idx=value_index), False)
            else:
                # we aren't actually completing anything - the last flag has all
                # of the values it expects
                return ([], True)

    def __offer_flag_suggestions(self):
        """
        Collects all option_strings, to calculate a list of all flags.
        """

        flag_suggestions = []

        for optional in self.parser._optionals._group_actions:
            flag_suggestions.extend(optional.option_strings)

        return flag_suggestions
