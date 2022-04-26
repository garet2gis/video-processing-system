from vidgear.gears import VideoGear
import logging
from datetime import datetime
import time

class ReconnectingRTSPGear:
    def __init__(self, cam_address, reset_attempts=50, reset_delay=5, is_logging=False):
        self.cam_address = cam_address
        self.reset_attempts = reset_attempts
        self.logging = is_logging
        self.reset_delay = reset_delay
        self.source = VideoGear(source=self.cam_address, logging=self.logging).start()
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
                        datetime.now().strftime("%m-%d-%Y %I:%M:%S%p"),
                    )
                )
                time.sleep(self.reset_delay)
                self.source = VideoGear(source=self.cam_address, logging=self.logging).start()
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
