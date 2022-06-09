from locust import HttpUser, task, between
import cv2
import numpy as np
from utils import frames_to_file
from collections import deque


def get_video_chunk_cnn3d():
    camera = cv2.VideoCapture("tests/violence_test.mp4")
    camera_buffer = deque(maxlen=64)

    counter = 0
    while camera.isOpened() and counter < 64:
        ret, frame = camera.read()
        if ret:
            frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            camera_buffer.append(frame)
        else:
            break
        counter += 1

    camera.release()

    return np.array(camera_buffer)


frames = get_video_chunk_cnn3d()


class TestUser(HttpUser):
    @task
    def predict(self):
        self.client.post("/predict_cnn3d", files=frames_to_file(frames))

    # wait_time = between(1, 2)
