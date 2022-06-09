import cv2
import numpy as np
from pydantic import BaseModel


# url - link to service to which http requests will be sent
# buffer_size - number of frames in the buffer
# preprocess_func_name - name of the function that processes a single frame
# timeout - delay time between sending requests per second
class NeuroserviceConfig(BaseModel):
    url: str
    buffer_size: int
    preprocess_func_name: str
    timeout: int


# list of elements with the following structure
# first argument - {unique_id_of_source : rtsp url, ...}
# second argument - {unique_id_of_source : NeuroserviceConfig}
sources_config = [({1: "rtsp://cactus.tv:1554/cam223"},
                   {1: NeuroserviceConfig(url=f"http://localhost:8005/predict_cnn_lstm", buffer_size=30,
                                          preprocess_func_name="violence_preprocess_cnn_lstm", timeout=1)}),
                  ({2: "rtsp://cactus.tv:1554/cam71"},
                   {2: NeuroserviceConfig(url=f"http://localhost:8005/predict_frame_cnn3d", buffer_size=64,
                                          preprocess_func_name="violence_preprocess_cnn3d", timeout=3)})]


# preprocess frame functions
def violence_preprocess_cnn3d(frame: np.ndarray) -> np.ndarray:
    new_frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
    new_frame = cv2.cvtColor(new_frame, cv2.COLOR_BGR2RGB)
    new_frame = np.reshape(new_frame, (224, 224, 3))
    return new_frame


def violence_preprocess_cnn_lstm(frame: np.ndarray) -> np.ndarray:
    new_frame = cv2.resize(frame, (160, 160), interpolation=cv2.INTER_AREA)
    if np.max(new_frame) > 1:
        new_frame = new_frame / 255.0
    return new_frame


def violence_preprocess_cnn2d(frame: np.ndarray) -> np.ndarray:
    new_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    new_frame = cv2.resize(new_frame, (128, 128))
    return new_frame
