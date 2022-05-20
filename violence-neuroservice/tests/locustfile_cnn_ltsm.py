from locust import HttpUser, task
import cv2
import numpy as np
from collections import deque
from utils import frames_to_file


def get_video_chunk_cnn_lstm():
    camera = cv2.VideoCapture("tests/violence_test.mp4")
    camera_buffer = deque(maxlen=30)

    counter = 0
    while camera.isOpened() and counter < 30:
        ret, frame = camera.read()
        if ret:
            frame = cv2.resize(frame, (160, 160), interpolation=cv2.INTER_AREA)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if np.max(frame) > 1:
                frame = frame / 255.0
            camera_buffer.append(frame)
        else:
            break
        counter += 1

    camera.release()
    return np.array(camera_buffer)


frames = get_video_chunk_cnn_lstm()


class TestUser(HttpUser):
    @task
    def predict(self):
        self.client.post("/predict_cnn_lstm", files=frames_to_file(frames))
