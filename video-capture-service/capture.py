from vidgear.gears import CamGear, StreamGear
import cv2
import os
from vidgear.gears.helper import reducer
import logging


class MultipleStreamGear:
    def __init__(self, cam_id, source, logging=False):
        self.cam_id = cam_id
        self.capture_source = source
        self.logging = logging

        self.camera_gear = CamGear(source=self.capture_source, logging=self.logging).start()

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


if __name__ == "__main__":
    cameras = {
        1: "rtsp://rtsp.stream/pattern",
        2: "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
    }

    for i in cameras.keys():
        if not os.path.exists(f'streams/hls{i}'):
            try:
                os.mkdir(f'streams/hls{i}')
                logging.error(f'Made new directory to save stream: streams/hls{i}')
            except:
                logging.error('Unable to create directory')

    gears = {}

    for key, value in cameras.items():
        gears[key] = MultipleStreamGear(key, value, True)

    try:
        while True:
            is_error = False
            for i in gears.keys():
                ret = gears[i].stream_frame()
                if not ret:
                    is_error = True
            if is_error:
                break

    except KeyboardInterrupt:
        print("Detected Keyboard Interrupt. Quitting...")
        pass

    finally:
        for i in gears.keys():
            gears[i].stop()
