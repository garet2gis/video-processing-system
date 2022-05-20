from fastapi import FastAPI, HTTPException, File
import numpy as np
from pydantic import BaseModel
from datetime import datetime
import logging
import redis
import json
import uuid
import base64
import time
from app.settings import settings

logging.basicConfig(level=logging.INFO)

app = FastAPI()

db = redis.StrictRedis(host=settings.redis_host, port=settings.redis_port)


@app.get("/")
def read_root():
    return {"Hello": "World"}


class Prediction(BaseModel):
    success: bool
    prediction: float


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
        answer_bound_time = datetime.now()

        put_in_redis_bound_time = datetime.now()

        k = str(uuid.uuid4())
        image = base64.b64encode(processed_frames).decode("utf-8")
        d = {"id": k, "frames": image}
        db.rpush(settings.redis_queue_name, json.dumps(d))

        logging.info(f"put frames bound time: {datetime.now() - put_in_redis_bound_time}")

        num_tries = 0
        while num_tries < settings.client_max_tries:
            num_tries += 1

            output = db.get(k)

            if output is not None:
                output = output.decode("utf-8")
                data["prediction"] = float(json.loads(output)["prediction"])
                data["success"] = True

                db.delete(k)

                logging.info(f"answer bound time: {datetime.now() - answer_bound_time}")

                break

            time.sleep(settings.timeout_server)
        else:
            raise HTTPException(status_code=400, detail="Request failed after {} tries".format(settings.timeout_server))

    finally:
        return data
