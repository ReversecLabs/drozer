import io
from twisted.internet.protocol import Protocol


class StreamReceiver(Protocol):
    """
    A Twisted Protocol that receives data from the runtime, and recombines it
    into a data stream.

    Whenever the stream is updated, the streamReceived() method is called on
    the implementation, which can choose to consume some of the data.
    """

    stream = None

    def __init__(self):
        pass

    def connectionMade(self):
        """
        Called when a connection is received to the StreamReceiver. This
        initialises the buffer we will use.
        """

        self.stream = io.BytesIO()

    def dataReceived(self, data):
        """
        Called whenever more data is received from the client. The data is
        added to the stream, and streamReceived() called on the implementation.

        If the implementation has consumed the entire stream, we truncate
        it to preserve memory.
        """

        self.__enqueue(data)

        self.streamReceived()

        if self.stream.tell() == len(self.stream.getvalue()):
            self.stream.truncate(0)

    def __enqueue(self, data):
        """
        Append some more data to the end of the stream.
        """

        # yaynoteyay
        # for some reason, while the stream was being appended, the read position never changed
        # so moved the position parameter setting more down
        #position = self.stream.tell()

        self.stream.seek(len(self.stream.getvalue()))

        # new position here
        # `self.stream.seek(len(self.stream.getvalue()))` sets the current read position at the end of the stream
        # `self.stream.tell()` gets the current read position
        # so now `position` should be at the current end of the stream
        position = self.stream.tell()

        self.stream.write(data)
        self.stream.seek(position)
