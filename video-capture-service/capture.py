from vidgear.gears import CamGear, StreamGear
import cv2
import os
from vidgear.gears.helper import reducer
import logging
import datetime
import time


class ReconnectingCamGear:
    def __init__(self, cam_address, reset_attempts=50, reset_delay=5, is_logging=False):
        self.cam_address = cam_address
        self.reset_attempts = reset_attempts
        self.logging = is_logging
        self.reset_delay = reset_delay
        self.source = CamGear(source=self.cam_address, logging=self.logging).start()
        self.running = True

    def read(self):
        if self.source is None:
            return None
        if self.running and self.reset_attempts > 0:
            frame = self.source.read()
            if frame is None:
                self.source.stop()
                self.reset_attempts -= 1
                logging.info(
                    "Re-connection Attempt-{} occured at time:{}".format(
                        str(self.reset_attempts),
                        datetime.datetime.now().strftime("%m-%d-%Y %I:%M:%S%p"),
                    )
                )
                time.sleep(self.reset_delay)
                self.source = CamGear(source=self.cam_address, logging=self.logging).start()
                # return previous frame
                return self.frame
            else:
                self.frame = frame
                return frame
        else:
            return None

    def stop(self):
        self.running = False
        self.reset_attempts = 0
        self.frame = None
        if self.source is not None:
            self.source.stop()

    @property
    def framerate(self):
        return self.source.framerate


class RTSPStreamGear:
    def __init__(self, cam_id, source, logging=False):
        self.cam_id = cam_id
        self.capture_source = source
        self.logging = logging

        self.camera_gear = ReconnectingCamGear(
            cam_address=self.capture_source,
            reset_attempts=20,
            reset_delay=5,
        )

        stream_params = {"-input_framerate": self.camera_gear.framerate, "-livestream": True}

        self.stream_gear = StreamGear(output=f"streams/hls{self.cam_id}/cam{self.cam_id}.m3u8", format="hls",
                                      logging=self.logging, **stream_params)

    def stream_frame(self):
        frame = self.camera_gear.read()

        if frame is None:
            return False

        frame = reducer(frame, percentage=30)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        self.stream_gear.stream(frame)

        return True

    def stop(self):
        self.camera_gear.stop()
        self.stream_gear.terminate()


class MultipleStreams:
    def __init__(self, camera_sources):
        self.streams = {}
        for key, value in camera_sources.items():
            self.streams[key] = RTSPStreamGear(key, value, True)

    def start(self):
        try:
            while True:
                is_error = False
                for i in self.streams.keys():
                    ret = self.streams[i].stream_frame()
                    if not ret:
                        is_error = True
                if is_error:
                    break

        except KeyboardInterrupt:
            print("Detected Keyboard Interrupt. Quitting...")
            pass

        finally:
            for i in self.streams.keys():
                self.streams[i].stop()


if __name__ == "__main__":
    cameras = {
        1: "rtsp://cactus.tv:1554/cam1",
        2: "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
    }

    for i in cameras.keys():
        if not os.path.exists(f'streams/hls{i}'):
            try:
                os.mkdir(f'streams/hls{i}')
                logging.error(f'Made new directory to save stream: streams/hls{i}')
            except OSError:
                logging.error('Unable to create directory')

    multiple_streams = MultipleStreams(cameras)

    multiple_streams.start()
