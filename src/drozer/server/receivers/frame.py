from pysolar.api import Frame

from reversec.common.twisted import StreamReceiver

class FrameReceiver(StreamReceiver):
    """
    The FrameReceiver reads streams created by a StreamReceiver, and reads any
    complete Frames from the stream.

    Once a frame is ready, it is passed to the frameReceived() method.
    """
    
    def __init__(self, *args, **kwargs):
        pass

    def connectionMade(self):
        """
        Called when a connection is made to the FrameReceiver, and passes the
        context back to the StreamReceiver.
        """
        StreamReceiver.connectionMade(self)

    def buildFrame(self):
        """
        Attempts to get a frame from the data in the stream.
        """

        frame = Frame.readFrom(self.stream)
        
        return frame

    def streamReceived(self):
        """
        Called whenever the StreamReceiver is updated. Attempts to read a Frame
        from the stream, and passes it to frameReceived if there is.
        """

        frame = self.buildFrame()

        if frame is not None:
            self.frameReceived(frame)
            