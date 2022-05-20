from locust import HttpUser, task
import cv2
import os
from utils import frames_to_file


def get_video_chunk_cnn2d():
    print(os.path.exists("tests/violence_test.mp4"))
    camera = cv2.VideoCapture("tests/violence_test.mp4")
    if camera.isOpened():
        ret, frame = camera.read()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (128, 128))
            camera.release()

            return frame

    camera.release()

    return []


frames = get_video_chunk_cnn2d()


class TestUser(HttpUser):
    @task
    def predict(self):
        self.client.post("/predict_cnn2d", files=frames_to_file(frames))
