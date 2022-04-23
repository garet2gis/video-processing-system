import cv2
import numpy as np


def preprocess_frame_violence(frame: np.ndarray) -> np.ndarray:

    newFrame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
    newFrame = cv2.cvtColor(newFrame, cv2.COLOR_BGR2RGB)
    newFrame = np.reshape(newFrame, (224, 224, 3))
    return newFrame
