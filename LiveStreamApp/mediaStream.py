from aiortc.contrib.media import MediaPlayer, MediaBlackhole
from aiortc import MediaStreamTrack
import cv2
from av import VideoFrame

class StoreStreams:
    _streams = dict()
    def get_field(self, dic_key):
        self._streams[dic_key] = dict()
        # self.blackhole = MediaBlackhole()
    def add_track(self, dic_key, kind, track):
        # Track = await Stream(track, kind)
        if kind=="audio":
            self._streams[dic_key]["audio"] = track
        elif kind == "video":
            self._streams[dic_key]["video"] = track 
        # print("add_track", self._streams[dic_key])

    def get_track(self, dic_key, kind, pix=""):
        # print("get_track", self._streams[dic_key])
        if kind == "video":
            return VideoReqTrack(self._streams[dic_key][kind], pix) 
        else:
            return self._streams[dic_key][kind]

Streams =   StoreStreams()


class AudioReqTrack(MediaStreamTrack):
    kind="audio"

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        return await self.track.recv()

        
class VideoReqTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """
    kind = "video"

    def __init__(self, track, p="360p"):
        super().__init__()  # don't forget this!
        self.track = track
        self.p = p #720p 360p etc

    async def recv(self):
        frame = await self.track.recv()
        # return frame
        if frame:
            if self.p == "720p":
                # return frame
                img = frame.to_ndarray(format="bgr24")
                img = cv2.resize(img,(1280,720),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
                new_frame = VideoFrame.from_ndarray(img, format="bgr24")
                new_frame.pts = frame.pts
                new_frame.time_base = frame.time_base
                return new_frame
            elif self.p == "480p":
                pass
            elif self.p == "360p":
                img = frame.to_ndarray(format="bgr24")
                img = cv2.resize(img,(640,360),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
                new_frame = VideoFrame.from_ndarray(img, format="bgr24")
                new_frame.pts = frame.pts
                new_frame.time_base = frame.time_base
                return new_frame
            else:
                pass
            
        else:
            return frame
