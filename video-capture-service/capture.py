from vidgear.gears import StreamGear, NetGear, VideoGear
import cv2
import os
from vidgear.gears.helper import reducer
import logging
import datetime
import time
import numpy as np
from ReconnectingRTSPGear.ReconnectingRTSPGear import ReconnectingRTSPGear



class RTSPStreamGear:
    def __init__(self, cam_id, source, server=None, is_logging=False, enable_stream=True):
        self.cam_id = cam_id
        self.server = server
        self.capture_source = source
        self.logging = is_logging

        self.count = 0

        self.camera_gear = ReconnectingRTSPGear(
            cam_address=self.capture_source,
            reset_attempts=20,
            reset_delay=5,
        )

        self.stream_gear = None
        if enable_stream:
            stream_params = {"-vf": "scale=1280:-2", "-profile:v": "high444", "-livestream": True, "-streams": [
                {"-resolution": "640x360"}]}

            self.stream_gear = StreamGear(output=f"streams/hls{self.cam_id}/cam{self.cam_id}.m3u8", format="hls",
                                          logging=self.logging, **stream_params)

    def stream_frame(self):
        frame = self.camera_gear.read()

        if frame is None:
            return None


        if self.stream_gear is not None:
            reduce_frame = reducer(frame, percentage=70)
            self.stream_gear.stream(reduce_frame)

        if self.server is not None and self.count < 64:
            # resize for server nn
            frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.reshape(frame, (224, 224, 3))
            self.server.send(frame, message=str(self.cam_id))

        self.count += 1

        if self.count == 128:
            self.count = 0

        return frame

    def stop(self):
        self.camera_gear.stop()
        self.stream_gear.terminate()


class MultipleStreams:
    def __init__(self, camera_sources, enable_stream=True, enable_netgear=True):
        self.server = None
        if enable_netgear:
            options = {"bidirectional_mode": True}
            self.server = NetGear(logging=True, **options)
        self.streams = {}
        for key, value in camera_sources.items():
            self.streams[key] = RTSPStreamGear(key, value, self.server, is_logging=True, enable_stream=enable_stream)

    def start(self):
        try:
            while True:
                is_error = False
                for i in self.streams.keys():
                    ret = self.streams[i].stream_frame()

                    if ret is None:
                        is_error = True
                        break

                if is_error:
                    break

        except KeyboardInterrupt:
            logging.error("Detected Keyboard Interrupt. Quitting...")
            pass

        finally:
            for i in self.streams.keys():
                self.streams[i].stop()


if __name__ == "__main__":
    cameras = {
        # 1: "rtsp://cactus.tv:1554/cam3",
        4: "rtsp://cactus.tv:1554/cam15",
        # 2: "./videos/not_violence.mp4",
        1: "./videos/violence2.mp4"
    }

    for i in cameras.keys():
        if os.path.exists(f'streams/hls{i}'):
            try:
                os.rmdir(f'streams/hls{i}')
                os.mkdir(f'streams/hls{i}')
                logging.info(f'Made new directory to save stream: streams/hls{i}')
            except OSError:
                logging.error('Unable to recreate directory')
        else:
            try:
                os.mkdir(f'streams/hls{i}')
                logging.info(f'Made new directory to save stream: streams/hls{i}')
            except OSError:
                logging.error('Unable to create directory')

    multiple_streams = MultipleStreams(cameras, enable_stream=True)

    multiple_streams.start()
