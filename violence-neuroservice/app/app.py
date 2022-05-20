from keras.models import load_model
from fastapi import FastAPI, HTTPException, File
import numpy as np
from pydantic import BaseModel
from app.neural_networks.video_transform import video_tranform
from datetime import datetime
import logging
from settings import settings

logging.basicConfig(level=logging.INFO)

app = FastAPI()

if settings.model_type == 'cnn3d':
    model = load_model("app/neural_networks/violence_detection_3dcnn/weights.h5", compile=False)
elif settings.model_type == 'cnn_lstm':
    model = load_model("app/neural_networks/violence_detection_cnn_lstm/weights.h5", compile=False)
else:
    model = load_model("app/neural_networks/mobile_net_pretrained/weights.h5", compile=False)


@app.get("/")
def read_root():
    return {"Hello": "World"}


class Prediction(BaseModel):
    success: bool
    prediction: float


@app.post("/predict_cnn3d", response_model=Prediction)
def predict(file: bytes = File(...)):
    data = {"success": False, "prediction": -1}
    try:
        process_bound_time = datetime.now()
        array_image = np.frombuffer(file, dtype=np.uint8)
        frames_64 = np.reshape(array_image, (64, 224, 224, 3))
        processed_frames = video_tranform.process_frames(frames_64)
        logging.info(f"process frames bound time: {datetime.now() - process_bound_time}")

    except Exception:
        raise HTTPException(status_code=400, detail="Bad request: wrong frames, can't parse")

    try:
        predict_bound_time = datetime.now()
        is_violence = model.predict(processed_frames)[0][0]
        data['prediction'] = is_violence
        data['success'] = True
        logging.info(f"predict frames bound time: {datetime.now() - predict_bound_time}")
        logging.info(f"is violence prob: {is_violence}")

    finally:
        return data


@app.post("/predict_cnn_lstm", response_model=Prediction)
def predict(file: bytes = File(...)):
    data = {"success": False, "prediction": -1}
    try:
        process_bound_time = datetime.now()
        array_image = np.frombuffer(file, dtype=np.float64)
        processed_frames = np.reshape(array_image, (30, 160, 160, 3))
        processed_frames = np.expand_dims(processed_frames, axis=0)
        logging.info(f"process frames bound time: {datetime.now() - process_bound_time}")
    except Exception:
        raise HTTPException(status_code=400, detail="Bad request: wrong frames, can't parse")

    try:
        predict_bound_time = datetime.now()
        print('start_pred')
        is_violence = model.predict(processed_frames)[0][1]

        data['prediction'] = is_violence
        data['success'] = True
        logging.info(f"predict frames bound time: {datetime.now() - predict_bound_time}")
        logging.info(f"is violence prob: {is_violence}")

    finally:
        return data


@app.post("/predict_cnn2d", response_model=Prediction)
def predict(file: bytes = File(...)):
    data = {"success": False, "prediction": -1}
    try:
        process_bound_time = datetime.now()

        array_image = np.frombuffer(file, dtype=np.uint8)
        frame = np.array(np.reshape(array_image, (128, 128, 3)))
        frame = frame.reshape(128, 128, 3) / 255
        frame = np.expand_dims(frame, axis=0)

        logging.info(f"process frames bound time: {datetime.now() - process_bound_time}")

    except Exception:
        raise HTTPException(status_code=400, detail="Bad request: wrong frames, can't parse")

    try:
        predict_bound_time = datetime.now()

        is_violence = model.predict(frame)[0][0]
        data['prediction'] = is_violence
        data['success'] = True
        logging.info(f"is violence prob: {is_violence}")

        logging.info(f"predict frames bound time: {datetime.now() - predict_bound_time}")
    finally:
        return data
