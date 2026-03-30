import requests

from drozer.configuration import Configuration


class Remote(object):
    """
    Remote is a wrapper around a set of drozer remote repositories, and provides
    methods for managing them.

    A Remote can be instantiated to provide API access to the repository, to
    get information about available modules and download their source.
    """

    def __init__(self, url):
        self.url = url if url.endswith("/") else url + "/"

    @classmethod
    def all(cls):
        """
        Returns all known drozer remotes.

        If the [remotes] section does not exist in the configuration file, we
        create it and add a default repository.
        """

        if not Configuration.has_section('remotes'):
            cls.create("https://raw.githubusercontent.com/ReversecLabs/drozer-modules/repository/")

        return Configuration.get_all_values('remotes')

    @classmethod
    def create(cls, url):
        """
        Create a new drozer remote, with the specified URL.

        If the URL already exists, no remote will be created.
        """

        if cls.get(url) is None:
            Configuration.set('remotes', url, url)

            return True
        else:
            return False

    @classmethod
    def delete(cls, url):
        """
        Removes a drozer remote, with the specified URL.
        """

        if cls.get(url) is not None:
            Configuration.delete('remotes', url)

            return True
        else:
            raise UnknownRemote(url)

    @classmethod
    def get(cls, url):
        """
        Get an instance of Remote, initialised with the remote settings.
        """

        url = Configuration.get('remotes', url)

        if url is not None:
            return cls(url)
        else:
            return None

    def buildPath(self, path):
        """
        Build a full URL for a given path on this remote.
        """

        return self.url + str(path)

    def download(self, module):
        """
        Download a module from the remote, if it exists.
        """

        try:
            return self.getPath(module)
        except Exception as e:
            raise NetworkException(str(e))

    def getPath(self, path):
        """
        Fetch a file from the remote.
        """

        uri = self.buildPath(path)
        response = requests.get(uri)
        response.raise_for_status()
        return response.content


class NetworkException(Exception):
    """
    Raised if a Remote is not available, because of some network error.
    """

    def __init__(self, message="There was a problem accessing the remote."):
        super().__init__(message)

    def __str__(self):
        return super().__str__()


class UnknownRemote(Exception):
    """
    Raised if a Remote is specified that isn't in the configuration.
    """

    def __init__(self, url):
        super().__init__()

        self.url = url

    def __str__(self):
        return "The remote {} is not registered.".format(self.url)
