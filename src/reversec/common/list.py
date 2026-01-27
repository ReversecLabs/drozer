import collections.abc as collections


def chunk(l, n):
    """
    Utility method to split a list (l) in chunks of n sections.
    """

    for i in range(0, len(l), n):
        yield l[i:i + n]


def flatten(l):
    """
    Utility method to flatten a nested list (l) into a single list.
    """

    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, str):
            for sub in flatten(el):
                yield sub
        else:
            yield el
