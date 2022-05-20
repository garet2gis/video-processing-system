import cv2
import numpy as np


def violence_preprocess_cnn3d(frame: np.ndarray) -> np.ndarray:
    new_frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
    new_frame = cv2.cvtColor(new_frame, cv2.COLOR_BGR2RGB)
    new_frame = np.reshape(new_frame, (224, 224, 3))
    return new_frame


def violence_preprocess_cnn_lstm(frame: np.ndarray) -> np.ndarray:
    new_frame = cv2.resize(frame, (160, 160), interpolation=cv2.INTER_AREA)
    if np.max(new_frame) > 1:
        new_frame = new_frame / 255.0
    # new_frame = cv2.cvtColor(new_frame, cv2.COLOR_BGR2RGB)
    return new_frame


def violence_preprocess_2dcnn(frame: np.ndarray) -> np.ndarray:
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame, (128, 128))

    return frame
