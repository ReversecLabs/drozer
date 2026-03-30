import os


def _shell_escape(path):
    """
    Escape *path* so it survives ``shlex.split()`` as a single token.

    * Spaces are backslash-escaped (``\\ ``) on every platform.
    * On Windows the path separator ``\\`` is doubled so that
      ``shlex.split()`` (POSIX mode) does not swallow it
      (e.g. ``C:\\Users`` stays intact instead of becoming ``C:Users``).
    """
    if os.name == "nt":
        # Double every backslash first, *then* escape spaces.
        path = path.replace("\\", "\\\\")
    return path.replace(" ", "\\ ")


def complete(path, include_files=True):
    """
    Provides path completion, against files local to the Console.
    """
    if path == "":
        path = os.path.abspath(".")

    folder, search_path = get_folder_and_search_path(path, os.path.sep)
    folders = os.listdir(folder)

    return [_shell_escape(s) for s in get_suggestions(folder, search_path, folders, os.path.sep, include_files)]


def get_folder_and_search_path(path, sep):
    """
    Breakdown the search path, to determine the base folder and search string.
    """

    folder = path[:path.rfind(sep) + 1] if (path != sep) else sep
    search_path = path[path.rfind(sep) + 1:]

    return folder, search_path


def get_suggestions(folder, search_path, folders, sep, include_files=True):
    """
    Filter a list of folders with a given search path.
    """

    suggestions = [(folder + p + sep) for p in folders if
                   (p.startswith(search_path) and p != search_path and os.path.isdir(folder + p))]

    if include_files:
        suggestions += [(folder + p) for p in folders if
                        (p.startswith(search_path) and p != search_path and not os.path.isdir(folder + p))]

    return suggestions
