import cv2
import numpy as np


def violence_preprocess(frame: np.ndarray) -> np.ndarray:
    new_frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
    new_frame = cv2.cvtColor(new_frame, cv2.COLOR_BGR2RGB)
    new_frame = np.reshape(new_frame, (224, 224, 3))
    return new_frame
